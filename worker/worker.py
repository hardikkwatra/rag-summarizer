import os
import logging
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the Celery app from the tasks module
from app.tasks import celery_app

# For auto-discovery
celery_app.autodiscover_tasks(['app'])

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.worker_main(["worker", "--loglevel=info", "--concurrency=2"])
