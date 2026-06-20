"""
Pipeline task entry-points for both Celery and APScheduler.

Hardening:
  • Celery import is optional — system works without redis/celery installed
  • APScheduler async entry-point is the primary path
  • Full catch-all so tasks never crash the scheduler
"""
import asyncio
import logging

from app.services.pipeline.engine import PipelineEngine
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery task (optional — only works when celery + redis are available)
# ---------------------------------------------------------------------------
try:
    from app.worker.celery_app import celery_app

    @celery_app.task(
        bind=True,
        name="app.tasks.pipeline.process_pipeline_task",
        max_retries=3,
    )
    def process_pipeline_task(self, ticket_id: str):
        """Celery task delegating to the deterministic engine core."""
        logger.info(
            f"Celery Task: Delegating pipeline execution for ticket {ticket_id}"
        )
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                PipelineEngine.execute_core(ticket_id, AsyncSessionLocal)
            )
        except Exception as exc:
            logger.error(
                f"Celery Task critical failure for ticket {ticket_id}: {exc}",
                exc_info=True,
            )
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

except ImportError:
    logger.info("Celery not available — using APScheduler fallback only.")


# ---------------------------------------------------------------------------
# APScheduler async entry-point (primary, always available)
# ---------------------------------------------------------------------------
async def execute_core(ticket_id: str):
    """APScheduler async task — delegates to the deterministic engine core."""
    logger.info(
        f"APScheduler Task: Delegating pipeline execution for ticket {ticket_id}"
    )
    try:
        await PipelineEngine.execute_core(ticket_id, AsyncSessionLocal)
    except Exception as exc:
        logger.error(
            f"APScheduler Task critical failure for ticket {ticket_id}: {exc}",
            exc_info=True,
        )
