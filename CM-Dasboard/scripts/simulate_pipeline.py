import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.models.complaint import Complaint, PriorityEnum, ComplaintStatus
from app.services.pipeline.engine import PipelineEngine
from app.engines.escalation import EscalationEngine
from app.engines.analytics import AnalyticsEngine
from app.engines.faiss_rag import FaissMemory
from app.engines.rl_feedback import RLEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cm_dashboard.simulation")

# Disable access logs from other components for cleaner trace
logging.getLogger("httpx").setLevel(logging.WARNING)

async def run_simulation():
    logger.info("=== STARTING FULL BACKEND CORE SIMULATION ===")
    
    # 1. 100-Complaint Batch Ingestion
    logger.info("--- [TEST 1] INJECTING 100 BATCH COMPLAINTS ---")
    ticket_ids = []
    async with AsyncSessionLocal() as session:
        for i in range(100):
            ticket_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
            ticket_ids.append(ticket_id)
            c = Complaint(
                ticket_id=ticket_id,
                title=f"Simulated Issue {i}",
                description="This is a test issue for the AI pipeline.",
                citizen_name="Sim User",
                citizen_phone="1234567890",
                district="North Delhi" if i % 2 == 0 else "South Delhi",
                category="OTHER",
                department="GENERAL_DEPT",
                status=ComplaintStatus.SUBMITTED
            )
            session.add(c)
        await session.commit()
    logger.info(f"Successfully injected 100 complaints.")
    
    # 2. Concurrent Processing
    logger.info("--- [TEST 2] CONCURRENT AI ROUTING (100 TASKS with Semaphore) ---")
    # SQLite local DBs do not support concurrent async transactions. Set to 1 for simulation.
    sem = asyncio.Semaphore(1)
    async def bound_execute(tid):
        async with sem:
            await PipelineEngine.execute_core(tid, AsyncSessionLocal)
            
    tasks = [bound_execute(tid) for tid in ticket_ids]
    await asyncio.gather(*tasks)
    logger.info("Concurrent processing completed.")
    
    # Verify results
    async with AsyncSessionLocal() as session:
        query = select(Complaint).filter(Complaint.ticket_id.in_(ticket_ids))
        res = await session.execute(query)
        processed = res.scalars().all()
        resolved_count = sum(1 for c in processed if c.status == ComplaintStatus.RESOLVED)
        logger.info(f"Verification: {resolved_count}/100 complaints resolved by DecisionAgent.")
        
    # 3. Escalation Trigger Simulation
    logger.info("--- [TEST 3] DELAYED SLA ESCALATION TRIGGER ---")
    async with AsyncSessionLocal() as session:
        # Reopen 5 complaints and age them 20 days
        for i in range(5):
            c = processed[i]
            c.status = ComplaintStatus.PROCESSING
            c.created_at = datetime.utcnow() - timedelta(days=20)
            session.add(c)
        await session.commit()
        
    # Run Escalation Engine
    async with AsyncSessionLocal() as session:
        await EscalationEngine.process_escalations(session)
        
    # 4. RL Feedback Loop
    logger.info("--- [TEST 4] RL FEEDBACK LOOP INJECTION ---")
    async with AsyncSessionLocal() as session:
        c = processed[10]
        logger.info(f"Submitting 1-star feedback for {c.ticket_id} to trigger memory deprecation.")
        await RLEngine.process_feedback(c.id, rating=1, comments="Terrible!", session=session)
        
    # 5. Analytics Aggregation
    logger.info("--- [TEST 5] ANALYTICS AGGREGATION ---")
    async with AsyncSessionLocal() as session:
        await AnalyticsEngine.precompute_nightly_metrics(session)
        
    # 6. FAISS Failure Simulation
    logger.info("--- [TEST 6] FAISS OUTAGE SIMULATION ---")
    # We will temporarily break FAISS's add_memory and see if it crashes the pipeline
    original_add_memory = FaissMemory.add_memory
    
    def fake_faiss_fail(*args, **kwargs):
        raise RuntimeError("FAISS OUT OF MEMORY SIMULATION")
        
    FaissMemory.add_memory = fake_faiss_fail
    
    async with AsyncSessionLocal() as session:
        fail_tid = f"FAIL-{uuid.uuid4().hex[:8].upper()}"
        c = Complaint(
            ticket_id=fail_tid,
            title="Faiss Outage Test",
            description="Testing graceful failure.",
            citizen_name="Sim User",
            district="North Delhi",
            category="OTHER",
            department="GENERAL_DEPT",
            status=ComplaintStatus.SUBMITTED
        )
        session.add(c)
        await session.commit()
        
    logger.info("Running pipeline with simulated FAISS failure...")
    await PipelineEngine.execute_core(fail_tid, AsyncSessionLocal)
    
    async with AsyncSessionLocal() as session:
        query = select(Complaint).filter(Complaint.ticket_id == fail_tid)
        res = await session.execute(query)
        fail_c = res.scalars().first()
        logger.info(f"After FAISS failure, status is: {fail_c.status.name}")
        
    # Restore FAISS
    FaissMemory.add_memory = original_add_memory
    
    logger.info("=== FULL SIMULATION COMPLETE. 0 CRASHES! ===")

if __name__ == "__main__":
    asyncio.run(run_simulation())
