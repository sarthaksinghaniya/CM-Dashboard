import logging
import json
import os
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.feedback import Feedback
from app.models.complaint import Complaint
from app.engines.faiss_rag import FaissMemory

logger = logging.getLogger("cm_dashboard.engines.rl_feedback")

class RLEngine:
    """
    Reinforcement Learning Engine.
    Captures resolution success and citizen feedback signals to compute rewards.
    Applies real-time boosting/deprecation to FAISS RAG Memory and logs signals 
    for periodic offline fine-tuning.
    """
    
    LEDGER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs", "rl_ledger.json")

    @staticmethod
    async def process_feedback(complaint_id: int, rating: int, comments: str, session: AsyncSession):
        """
        Process citizen feedback and apply RL signals.
        """
        logger.info(f"[RL_ENGINE] Processing Feedback for complaint ID {complaint_id} with rating {rating}/5")
        
        # 1. Fetch Complaint Context
        query = select(Complaint).filter(Complaint.id == complaint_id)
        res = await session.execute(query)
        complaint = res.scalars().first()
        
        if not complaint:
            logger.error(f"[RL_ENGINE] Complaint ID {complaint_id} not found.")
            return
            
        text = complaint.description or complaint.title
        
        # 2. Compute Reward Signal
        # Ratings: 1-2 -> Negative (-1.0), 3 -> Neutral (0.0), 4-5 -> Positive (+1.0)
        reward = 0.0
        if rating <= 2:
            reward = -1.0
        elif rating >= 4:
            reward = 1.0
            
        # 3. Apply to RAG Memory
        if reward != 0.0:
            memory = FaissMemory()
            metadata = {
                "ticket_id": complaint.ticket_id,
                "rating": rating,
                "rl_applied": True
            }
            await memory.async_apply_rl_reward(text, reward, metadata)
            
        # 4. Store offline training signal
        signal = {
            "ticket_id": complaint.ticket_id,
            "text": text,
            "category": complaint.category,
            "assigned_to": complaint.assigned_to,
            "rating": rating,
            "reward": reward,
            "comments": comments
        }
        await RLEngine._append_to_ledger(signal)
        logger.info(f"[RL_ENGINE] Feedback processed successfully. Reward: {reward}")

    @staticmethod
    async def process_resolution_success(complaint: Complaint):
        """
        Processes automated success signal based on SLA timeline.
        Called when a complaint transitions to RESOLVED.
        """
        # If no delays and retry_count is low, assign positive reward
        # This acts as an automated reinforcement loop even without citizen feedback
        reward = 1.0 if complaint.retry_count == 0 else 0.0
        
        if reward > 0:
            memory = FaissMemory()
            text = complaint.description or complaint.title
            metadata = {
                "ticket_id": complaint.ticket_id,
                "auto_resolved": True,
                "rl_applied": True
            }
            await memory.async_apply_rl_reward(text, reward, metadata)

    @staticmethod
    async def _append_to_ledger(signal: Dict[str, Any]):
        """Safely append the signal to the local JSON ledger for ML retraining batch jobs."""
        def sync_write():
            ledger = []
            os.makedirs(os.path.dirname(RLEngine.LEDGER_PATH), exist_ok=True)
            if os.path.exists(RLEngine.LEDGER_PATH):
                try:
                    with open(RLEngine.LEDGER_PATH, "r") as f:
                        ledger = json.load(f)
                except json.JSONDecodeError:
                    pass
            ledger.append(signal)
            with open(RLEngine.LEDGER_PATH, "w") as f:
                json.dump(ledger, f, indent=4)
                
        await asyncio.to_thread(sync_write)
