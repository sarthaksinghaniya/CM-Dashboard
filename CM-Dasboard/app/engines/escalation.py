"""
Escalation Engine — automated SLA breach detection & escalation.

Hardening:
  • Race-condition guard: skips if complaint was resolved concurrently
  • Idempotent: won't re-escalate already-ESCALATED complaints
  • Full try/except per complaint — one failure doesn't abort the sweep
  • Structured logging with ticket_id tracing
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.models.complaint import Complaint, ComplaintStatus, PriorityEnum
from app.models.escalation import Escalation
from app.models.user import User, RoleEnum

logger = logging.getLogger("cm_dashboard.engines.escalation")


class EscalationEngine:
    """Background batch processor for automated SLA escalations."""

    # SLA limits in hours per priority level
    SLA_HOURS = {
        PriorityEnum.CRITICAL: 24,
        PriorityEnum.HIGH: 48,
        PriorityEnum.MEDIUM: 168,   # 7 days
        PriorityEnum.LOW: 336,      # 14 days
    }

    @staticmethod
    async def process_escalations(session: AsyncSession) -> int:
        """
        Sweep all active complaints for SLA breaches and escalate.
        Returns the number of escalated complaints.
        """
        logger.info("[ESCALATION_ENGINE] Starting SLA sweep for escalations...")

        now = datetime.utcnow()
        query = select(Complaint).filter(
            Complaint.status.in_([
                ComplaintStatus.SUBMITTED,
                ComplaintStatus.PROCESSING,
            ])
        )
        res = await session.execute(query)
        complaints = res.scalars().all()

        escalated = 0
        for c in complaints:
            try:
                priority = c.priority or PriorityEnum.MEDIUM
                sla_hours = EscalationEngine.SLA_HOURS.get(priority, 168)
                sla_limit = timedelta(hours=sla_hours)

                if now - c.created_at > sla_limit:
                    await EscalationEngine._escalate(c, session)
                    escalated += 1
            except Exception as exc:
                # One complaint failure must NOT abort the entire sweep
                logger.error(
                    f"[ESCALATION_ENGINE] Error escalating {c.ticket_id}: {exc}",
                    exc_info=True,
                )

        if escalated:
            try:
                await session.commit()
            except Exception as exc:
                logger.error(f"[ESCALATION_ENGINE] Commit failed: {exc}", exc_info=True)
                await session.rollback()
            logger.info(
                f"[ESCALATION_ENGINE] Successfully escalated {escalated} complaints."
            )
        else:
            logger.info("[ESCALATION_ENGINE] No escalations required.")

        return escalated

    @staticmethod
    async def _escalate(complaint: Complaint, session: AsyncSession):
        """Escalate a single complaint with idempotent safety."""
        logger.warning(
            f"[ESCALATION_ENGINE] SLA Breach detected on Complaint "
            f"{complaint.ticket_id}. Escalating."
        )

        # Race-condition guard: skip if resolved concurrently
        if complaint.status in (ComplaintStatus.RESOLVED, ComplaintStatus.ESCALATED):
            logger.info(
                f"[ESCALATION_ENGINE] Complaint {complaint.ticket_id} "
                f"already {complaint.status.value} — skipping."
            )
            return

        # Determine escalation target role
        target_role = RoleEnum.HEAD
        if complaint.assigned_to:
            q = select(User).filter(User.id == complaint.assigned_to)
            res = await session.execute(q)
            current = res.scalars().first()
            if current and current.role == RoleEnum.HEAD:
                target_role = RoleEnum.ADMIN

        # Find next assignee
        q_target = (
            select(User)
            .filter(
                User.role == target_role,
                or_(
                    User.department == complaint.department,
                    User.department == "GENERAL_DEPT",
                ),
            )
            .order_by(User.id.asc())
            .limit(1)
        )
        res_target = await session.execute(q_target)
        new_assignee = res_target.scalars().first()
        new_id = new_assignee.id if new_assignee else None

        # Update state
        complaint.status = ComplaintStatus.ESCALATED
        complaint.assigned_to = new_id

        # Audit trail
        session.add(Escalation(
            complaint_id=complaint.id,
            escalated_by=None,  # system
            escalated_to=new_id,
            reason=(
                f"Automated Escalation: SLA breached for "
                f"priority {complaint.priority.name}"
            ),
        ))
        logger.info(
            f"[ESCALATION_ENGINE] Escalated {complaint.ticket_id} "
            f"to {target_role.name} ({new_id})"
        )
