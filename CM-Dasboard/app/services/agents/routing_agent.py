from typing import Dict, Any, List
from .base_agent import BaseAgent

class RoutingAgent(BaseAgent):
    """
    Agent responsible for routing the incident to the correct department.
    Participates in negotiation if conflicts arise.
    """
    
    async def process(self, text: str, context: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Baseline heuristic prediction for routing.
        """
        text_lower = text.lower()
        if any(word in text_lower for word in ["fire", "smoke", "burn"]):
            pred = "FIRE_DEPARTMENT"
            conf = 0.8
        elif any(word in text_lower for word in ["medical", "injured", "heart"]):
            pred = "EMS"
            conf = 0.8
        elif any(word in text_lower for word in ["police", "gun", "robbery", "theft", "crime"]):
            pred = "LAW_ENFORCEMENT"
            conf = 0.8
        elif any(word in text_lower for word in ["water", "pipe", "leak", "dry tap"]):
            pred = "WATER_BOARD"
            conf = 0.8
        elif any(word in text_lower for word in ["power", "electricity", "outage"]):
            pred = "POWER_GRID"
            conf = 0.8
        elif any(word in text_lower for word in ["garbage", "trash", "sewage"]):
            pred = "SANITATION_DEPT"
            conf = 0.8
        elif any(word in text_lower for word in ["pothole", "road", "street"]):
            pred = "PUBLIC_WORKS"
            conf = 0.8
        else:
            pred = "GENERAL_SUPPORT"
            conf = 0.5
            
        return {
            "prediction": pred,
            "confidence": conf,
            "reason": "Initial heuristic routing based on keywords."
        }
        
    async def re_evaluate(self, text: str, context: List[Dict[str, Any]], conflicts: List[str], peer_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-evaluate based on peer pushback.
        """
        baseline = await self.process(text, context)
        current_pred = baseline["prediction"]
        current_conf = baseline["confidence"]
        
        peer_cat = peer_predictions.get("classification", {}).get("prediction", "")
        peer_cat_conf = peer_predictions.get("classification", {}).get("confidence", 0)
        
        peer_complaint = peer_predictions.get("complaint", {}).get("prediction", [])
        peer_complaint_conf = peer_predictions.get("complaint", {}).get("confidence", 0)
        
        # Incident Mapping
        dept_mapping = {"FIRE": "FIRE_DEPARTMENT", "MEDICAL": "EMS", "POLICE": "LAW_ENFORCEMENT"}
        
        # Complaint Mapping
        complaint_mapping = {
            "WATER_SUPPLY": "WATER_BOARD",
            "ELECTRICITY": "POWER_GRID",
            "SANITATION": "SANITATION_DEPT",
            "ROADS": "PUBLIC_WORKS",
            "TRAFFIC": "LAW_ENFORCEMENT",
            "HEALTHCARE": "HEALTH_DEPT",
            "LAW_ORDER": "LAW_ENFORCEMENT",
            "CORRUPTION": "ANTI_CORRUPTION_BUREAU"
        }
        
        expected_routing_inc = dept_mapping.get(peer_cat)
        
        # Grab the first matching department from the list of complaints
        expected_routing_comp = None
        for comp in peer_complaint:
            if comp in complaint_mapping:
                expected_routing_comp = complaint_mapping[comp]
                break
        
        # Yield to Complaint Agent if it's highly confident
        if expected_routing_comp and expected_routing_comp != current_pred and peer_complaint_conf > current_conf:
            return {
                "prediction": expected_routing_comp,
                "confidence": peer_complaint_conf,
                "reason": f"Yielded routing to match highly confident peer complaint classifications '{peer_complaint}'."
            }
            
        # Yield to Classification Agent
        if expected_routing_inc and expected_routing_inc != current_pred and peer_cat_conf > current_conf:
            return {
                "prediction": expected_routing_inc,
                "confidence": peer_cat_conf,
                "reason": f"Yielded routing to match highly confident peer classification '{peer_cat}'."
            }
            
        return {
            "prediction": current_pred,
            "confidence": current_conf,
            "reason": "Stood ground on initial routing prediction."
        }
