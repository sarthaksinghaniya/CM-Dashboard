"""
Analytics Engine — batch metric precomputation with crash-proofing.

Hardening:
  • Each aggregation query wrapped in try/except — partial results saved
  • File I/O crash-proofed
  • Handles SQLite timedelta arithmetic (returns float, not timedelta)
  • Structured logging
"""
import logging
import json
import os
import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User

logger = logging.getLogger("cm_dashboard.engines.analytics")


class AnalyticsEngine:
    """Precomputes heavy metrics into a cached snapshot for O(1) dashboard reads."""

    CACHE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "outputs",
        "analytics_cache.json",
    )

    @staticmethod
    async def precompute_nightly_metrics(session: AsyncSession):
        """Execute heavy SQL aggregations and persist snapshot."""
        logger.info("[ANALYTICS_ENGINE] Starting nightly analytics precomputation...")

        snapshot: dict = {"timestamp": datetime.utcnow().isoformat()}

        # 1. District heatmaps
        try:
            q = (
                select(
                    Complaint.district,
                    func.count(Complaint.id).label("count"),
                )
                .filter(
                    Complaint.status.in_([
                        ComplaintStatus.SUBMITTED,
                        ComplaintStatus.PROCESSING,
                        ComplaintStatus.ESCALATED,
                    ])
                )
                .group_by(Complaint.district)
            )
            res = await session.execute(q)
            snapshot["district_heatmaps"] = {
                (row.district or "Unknown"): row.count for row in res.all()
            }
        except Exception as exc:
            logger.error(f"[ANALYTICS_ENGINE] District heatmap failed: {exc}")
            snapshot["district_heatmaps"] = {}

        # 2. Avg resolution time by department (last 30 days)
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            q_sla = (
                select(
                    Complaint.department,
                    func.avg(
                        func.julianday(Complaint.updated_at)
                        - func.julianday(Complaint.created_at)
                    ).label("avg_days"),
                )
                .filter(Complaint.status == ComplaintStatus.RESOLVED)
                .filter(Complaint.created_at >= thirty_days_ago)
                .group_by(Complaint.department)
            )
            res_sla = await session.execute(q_sla)
            sla_stats = {}
            for row in res_sla.all():
                if row.avg_days is not None:
                    hours = float(row.avg_days) * 24
                    sla_stats[row.department or "Unknown"] = round(hours, 2)
            snapshot["department_sla_hours"] = sla_stats
        except Exception as exc:
            logger.error(f"[ANALYTICS_ENGINE] SLA computation failed: {exc}")
            snapshot["department_sla_hours"] = {}

        # 3. Top officers by resolved count
        try:
            q_off = (
                select(
                    User.id,
                    User.name,
                    func.count(Complaint.id).label("resolved_count"),
                )
                .join(Complaint, Complaint.assigned_to == User.id)
                .filter(Complaint.status == ComplaintStatus.RESOLVED)
                .group_by(User.id, User.name)
                .order_by(func.count(Complaint.id).desc())
                .limit(10)
            )
            res_off = await session.execute(q_off)
            snapshot["top_officers"] = [
                {"id": r.id, "name": r.name, "resolved_count": r.resolved_count}
                for r in res_off.all()
            ]
        except Exception as exc:
            logger.error(f"[ANALYTICS_ENGINE] Officer stats failed: {exc}")
            snapshot["top_officers"] = []

        # 4. Save
        await AnalyticsEngine._save_snapshot(snapshot)
        logger.info(
            "[ANALYTICS_ENGINE] Nightly analytics precomputation completed successfully."
        )

    @staticmethod
    async def _save_snapshot(snapshot: dict):
        """Safely write cached analytics to disk."""
        def _sync_write():
            try:
                os.makedirs(os.path.dirname(AnalyticsEngine.CACHE_PATH), exist_ok=True)
                with open(AnalyticsEngine.CACHE_PATH, "w") as f:
                    json.dump(snapshot, f, indent=4)
            except Exception as exc:
                logger.error(f"[ANALYTICS_ENGINE] Snapshot save failed: {exc}")

        await asyncio.to_thread(_sync_write)

    @staticmethod
    async def get_latest_analytics() -> dict:
        """O(1) read for dashboard endpoint."""
        def _sync_read():
            if not os.path.exists(AnalyticsEngine.CACHE_PATH):
                return {"error": "Analytics not precomputed yet."}
            try:
                with open(AnalyticsEngine.CACHE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return {"error": "Failed to read analytics cache."}

        return await asyncio.to_thread(_sync_read)
