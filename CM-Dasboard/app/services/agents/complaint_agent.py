from typing import Dict, Any, List
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class ComplaintAgent(BaseAgent):
    """
    Agent responsible for classifying civic complaints into specific categories.
    Categories: WATER_SUPPLY, ELECTRICITY, SANITATION, ROADS, TRAFFIC, HEALTHCARE, LAW_ORDER, CORRUPTION, OTHER
    Returns a LIST of complaint categories (Multi-label).
    """
    
    async def process(self, text: str, context: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Initial heuristic prediction.
        """
        text_lower = text.lower()
        
        mapping = {
            "WATER_SUPPLY": ["water", "pipe", "leak", "dry tap", "drinking"],
            "ELECTRICITY": ["power", "electricity", "outage", "blackout", "wire", "voltage"],
            "SANITATION": ["garbage", "trash", "waste", "sewage", "drain", "clean"],
            "ROADS": ["pothole", "road", "street", "pavement", "asphalt"],
            "TRAFFIC": ["traffic", "jam", "signal", "accident", "congestion"],
            "HEALTHCARE": ["hospital", "clinic", "ambulance", "doctor", "medicine"],
            "LAW_ORDER": ["police", "theft", "crime", "robbery", "gun"],
            "CORRUPTION": ["bribe", "corruption", "fraud", "scam", "payoff"]
        }
        
        preds = []
        conf = 0.5
        reason = "No specific keywords matched, defaulted to OTHER."
        
        for category, keywords in mapping.items():
            if any(k in text_lower for k in keywords):
                preds.append(category)
                
        if len(preds) > 0:
            conf = 0.7 + (0.05 * (len(preds) - 1))  # Slightly higher confidence if multiple detected
            reason = f"Keyword match found for {len(preds)} categories."
        else:
            preds = ["OTHER"]
                
        return {
            "prediction": preds,
            "confidence": conf,
            "reason": reason
        }
        
    async def re_evaluate(self, text: str, context: List[Dict[str, Any]], conflicts: List[str], peer_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate based on peer pushback.
        """
        baseline = await self.process(text, context)
        current_preds = baseline["prediction"]
        current_conf = baseline["confidence"]
        
        # If there are conflicts, see if RAG context strongly implies something else
        if conflicts and context:
            category_counts = {}
            for c in context:
                # Expecting a list in the metadata now
                mem_cats = c.get("metadata", {}).get("complaint_categories", [])
                for cat in mem_cats:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    
            injected = False
            for cat, count in category_counts.items():
                if count >= 2 and cat not in current_preds and cat != "OTHER":
                    if "OTHER" in current_preds:
                        current_preds.remove("OTHER")
                    current_preds.append(cat)
                    injected = True
            
            if injected:
                return {
                    "prediction": current_preds,
                    "confidence": 0.8,
                    "reason": f"Injected new categories from highly recurrent RAG memory past cases."
                }
                    
        return {
            "prediction": current_preds,
            "confidence": current_conf,
            "reason": "Stood ground on initial multi-label complaint prediction."
        }
