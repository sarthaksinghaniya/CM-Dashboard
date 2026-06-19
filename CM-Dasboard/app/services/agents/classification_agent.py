from typing import Dict, Any, List
from .base_agent import BaseAgent
from app.services.ml.inference import MLInferenceService

class ClassificationAgent(BaseAgent):
    """
    Agent responsible for analyzing the text and determining the incident category.
    Participates in negotiation if conflicts arise.
    """
    def __init__(self):
        super().__init__()
        self.inference_service = MLInferenceService()
        
    async def process(self, text: str, context: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Baseline prediction for classification.
        """
        model_pred = self.inference_service.predict(text)
        
        # We only care about classification
        cat = model_pred.get("category_pred", "OTHER")
        conf = model_pred.get("confidence_score", 0.5)
        
        return {
            "prediction": cat,
            "confidence": conf,
            "reason": f"Initial model prediction based on semantic embedding."
        }
        
    async def re_evaluate(self, text: str, context: List[Dict[str, Any]], conflicts: List[str], peer_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate based on peer pushback.
        """
        baseline = await self.process(text, context)
        current_pred = baseline["prediction"]
        current_conf = baseline["confidence"]
        
        # Analyze context to see if FAISS overrides the model
        categories = [c.get("incident_type") or c.get("category") for c in context] if context else []
        if categories:
            from collections import Counter
            common_cat = Counter(categories).most_common(1)[0][0]
            
            # If peers are complaining (e.g. routing says GENERAL_SUPPORT but we said FIRE)
            # and memory says something else, we might yield
            if common_cat != current_pred and current_conf < 0.8:
                return {
                    "prediction": common_cat,
                    "confidence": current_conf + 0.1,
                    "reason": f"Yielded to FAISS memory '{common_cat}' due to peer conflict: {conflicts[0]}"
                }
                
        # If confidence is very high, stand ground
        return {
            "prediction": current_pred,
            "confidence": current_conf,
            "reason": "Stood ground on initial prediction despite peer conflict."
        }
