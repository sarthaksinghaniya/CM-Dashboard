"""
Assignment Engine — production-grade with crash-proofing.

Features:
  • DB retry with exponential backoff (handles SQLite locking / PG transient errors)
  • Multi-level fallback: District → State-wide → Dept Head → UNASSIGNED (None)
  • Accepts either an AsyncSession or async_sessionmaker (prevents the
    'async_sessionmaker has no attribute execute' crash)
  • Full structured logging with complaint tracing
"""
import logging
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError, OperationalError

from app.models.user import User, RoleEnum
from app.models.complaint import Complaint, ComplaintStatus

logger = logging.getLogger("cm_dashboard.engines.assignment")

# ---------------------------------------------------------------------------
# Retry helper — exponential backoff for transient DB errors
# ---------------------------------------------------------------------------
MAX_DB_RETRIES = 3
BASE_DELAY = 0.3  # seconds


async def _execute_with_retry(session: AsyncSession, query, label: str = ""):
    """Execute a query with automatic retry on transient DB errors."""
    for attempt in range(1, MAX_DB_RETRIES + 1):
        try:
            result = await session.execute(query)
            return result.first()
        except (DBAPIError, OperationalError) as exc:
            if attempt == MAX_DB_RETRIES:
                logger.error(
                    f"[ASSIGNMENT_ENGINE]{label} DB query failed after "
                    f"{MAX_DB_RETRIES} retries: {exc}"
                )
                return None  # graceful degradation — don't crash
            delay = BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"[ASSIGNMENT_ENGINE]{label} DB retry {attempt}/{MAX_DB_RETRIES} "
                f"in {delay:.1f}s — {exc}"
            )
            await asyncio.sleep(delay)
    return None


class AssignmentEngine:
    """Deterministic officer assignment with multi-level fallback."""

    @staticmethod
    async def assign_officer(
        department: str,
        district: str,
        session_or_factory,
    ) -> Optional[int]:
        """
        Find the best officer for a complaint.

        Accepts an ``AsyncSession`` **or** an ``async_sessionmaker``.
        Returns the User ID, or ``None`` (UNASSIGNED) on any failure.
        """
        # ---- Input validation -------------------------------------------------
        if not department:
            logger.error("[ASSIGNMENT_ENGINE] department is None/empty — UNASSIGNED")
            return None
        if not district:
            district = "UNKNOWN"

        logger.info(
            f"[ASSIGNMENT_ENGINE] Attempting assignment — "
            f"Dept: {department}, District: {district}"
        )

        # ---- Resolve session vs factory ---------------------------------------
        if hasattr(session_or_factory, "execute"):
            # Already an AsyncSession
            return await AssignmentEngine._do_assign(
                session_or_factory, department, district
            )
        else:
            # It's an async_sessionmaker — open a fresh session
            async with session_or_factory() as session:
                return await AssignmentEngine._do_assign(
                    session, department, district
                )

    @staticmethod
    async def _do_assign(
        session: AsyncSession, department: str, district: str
    ) -> Optional[int]:
        """Core assignment logic with three-tier fallback."""
        try:
            active_statuses = [
                ComplaintStatus.SUBMITTED.name,
                ComplaintStatus.PROCESSING.name,
                ComplaintStatus.ESCALATED.name,
            ]

            # --- Tier 1: District + Department match ---
            q1 = (
                select(User.id, func.count(Complaint.id).label("active_workload"))
                .outerjoin(
                    Complaint,
                    (Complaint.assigned_to == User.id)
                    & (Complaint.status.in_(active_statuses)),
                )
                .where(User.role == RoleEnum.OFFICER)
                .where(User.department == department)
                .where(User.district == district)
                .group_by(User.id)
                .order_by("active_workload")
                .limit(1)
            )
            row = await _execute_with_retry(session, q1, " [Tier1]")
            if row:
                logger.info(
                    f"[ASSIGNMENT_ENGINE] ✓ Assigned Officer {row.id} "
                    f"(workload={row.active_workload})"
                )
                return row.id

            # --- Tier 2: State-wide pool (ignore district) ---
            logger.warning(
                f"[ASSIGNMENT_ENGINE] No officer in {district}. "
                f"Falling back to state-wide pool for {department}."
            )
            q2 = (
                select(User.id, func.count(Complaint.id).label("active_workload"))
                .outerjoin(
                    Complaint,
                    (Complaint.assigned_to == User.id)
                    & (Complaint.status.in_(active_statuses)),
                )
                .where(User.role == RoleEnum.OFFICER)
                .where(User.department == department)
                .group_by(User.id)
                .order_by("active_workload")
                .limit(1)
            )
            row2 = await _execute_with_retry(session, q2, " [Tier2]")
            if row2:
                logger.info(
                    f"[ASSIGNMENT_ENGINE] ✓ Fallback Officer {row2.id} "
                    f"(workload={row2.active_workload})"
                )
                return row2.id

            # --- Tier 3: Department Head ---
            logger.warning(
                f"[ASSIGNMENT_ENGINE] Falling back to Department Head for {department}."
            )
            q3 = (
                select(User.id)
                .where(User.role == RoleEnum.HEAD)
                .where(User.department == department)
                .limit(1)
            )
            head = await _execute_with_retry(session, q3, " [Tier3-Head]")
            if head:
                logger.info(
                    f"[ASSIGNMENT_ENGINE] ✓ Assigned to Dept Head {head.id}"
                )
                return head.id

            # --- All fallbacks exhausted ---
            logger.error(
                f"[ASSIGNMENT_ENGINE] ✗ UNASSIGNED — no officers/heads for {department}"
            )
            return None

        except Exception as exc:
            # Catch-all — engine must NEVER crash
            logger.error(
                f"[ASSIGNMENT_ENGINE] Unexpected error — returning UNASSIGNED: {exc}",
                exc_info=True,
            )
            return None
