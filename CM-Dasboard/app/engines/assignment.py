import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.user import User, RoleEnum
from app.models.complaint import Complaint, ComplaintStatus

logger = logging.getLogger("cm_dashboard.engines.assignment")

class AssignmentEngine:
    """
    Core engine responsible for deterministic officer assignment.
    Assigns complaints based on district, department, and active workload balancing.
    """

    @staticmethod
    async def assign_officer(department: str, district: str, session: AsyncSession) -> Optional[int]:
        """
        Finds the most suitable officer for a complaint based on matching criteria
        and workload balancing.
        
        Returns the User ID of the assigned officer, or None if no suitable officer is found.
        """
        logger.info(f"[ASSIGNMENT_ENGINE] Attempting assignment for Dept: {department}, District: {district}")

        # Subquery to count active assigned complaints per officer
        active_statuses = [
            ComplaintStatus.SUBMITTED.name,
            ComplaintStatus.PROCESSING.name,
            ComplaintStatus.ESCALATED.name
        ]
        
        # We want to find officers matching the district and department.
        # We order by their current active workload (ascending) to balance the load.
        query = (
            select(
                User.id,
                func.count(Complaint.id).label("active_workload")
            )
            .outerjoin(
                Complaint,
                (Complaint.assigned_to == User.id) & (Complaint.status.in_(active_statuses))
            )
            .where(User.role == RoleEnum.OFFICER)
            .where(User.department == department)
            .where(User.district == district)
            .group_by(User.id)
            .order_by("active_workload")
            .limit(1)
        )

        result = await session.execute(query)
        officer_row = result.first()

        if officer_row:
            officer_id = officer_row.id
            workload = officer_row.active_workload
            logger.info(f"[ASSIGNMENT_ENGINE] Assigned Officer ID {officer_id} (Current Workload: {workload})")
            return officer_id
        
        # Fallback: Ignore district if no officer is found in the specific district
        logger.warning(f"[ASSIGNMENT_ENGINE] No officer found in {district}. Falling back to state-wide pool for {department}.")
        fallback_query = (
            select(
                User.id,
                func.count(Complaint.id).label("active_workload")
            )
            .outerjoin(
                Complaint,
                (Complaint.assigned_to == User.id) & (Complaint.status.in_(active_statuses))
            )
            .where(User.role == RoleEnum.OFFICER)
            .where(User.department == department)
            .group_by(User.id)
            .order_by("active_workload")
            .limit(1)
        )
        
        fallback_result = await session.execute(fallback_query)
        fallback_row = fallback_result.first()
        
        if fallback_row:
            officer_id = fallback_row.id
            workload = fallback_row.active_workload
            logger.info(f"[ASSIGNMENT_ENGINE] Assigned Fallback Officer ID {officer_id} (Current Workload: {workload})")
            return officer_id

        logger.error(f"[ASSIGNMENT_ENGINE] FAILED TO ASSIGN. No officers available for department {department}.")
        return None
