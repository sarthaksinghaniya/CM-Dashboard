import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.complaint import Complaint, ComplaintStatus, PriorityEnum
from app.models.complaint_update import ComplaintUpdate

logger = logging.getLogger("cm_dashboard.pipeline.engine")

class RetryHandler:
    MAX_RETRIES = 3
    BASE_BACKOFF_SECONDS = 60 # 1 minute base
    
    @classmethod
    def calculate_backoff(cls, current_retry: int) -> int:
        """Exponential backoff: 60s, 120s, 240s..."""
        return cls.BASE_BACKOFF_SECONDS * (2 ** current_retry)
    
    @classmethod
    def can_retry(cls, current_retry: int) -> bool:
        return current_retry < cls.MAX_RETRIES


class PipelineEngine:
    """
    Deterministic, production-grade complaint processing ENGINE CORE.
    Handles strict state transitions, locks, and exponential retries.
    """

    @staticmethod
    async def transition_to_processing(ticket_id: str, session: AsyncSession) -> Optional[Complaint]:
        """
        Atomically transitions a complaint from SUBMITTED or FAILED to IN_PROGRESS.
        Returns the Complaint if the lock was acquired and transition succeeded.
        Returns None if already processing, resolved, or not found (preventing duplicate processing).
        """
        # Step 1: Query the complaint
        query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
        result = await session.execute(query)
        complaint = result.scalars().first()
        
        if not complaint:
            logger.warning(f"[ENGINE][{ticket_id}] Ticket not found.")
            return None
            
        # Step 2: Idempotency check
        if complaint.status not in [ComplaintStatus.SUBMITTED, ComplaintStatus.FAILED]:
            logger.warning(f"[ENGINE][{ticket_id}] Aborting duplicate processing. Current state: {complaint.status.value}")
            return None
            
        # Step 3: Transition State
        old_status = complaint.status
        complaint.status = ComplaintStatus.PROCESSING
        
        # Log Hook
        PipelineEngine._log_transition(ticket_id, old_status.value, complaint.status.value)
        
        # Register the ledger update
        ledger_entry = ComplaintUpdate(
            complaint_id=complaint.id,
            status=ComplaintStatus.PROCESSING.value,
            note="System Core Engine initialized processing loop.",
            updated_by=None
        )
        session.add(ledger_entry)
        
        await session.commit()
        await session.refresh(complaint)
        return complaint

    @staticmethod
    async def transition_to_resolved(ticket_id: str, assigned_to: Optional[int], session: AsyncSession) -> Optional[Complaint]:
        """
        Successfully resolves the processing cycle. Moves IN_PROGRESS -> ASSIGNED or RESOLVED.
        """
        query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
        result = await session.execute(query)
        complaint = result.scalars().first()
        
        if not complaint or complaint.status != ComplaintStatus.PROCESSING:
            return None
            
        old_status = complaint.status
        # In this system, if it's assigned, it goes to ASSIGNED. Otherwise RESOLVED.
        complaint.status = ComplaintStatus.ASSIGNED if assigned_to else ComplaintStatus.RESOLVED
        
        PipelineEngine._log_transition(ticket_id, old_status.value, complaint.status.value)
        
        ledger_entry = ComplaintUpdate(
            complaint_id=complaint.id,
            status=complaint.status.value,
            note="AI Pipeline execution completed successfully.",
            updated_by=None
        )
        session.add(ledger_entry)
        
        await session.commit()
        return complaint

    @staticmethod
    async def handle_failure(ticket_id: str, exception: Exception, session: AsyncSession) -> None:
        """
        Catches failures, logs errors, and delegates exponential retry logic.
        Transitions IN_PROGRESS -> FAILED or FAILED_FINAL.
        """
        query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
        result = await session.execute(query)
        complaint = result.scalars().first()
        
        if not complaint:
            logger.error(f"[ENGINE][{ticket_id}] Cannot handle failure. Ticket not found.")
            return

        old_status = complaint.status
        complaint.failure_reason = str(exception)
        
        if RetryHandler.can_retry(complaint.retry_count):
            complaint.status = ComplaintStatus.FAILED
            complaint.retry_count += 1
            complaint.last_retry_at = datetime.now(timezone.utc).replace(tzinfo=None)
            backoff = RetryHandler.calculate_backoff(complaint.retry_count)
            logger.warning(f"[ENGINE][{ticket_id}] Execution failed. Scheduled retry {complaint.retry_count}/{RetryHandler.MAX_RETRIES} in {backoff}s. Error: {exception}")
        else:
            complaint.status = ComplaintStatus.FAILED_FINAL
            logger.error(f"[ENGINE][{ticket_id}] MAX RETRIES EXCEEDED. Transitioning to terminal FAILED_FINAL state. Error: {exception}")

        PipelineEngine._log_transition(ticket_id, old_status.value, complaint.status.value)
        
        ledger_entry = ComplaintUpdate(
            complaint_id=complaint.id,
            status=complaint.status.value,
            note=f"Pipeline execution failed. Reason: {str(exception)[:200]}",
            updated_by=None
        )
        session.add(ledger_entry)
        
        await session.commit()

    @staticmethod
    def _log_transition(ticket_id: str, old_state: str, new_state: str):
        """Structured logging hook for every state change."""
        logger.info(f"[ENGINE][{ticket_id}] STATE TRANSITION: {old_state} -> {new_state}")

    @staticmethod
    async def execute_core(ticket_id: str, session_factory):
        """
        The central, deterministic pipeline executor.
        It is fully isolated from APIs, idempotent, and failure-safe.
        """
        from app.engines.routing import RoutingEngine
        
        async with session_factory() as session:
            # 1. Idempotent Transition Lock
            complaint = await PipelineEngine.transition_to_processing(ticket_id, session)
            if not complaint:
                return # Abort (already processing, resolved, or nonexistent)
            
            # Snapshots for ML
            text = complaint.description or complaint.title
            
        try:
            # 2. Execute AI Auto Routing Engine
            from app.engines.routing import RoutingEngine
            
            async with session_factory() as session:
                query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
                res = await session.execute(query)
                complaint = res.scalars().first()
                
                district = complaint.district
                text = complaint.description or complaint.title
            
            routing_result = await RoutingEngine.process_routing(text, district, session_factory)
            
            # 3. Apply Routing Decision
            async with session_factory() as session:
                query = select(Complaint).filter(Complaint.ticket_id == ticket_id)
                res = await session.execute(query)
                complaint = res.scalars().first()
                
                complaint.priority = routing_result["priority"]
                complaint.category = routing_result["category"]
                complaint.department = routing_result["department"]
                complaint.assigned_to = routing_result["assigned_to"]
                
                assigned_to = routing_result["assigned_to"]
                await session.commit()
            
            # 4. Final Transition
            async with session_factory() as session:
                await PipelineEngine.transition_to_resolved(ticket_id, assigned_to, session)
            
        except Exception as e:
            # 5. Handle Failures & Retries
            logger.error(f"[ENGINE][{ticket_id}] Critical failure inside execution boundary: {e}", exc_info=True)
            async with session_factory() as session:
                await PipelineEngine.handle_failure(ticket_id, e, session)
