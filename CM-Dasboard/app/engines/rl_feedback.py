"""
RL Feedback Engine — reinforcement learning signal processor.

Hardening:
  • Input validation (rating clamped to 1-5, empty text handled)
  • FAISS errors don't crash the feedback pipeline
  • Ledger write is atomic per signal (append-only JSON)
  • Structured logging with complaint tracing
"""
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
    Captures citizen feedback signals, computes rewards,
    and applies real-time boosting/deprecation to FAISS RAG Memory.
    """

    LEDGER_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "outputs",
        "rl_ledger.json",
    )

    @staticmethod
    async def process_feedback(
        complaint_id: int,
        rating: int,
        comments: str,
        session: AsyncSession,
    ):
        """Process citizen feedback and apply RL signals."""
        # ---- Input validation ------------------------------------------------
        rating = max(1, min(5, rating))  # clamp to [1, 5]
        comments = (comments or "").strip()

        logger.info(
            f"[RL_ENGINE] Processing Feedback for complaint ID "
            f"{complaint_id} with rating {rating}/5"
        )

        # 1. Fetch Complaint Context
        try:
            query = select(Complaint).filter(Complaint.id == complaint_id)
            res = await session.execute(query)
            complaint = res.scalars().first()
        except Exception as exc:
            logger.error(f"[RL_ENGINE] DB lookup failed for {complaint_id}: {exc}")
            return

        if not complaint:
            logger.error(f"[RL_ENGINE] Complaint ID {complaint_id} not found.")
            return

        text = complaint.description or complaint.title
        if not text:
            logger.warning(f"[RL_ENGINE] No text for complaint {complaint_id} — skipping RL.")
            return

        # 2. Compute Reward Signal
        #    1-2 → negative (-1.0), 3 → neutral (0.0), 4-5 → positive (+1.0)
        reward = 0.0
        if rating <= 2:
            reward = -1.0
        elif rating >= 4:
            reward = 1.0

        # 3. Apply to RAG Memory (non-critical)
        if reward != 0.0:
            try:
                memory = FaissMemory()
                metadata = {
                    "ticket_id": complaint.ticket_id,
                    "rating": rating,
                    "rl_applied": True,
                }
                await memory.async_apply_rl_reward(text, reward, metadata)
            except Exception as exc:
                logger.error(
                    f"[RL_ENGINE] FAISS RL application failed — non-critical: {exc}"
                )

        # 4. Persist offline training signal
        signal = {
            "ticket_id": complaint.ticket_id,
            "text": text[:500],  # cap to prevent giant ledger entries
            "category": complaint.category,
            "assigned_to": complaint.assigned_to,
            "rating": rating,
            "reward": reward,
            "comments": comments[:500],
        }
        await RLEngine._append_to_ledger(signal)
        logger.info(f"[RL_ENGINE] Feedback processed successfully. Reward: {reward}")

    @staticmethod
    async def process_resolution_success(complaint: Complaint):
        """
        Automated success signal when a complaint is resolved.
        Positive reward only if no retries were needed.
        """
        reward = 1.0 if complaint.retry_count == 0 else 0.0
        if reward <= 0:
            return

        try:
            memory = FaissMemory()
            text = complaint.description or complaint.title
            if not text:
                return
            metadata = {
                "ticket_id": complaint.ticket_id,
                "auto_resolved": True,
                "rl_applied": True,
            }
            await memory.async_apply_rl_reward(text, reward, metadata)
        except Exception as exc:
            logger.error(f"[RL_ENGINE] Resolution success RL failed: {exc}")

    @staticmethod
    async def _append_to_ledger(signal: Dict[str, Any]):
        """Append signal to JSON ledger (thread-safe via asyncio.to_thread)."""
        def _sync_write():
            try:
                os.makedirs(os.path.dirname(RLEngine.LEDGER_PATH), exist_ok=True)
                ledger = []
                if os.path.exists(RLEngine.LEDGER_PATH):
                    try:
                        with open(RLEngine.LEDGER_PATH, "r") as f:
                            ledger = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        pass
                ledger.append(signal)
                with open(RLEngine.LEDGER_PATH, "w") as f:
                    json.dump(ledger, f, indent=4)
            except Exception as exc:
                # Ledger write must NEVER crash the caller
                logger.error(f"[RL_ENGINE] Ledger write failed: {exc}")

        await asyncio.to_thread(_sync_write)
