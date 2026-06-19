from typing import Dict, Any, List
from .base_agent import BaseAgent
from app.services.ml.inference import MLInferenceService

class SeverityAgent(BaseAgent):
    """
    Agent responsible for analyzing the text and determining the incident severity.
    Participates in negotiation if conflicts arise.
    """
    def __init__(self):
        super().__init__()
        self.inference_service = MLInferenceService()
        
    async def process(self, text: str, context: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Baseline prediction for severity.
        """
        model_pred = self.inference_service.predict(text)
        
        # We only care about severity
        sev = model_pred.get("severity_pred", "LOW")
        conf = model_pred.get("confidence_score", 0.5)
        
        return {
            "prediction": sev,
            "confidence": conf,
            "reason": f"Initial severity model prediction."
        }
        
    async def re_evaluate(self, text: str, context: List[Dict[str, Any]], conflicts: List[str], peer_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate based on peer pushback.
        """
        baseline = await self.process(text, context)
        current_pred = baseline["prediction"]
        current_conf = baseline["confidence"]
        
        peer_cat = peer_predictions.get("classification", {}).get("prediction", "")
        peer_routing = peer_predictions.get("routing", {}).get("prediction", "")
        
        # If classification says FIRE and routing says FIRE_DEPARTMENT, but we said LOW severity -> adjust
        if peer_cat == "FIRE" and current_pred in ["LOW", "MEDIUM"]:
            return {
                "prediction": "HIGH",
                "confidence": current_conf + 0.2,
                "reason": "Escalated severity to HIGH because peers reached consensus on FIRE category."
            }
            
        if peer_routing == "GENERAL_SUPPORT" and current_pred == "CRITICAL":
            return {
                "prediction": "MEDIUM",
                "confidence": current_conf,
                "reason": "Downgraded severity because peers routed to general support."
            }
            
        return {
            "prediction": current_pred,
            "confidence": current_conf,
            "reason": "Stood ground on initial severity prediction."
        }
