import asyncio
import logging
from app.worker.celery_app import celery_app
from app.services.pipeline.engine import PipelineEngine
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.pipeline.process_pipeline_task", max_retries=3)
def process_pipeline_task(self, ticket_id: str):
    """
    Celery task that delegates execution to the Deterministic Engine Core.
    """
    logger.info(f"Celery Task: Delegating pipeline execution to Engine Core for ticket {ticket_id}")
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        loop.run_until_complete(PipelineEngine.execute_core(ticket_id, AsyncSessionLocal))
    except Exception as exc:
        logger.error(f"Celery Task critical failure for ticket {ticket_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
