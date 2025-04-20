from celery import Celery, Task
from celery.signals import task_failure, task_success, task_retry
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.ai_utils import summarize_text
from app.cache import get_cached_summary, set_cached_summary

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Set up Celery with broker and result backend
celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,  # Prevent worker from prefetching too many tasks
    task_acks_late=True,  # Acknowledge tasks after they are executed
)

class LoggedTask(Task):
    """Base task that logs its progress."""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
        return super().on_success(retval, task_id, args, kwargs)
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {task_id} retrying: {exc}")
        return super().on_retry(exc, task_id, args, kwargs, einfo)

@celery_app.task(bind=True, base=LoggedTask, max_retries=3, retry_backoff=True)
def generate_summary_task(self, text: str, length: str = 'medium', 
                         format: str = 'paragraph', extractiveness: str = 'low') -> str:
    """
    Celery task to generate a summary of the provided text.
    
    Args:
        text: The text to summarize
        length: The length of the summary ('short', 'medium', or 'long')
        format: The format of the summary ('paragraph' or 'bullets')
        extractiveness: The extractiveness of the summary ('low' or 'high')
        
    Returns:
        The generated summary
    """
    # Check cache first
    cached = get_cached_summary(text)
    if cached:
        logger.info(f"Cache hit for task {self.request.id}")
        return cached.decode("utf-8")

    try:
        # Generate summary
        logger.info(f"Generating summary for task {self.request.id}")
        summary = summarize_text(text, length, format, extractiveness)
        
        # Cache the result
        set_cached_summary(text, summary)
        
        return summary
    except Exception as e:
        logger.error(f"Error in task {self.request.id}: {e}")
        # Retry with exponential backoff
        self.retry(exc=e, countdown=2 ** self.request.retries)

# Register task handlers
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    logger.error(f"Task {task_id} failed with error: {exception}")

@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    logger.info(f"Task completed successfully with result length: {len(str(result))}")

@task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, **kwargs):
    logger.warning(f"Task {request.id} is being retried due to: {reason}")
