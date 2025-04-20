from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from typing import Optional, Dict, Any
import logging
import time
from app.models import SummaryRequest, TaskResponse, ResultResponse, ErrorResponse
from app.tasks import celery_app, generate_summary_task
from app.cache import get_cached_summary

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["summarization"])

# Rate limiting (simple in-memory implementation)
request_counts = {}
RATE_LIMIT = 10  # requests per minute
RATE_WINDOW = 60  # seconds

async def check_rate_limit(request: Request):
    """Simple rate limiting middleware."""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean up old entries
    for ip in list(request_counts.keys()):
        if current_time - request_counts[ip]["timestamp"] > RATE_WINDOW:
            del request_counts[ip]
    
    # Check current IP
    if client_ip in request_counts:
        if request_counts[client_ip]["count"] >= RATE_LIMIT:
            if current_time - request_counts[client_ip]["timestamp"] < RATE_WINDOW:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {RATE_LIMIT} requests per {RATE_WINDOW} seconds."
                )
            else:
                # Reset if window has passed
                request_counts[client_ip] = {"count": 1, "timestamp": current_time}
        else:
            request_counts[client_ip]["count"] += 1
    else:
        request_counts[client_ip] = {"count": 1, "timestamp": current_time}

@router.post("/summarize", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def summarize(request: SummaryRequest, background_tasks: BackgroundTasks, req: Request, _: None = Depends(check_rate_limit)):
    """
    Create a summarization task.
    
    This endpoint accepts text and returns a task ID that can be used to retrieve the result.
    """
    try:
        # Log request
        logger.info(f"Received summarization request with text length: {len(request.text)}")
        
        # Check cache
        cached = get_cached_summary(request.text)
        if cached:
            logger.info("Cache hit, returning cached result")
            return TaskResponse(
                task_id=f"cached:{cached.decode('utf-8')}",
                status="completed"
            )
        
        # Create task
        task = generate_summary_task.delay(
            request.text, 
            request.length, 
            request.format, 
            request.extractiveness
        )
        
        logger.info(f"Created task with ID: {task.id}")
        return TaskResponse(task_id=task.id, status="pending")
    except Exception as e:
        logger.error(f"Error creating summarization task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create summarization task: {str(e)}"
        )

@router.get("/result/{task_id}", response_model=ResultResponse)
async def get_result(task_id: str):
    """
    Get the result of a summarization task.
    
    This endpoint accepts a task ID and returns the result if the task is complete.
    """
    try:
        # Check if this is a cached result
        if task_id.startswith("cached:"):
            logger.info(f"Returning cached result for task: {task_id[:15]}...")
            return ResultResponse(
                result=task_id.replace("cached:", ""),
                meta={"source": "cache"}
            )
        
        # Get task result
        logger.info(f"Checking result for task: {task_id}")
        result: AsyncResult = celery_app.AsyncResult(task_id)
        
        # Check task state
        if result.state == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task is still pending."
            )
        elif result.state == "STARTED":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task is in progress."
            )
        elif result.state == "RETRY":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task is being retried."
            )
        elif result.state == "FAILURE":
            logger.error(f"Task {task_id} failed: {str(result.result)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task failed: {str(result.result)}"
            )
        elif result.state == "SUCCESS":
            logger.info(f"Returning successful result for task: {task_id}")
            return ResultResponse(
                result=result.result,
                meta={"task_id": task_id, "state": result.state}
            )
        else:
            logger.warning(f"Unknown task state for {task_id}: {result.state}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown task state: {result.state}"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving task result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task result: {str(e)}"
        )

@router.delete("/result/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_task(task_id: str):
    """
    Revoke a pending or running task.
    
    This endpoint accepts a task ID and revokes the task if it is still pending or running.
    """
    try:
        # Check if this is a cached result
        if task_id.startswith("cached:"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Cannot revoke cached results"}
            )
        
        # Revoke task
        logger.info(f"Revoking task: {task_id}")
        celery_app.control.revoke(task_id, terminate=True)
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except Exception as e:
        logger.error(f"Error revoking task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke task: {str(e)}"
        )
