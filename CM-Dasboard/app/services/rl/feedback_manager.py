import json
import os
import datetime
from typing import Dict, Any, List

class FeedbackManager:
    """
    Handles the Reinforcement Learning feedback loop, calculating rewards,
    and persisting the feedback ledger for future fine-tuning.
    """
    def __init__(self, ledger_path: str = "outputs/feedback_ledger.json"):
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        self.ledger = self._load_ledger()
        
    def _load_ledger(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
        
    def _save_ledger(self):
        with open(self.ledger_path, 'w') as f:
            json.dump(self.ledger, f, indent=2)
            
    def calculate_reward(self, predicted: Dict[str, Any], actual: Dict[str, Any], rag_agreement: bool = False) -> float:
        """
        Calculates the reward based on the prediction accuracy and confidence.
        """
        pred_cat = predicted.get("category")
        actual_cat = actual.get("category")
        
        pred_sev = predicted.get("severity")
        actual_sev = actual.get("severity")
        
        confidence = predicted.get("confidence", 0.5)
        
        reward = 0.0
        
        # Exact match
        if pred_cat == actual_cat and pred_sev == actual_sev:
            reward += 1.0
        else:
            # Wrong prediction
            if confidence > 0.8:
                # High confidence wrong
                reward -= 2.0
            else:
                reward -= 1.0
                
        # RAG bonus if the model agreed with RAG originally
        if rag_agreement:
            reward += 0.5
            
        return reward

    def submit_feedback(self, incident_text: str, predicted: Dict[str, Any], actual: Dict[str, Any], rag_agreement: bool = False) -> float:
        """
        Submits human-corrected feedback, calculates reward, and logs it.
        """
        reward = self.calculate_reward(predicted, actual, rag_agreement)
        
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "incident": incident_text,
            "predicted": predicted,
            "actual": actual,
            "reward": reward,
            "rag_agreement": rag_agreement
        }
        
        self.ledger.append(record)
        self._save_ledger()
        return reward
        
    def get_average_reward(self, last_n: int = 50) -> float:
        if not self.ledger:
            return 0.0
        recent = self.ledger[-last_n:]
        total = sum(r.get("reward", 0.0) for r in recent)
        return total / len(recent)
