import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from threading import RLock

logger = logging.getLogger("cm_dashboard.services.feedback_manager")

_ledger_lock = RLock()

class FeedbackManager:
    """
    Handles the Reinforcement Learning feedback loop, calculating rewards,
    persisting the feedback ledger thread-safely, and updating rolling averages.
    """
    def __init__(self, ledger_path: str = None):
        if ledger_path is None:
            # Default path relative to project root
            self.ledger_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "outputs",
                "feedback_ledger.json"
            )
        else:
            self.ledger_path = ledger_path

        # Create directory if missing
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        self.ledger = self._load_ledger()
        
    def _load_ledger(self) -> List[Dict[str, Any]]:
        """
        Safely load ledger from disk under lock. Handles missing file and corrupted JSON gracefully.
        """
        with _ledger_lock:
            if not os.path.exists(self.ledger_path):
                logger.info(f"Ledger file missing. Initializing fresh ledger at {self.ledger_path}")
                return []
            try:
                with open(self.ledger_path, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Ledger file corrupted at {self.ledger_path}: {e}. Resetting to empty list.")
                return []
            except Exception as e:
                logger.error(f"Unexpected error loading ledger: {e}")
                return []
        
    def _save_ledger(self):
        """
        Safely write cached ledger snapshot to disk under lock.
        """
        with _ledger_lock:
            try:
                os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
                with open(self.ledger_path, 'w') as f:
                    json.dump(self.ledger, f, indent=2)
            except Exception as e:
                logger.error(f"[FEEDBACK_MANAGER_ERROR] Failed saving ledger: {str(e)}")

    def calculate_reward(self, predicted: Dict[str, Any], actual: Dict[str, Any], rag_agreement: bool = False, is_corrected: bool = False) -> float:
        """
        Calculates the reward based on the prediction accuracy, confidence parameters,
        and officer correction status.
        """
        pred_cat = predicted.get("category")
        actual_cat = actual.get("category")
        
        pred_sev = predicted.get("severity") or predicted.get("urgency_level")
        actual_sev = actual.get("severity") or actual.get("urgency_level")
        
        confidence = predicted.get("confidence", 0.5)
        reward = 0.0
        
        # Exact match structural validation check
        if pred_cat == actual_cat and pred_sev == actual_sev:
            reward += 1.0
        else:
            # Wrong prediction penalty adjustments
            if confidence > 0.8:
                reward -= 2.0  # High confidence penalization penalty
            else:
                reward -= 1.0
                
            # Officer corrected AI: bonus +0.5
            if is_corrected:
                reward += 0.5
                
        # RAG reward alignment allocation 
        if rag_agreement:
            reward += 0.5
            
        return reward

    def submit_feedback(self, incident_text: str, predicted: Dict[str, Any], actual: Dict[str, Any], rag_agreement: bool = False, is_corrected: bool = False) -> float:
        """
        Submits human-corrected feedback, calculates reward mechanics, and writes records.
        """
        reward = self.calculate_reward(predicted, actual, rag_agreement, is_corrected)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident": incident_text,
            "predicted": predicted,
            "actual": actual,
            "reward": reward,
            "rag_agreement": rag_agreement,
            "is_corrected": is_corrected
        }
        
        with _ledger_lock:
            self.ledger = self._load_ledger()
            self.ledger.append(record)
            self._save_ledger()
        return reward

    def record_citizen_rating(self, ticket_id: str, rating: int, remarks: str = None) -> float:
        """
        Record a citizen rating and calculate its corresponding RL reward.
        5 star -> +1.0
        4 star -> +0.5
        3 star -> 0.0
        2 star -> -1.0
        1 star -> -2.0
        """
        rating_map = {
            5: 1.0,
            4: 0.5,
            3: 0.0,
            2: -1.0,
            1: -2.0
        }
        reward = rating_map.get(rating, 0.0)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticket_id": ticket_id,
            "type": "citizen_rating",
            "rating": rating,
            "remarks": remarks,
            "reward": reward
        }

        with _ledger_lock:
            self.ledger = self._load_ledger()
            self.ledger.append(record)
            self._save_ledger()

        return reward

    def get_average_reward(self, last_n: int = 20) -> float:
        """
        Retrieve rolling average of the last N rewards.
        """
        with _ledger_lock:
            self.ledger = self._load_ledger()
            if not self.ledger:
                return 0.0
            recent = self.ledger[-last_n:]
            total = sum(r.get("reward", 0.0) for r in recent)
            return total / len(recent) if recent else 0.0