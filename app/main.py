from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import time
import os
from app.api import router
from app.models import HealthResponse, ErrorResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GenAI Summarizer API",
    version="1.0.0",
    description="API backend for text summarization using Cohere, Celery, and Redis",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {process_time:.4f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"- Error: {str(e)} "
            f"- Duration: {process_time:.4f}s"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "details": str(e)},
        )

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the API and its components.
    """
    # Check Redis connection
    redis_status = "up"
    redis_details = "Connected"
    try:
        from app.cache import cache
        cache.ping()
    except Exception as e:
        redis_status = "down"
        redis_details = str(e)
    
    # Check Celery connection
    celery_status = "up"
    celery_details = "Connected"
    try:
        from app.tasks import celery_app
        celery_app.control.ping()
    except Exception as e:
        celery_status = "down"
        celery_details = str(e)
    
    # Check Cohere connection
    cohere_status = "up"
    cohere_details = "Connected"
    try:
        from app.ai_utils import client, api_key
        # Just check if the API key is set
        if not api_key or len(api_key.strip()) == 0:
            raise ValueError("COHERE_API_KEY is not set or empty")
    except Exception as e:
        cohere_status = "down"
        cohere_details = str(e)
    
    return HealthResponse(
        status="ok" if all(s == "up" for s in [redis_status, celery_status, cohere_status]) else "degraded",
        version="1.0.0",
        components={
            "redis": {"status": redis_status, "details": redis_details},
            "celery": {"status": celery_status, "details": celery_details},
            "cohere": {"status": cohere_status, "details": cohere_details},
        },
    )

# Root endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint.
    
    Returns a simple message indicating that the API is running.
    """
    return {"message": "GenAI Summarizer API is running! Go to /docs for API documentation."}

# Include API router
app.include_router(router, prefix="/api")

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="GenAI Summarizer API",
        version="1.0.0",
        description="API backend for text summarization using Cohere, Celery, and Redis",
        routes=app.routes,
    )
    
    # Add security scheme if needed
    # openapi_schema["components"]["securitySchemes"] = {...}
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
