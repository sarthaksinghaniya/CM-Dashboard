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
    """
    Analytics precomputation engine.
    Aggregates heavy metrics (district workloads, SLA resolution times) into
    batch-computed caches for O(1) dashboard retrieval.
    """
    
    CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs", "analytics_cache.json")

    @staticmethod
    async def precompute_nightly_metrics(session: AsyncSession):
        """
        Executes heavy SQL aggregations and saves the snapshot to disk/redis.
        Should be invoked via the Scheduler Engine.
        """
        logger.info("[ANALYTICS_ENGINE] Starting nightly analytics precomputation...")
        
        # 1. District Heatmaps (Open Complaints)
        district_query = (
            select(Complaint.district, func.count(Complaint.id).label("count"))
            .filter(Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.PROCESSING, ComplaintStatus.ESCALATED]))
            .group_by(Complaint.district)
        )
        res_district = await session.execute(district_query)
        district_stats = {row.district or "Unknown": row.count for row in res_district.all()}
        
        # 2. Resolution Time (Average SLA Time by Department)
        # We estimate by looking at resolved complaints from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sla_query = (
            select(Complaint.department, func.avg(Complaint.updated_at - Complaint.created_at).label("avg_resolve_time"))
            .filter(Complaint.status == ComplaintStatus.RESOLVED)
            .filter(Complaint.created_at >= thirty_days_ago)
            .group_by(Complaint.department)
        )
        res_sla = await session.execute(sla_query)
        sla_stats = {}
        for row in res_sla.all():
            avg_delta = row.avg_resolve_time
            if avg_delta:
                # Convert timedelta to hours
                hours = avg_delta.total_seconds() / 3600
                sla_stats[row.department or "Unknown"] = round(hours, 2)
                
        # 3. Officer Performance (Resolved counts)
        officer_query = (
            select(User.id, User.name, func.count(Complaint.id).label("resolved_count"))
            .join(Complaint, Complaint.assigned_to == User.id)
            .filter(Complaint.status == ComplaintStatus.RESOLVED)
            .group_by(User.id, User.name)
            .order_by(func.count(Complaint.id).desc())
            .limit(10)
        )
        res_officer = await session.execute(officer_query)
        officer_stats = [{"id": row.id, "name": row.name, "resolved_count": row.resolved_count} for row in res_officer.all()]
        
        # 4. Construct Snapshot
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "district_heatmaps": district_stats,
            "department_sla_hours": sla_stats,
            "top_officers": officer_stats
        }
        
        # 5. Persist Snapshot
        await AnalyticsEngine._save_snapshot(snapshot)
        logger.info("[ANALYTICS_ENGINE] Nightly analytics precomputation completed successfully.")

    @staticmethod
    async def _save_snapshot(snapshot: dict):
        """Safely write to the cached ledger."""
        def sync_write():
            os.makedirs(os.path.dirname(AnalyticsEngine.CACHE_PATH), exist_ok=True)
            with open(AnalyticsEngine.CACHE_PATH, "w") as f:
                json.dump(snapshot, f, indent=4)
                
        await asyncio.to_thread(sync_write)
        
    @staticmethod
    async def get_latest_analytics() -> dict:
        """O(1) read for dashboard."""
        def sync_read():
            if not os.path.exists(AnalyticsEngine.CACHE_PATH):
                return {"error": "Analytics not precomputed yet."}
            with open(AnalyticsEngine.CACHE_PATH, "r") as f:
                return json.load(f)
        return await asyncio.to_thread(sync_read)
