import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.models.complaint import Complaint, ComplaintStatus, PriorityEnum
from app.models.escalation import Escalation
from app.models.user import User, RoleEnum
from app.engines.routing import RoutingEngine

logger = logging.getLogger("cm_dashboard.engines.escalation")

class EscalationEngine:
    """
    Background batch processor that handles automated escalations.
    Sweeps for unresolved complaints that breach SLAs and re-routes them.
    """

    # SLA defined in hours
    SLA_HOURS = {
        PriorityEnum.CRITICAL: 24,
        PriorityEnum.HIGH: 48,
        PriorityEnum.MEDIUM: 168,  # 7 days
        PriorityEnum.LOW: 336      # 14 days
    }

    @staticmethod
    async def process_escalations(session: AsyncSession):
        """
        Scans all active complaints and forces escalation transitions.
        """
        logger.info("[ESCALATION_ENGINE] Starting SLA sweep for escalations...")
        
        now = datetime.utcnow()
        
        # We only check complaints currently actively waiting or processing
        query = select(Complaint).filter(
            Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.PROCESSING])
        )
        res = await session.execute(query)
        complaints = res.scalars().all()
        
        escalated_count = 0
        for c in complaints:
            priority = c.priority or PriorityEnum.MEDIUM
            sla_limit = timedelta(hours=EscalationEngine.SLA_HOURS.get(priority, 168))
            
            # Check if breached
            if now - c.created_at > sla_limit:
                await EscalationEngine._escalate(c, session)
                escalated_count += 1
                
        if escalated_count > 0:
            await session.commit()
            logger.info(f"[ESCALATION_ENGINE] Successfully escalated {escalated_count} complaints.")
        else:
            logger.info("[ESCALATION_ENGINE] No escalations required.")

    @staticmethod
    async def _escalate(complaint: Complaint, session: AsyncSession):
        """
        Escalates a single complaint to the Department Head, 
        or directly to ADMIN if it was already assigned to a Head.
        """
        logger.warning(f"[ESCALATION_ENGINE] SLA Breach detected on Complaint {complaint.ticket_id}. Escalating.")
        
        old_assigned_to = complaint.assigned_to
        target_role = RoleEnum.HEAD
        
        # Determine escalation target
        if old_assigned_to:
            query = select(User).filter(User.id == old_assigned_to)
            res = await session.execute(query)
            officer = res.scalars().first()
            if officer and officer.role == RoleEnum.HEAD:
                target_role = RoleEnum.ADMIN
                
        # Find next assignee
        query_target = select(User).filter(
            User.role == target_role,
            or_(User.department == complaint.department, User.department == "GENERAL_DEPT")
        ).order_by(User.id.asc()).limit(1)
        res_target = await session.execute(query_target)
        new_assignee = res_target.scalars().first()
        
        new_assigned_to = new_assignee.id if new_assignee else None
        
        # Update Complaint Status
        complaint.status = ComplaintStatus.ESCALATED
        complaint.assigned_to = new_assigned_to
        
        # Create Audit Record
        esc_record = Escalation(
            complaint_id=complaint.id,
            escalated_by=None, # System
            escalated_to=new_assigned_to,
            reason=f"Automated Escalation: SLA breached for priority {complaint.priority.name}"
        )
        session.add(esc_record)
        logger.info(f"[ESCALATION_ENGINE] Escalated {complaint.ticket_id} to {target_role.name} ({new_assigned_to})")
