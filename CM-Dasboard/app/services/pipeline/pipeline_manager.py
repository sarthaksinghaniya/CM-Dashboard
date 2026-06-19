from typing import Dict, Any, List
import uuid
import datetime
import logging
from app.services.agents.classification_agent import ClassificationAgent
from app.services.agents.severity_agent import SeverityAgent
from app.services.agents.routing_agent import RoutingAgent
from app.services.agents.complaint_agent import ComplaintAgent
from app.services.memory.faiss_memory import FaissMemory
from app.services.memory.retriever import ContextRetriever
from app.services.rl.policy import DynamicPolicyEngine
from app.services.rl.feedback_manager import FeedbackManager
from app.services.geo.geo_tagger import GeoTagger
from app.services.geo.cluster_engine import ClusterEngine
from app.services.pipeline.async_queue import AsyncQueue

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    Orchestrates the Negotiation-Based Multi-Agent System.
    Integrates RL dynamic policies and Civic Complaint routing.
    """
    def __init__(self):
        self.classification_agent = ClassificationAgent()
        self.severity_agent = SeverityAgent()
        self.routing_agent = RoutingAgent()
        self.complaint_agent = ComplaintAgent()
        self.memory = FaissMemory()
        self.retriever = ContextRetriever()
        self.policy_engine = DynamicPolicyEngine()
        self.feedback_manager = self.policy_engine.feedback_manager
        self.geo_tagger = GeoTagger()
        self.cluster_engine = ClusterEngine()
        self.async_queue = AsyncQueue()
        
    async def start_background_workers(self):
        """Starts the execution queue workers."""
        await self.async_queue.start_workers()
        
    async def stop_background_workers(self):
        """Stops the execution queue workers."""
        await self.async_queue.stop_workers()

    def submit_rl_feedback(self, incident_id: str, incident_text: str, predicted: Dict[str, Any], actual: Dict[str, Any], rag_agreement: bool) -> float:
        """
        Public hook to submit human correction, calculate reward, and update FAISS memory directly.
        """
        reward = self.feedback_manager.submit_feedback(incident_text, predicted, actual, rag_agreement)
        self.memory.apply_rl_reward(incident_text, reward, metadata=actual)
        return reward

    def _detect_conflicts(self, cat_pred: str, sev_pred: str, routing_pred: str, comp_preds: List[str]) -> List[str]:
        conflicts = []
        dept_mapping = {"FIRE": "FIRE_DEPARTMENT", "MEDICAL": "EMS", "POLICE": "LAW_ENFORCEMENT"}
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
        
        expected_routing = dept_mapping.get(cat_pred)
        if expected_routing and routing_pred != expected_routing:
            conflicts.append(f"Classification '{cat_pred}' implies '{expected_routing}', but routing chose '{routing_pred}'.")
            
        # Check if routing matches at least one of the complaint categories
        expected_comp_routings = [complaint_mapping.get(c) for c in comp_preds if complaint_mapping.get(c)]
        if expected_comp_routings and routing_pred not in expected_comp_routings and "OTHER" not in comp_preds:
             conflicts.append(f"Complaints {comp_preds} imply one of {expected_comp_routings}, but routing chose '{routing_pred}'.")
            
        if sev_pred == "CRITICAL" and routing_pred == "GENERAL_SUPPORT":
            conflicts.append("Severity is CRITICAL, but incident routed to GENERAL_SUPPORT.")
            
        if cat_pred == "FIRE" and sev_pred in ["LOW", "MEDIUM"]:
            conflicts.append("Classification is FIRE, which usually requires HIGH/CRITICAL severity, but got LOW/MEDIUM.")
            
        return conflicts

    async def process_incident(self, text: str, lat: float = None, lon: float = None, area_name: str = None) -> Dict[str, Any]:
        """
        Runs the negotiation loop across all agents.
        """
        combined_result = {"original_text": text}
        incident_id = str(uuid.uuid4())
        
        # Extract/Validate Location
        location_data = self.geo_tagger.extract_location(text, lat, lon, area_name)
        
        # 0. Fetch Dynamic Policy
        policy = self.policy_engine.get_current_policy()
        combined_result["applied_policy"] = policy
        
        # 0. Retrieve FAISS context
        retriever_result = self.retriever.get_context(text, top_k=3)
        similar_incidents = retriever_result.get("similar_cases", [])
        
        # STEP 1: INDEPENDENT PREDICTIONS
        cat_res = await self.classification_agent.process(text, similar_incidents)
        sev_res = await self.severity_agent.process(text, similar_incidents)
        routing_res = await self.routing_agent.process(text, similar_incidents)
        comp_res = await self.complaint_agent.process(text, similar_incidents)
        
        # STRICT RAG OVERRIDE (Complaint specific)
        if len(similar_incidents) >= 3:
            all_mem_cats = []
            for c in similar_incidents[:3]:
                cats = c.get("metadata", {}).get("complaint_categories", [])
                all_mem_cats.extend(cats)
                
            from collections import Counter
            counts = Counter(all_mem_cats)
            overlapping = [cat for cat, count in counts.items() if count >= 3]
            
            if overlapping:
                logger.info(f"RAG OVERRIDE: Overlapping past complaints found for {overlapping}. Forcing Complaint classification.")
                comp_res["prediction"] = overlapping
                comp_res["confidence"] = 1.0
                comp_res["reason"] = f"Unconditional RAG Override: Top 3 historical matches all share categories: {overlapping}."
        
        # STEP 2 & 3: CROSS-CHECK AND NEGOTIATION LOOP
        max_iterations = 2
        iteration = 0
        conflicts = self._detect_conflicts(cat_res["prediction"], sev_res["prediction"], routing_res["prediction"], comp_res["prediction"])
        resolution_strategy = "independent_consensus"
        
        while conflicts and iteration < max_iterations:
            logger.info(f"Iteration {iteration+1}: Conflicts detected: {conflicts}")
            peer_preds = {
                "classification": cat_res,
                "severity": sev_res,
                "routing": routing_res,
                "complaint": comp_res
            }
            
            # Re-evaluate
            new_cat = await self.classification_agent.re_evaluate(text, similar_incidents, conflicts, peer_preds)
            new_sev = await self.severity_agent.re_evaluate(text, similar_incidents, conflicts, peer_preds)
            new_routing = await self.routing_agent.re_evaluate(text, similar_incidents, conflicts, peer_preds)
            new_comp = await self.complaint_agent.re_evaluate(text, similar_incidents, conflicts, peer_preds)
            
            cat_res, sev_res, routing_res, comp_res = new_cat, new_sev, new_routing, new_comp
            conflicts = self._detect_conflicts(cat_res["prediction"], sev_res["prediction"], routing_res["prediction"], comp_res["prediction"])
            resolution_strategy = "negotiation_consensus"
            iteration += 1

        # STEP 4: FINAL DECISION LOGIC
        if conflicts:
            resolution_strategy = "forced_resolution_highest_confidence"
            logger.warning("Failed to reach consensus after 2 iterations. Forcing resolution.")
            if routing_res["prediction"] == "GENERAL_SUPPORT" and sev_res["prediction"] == "CRITICAL":
                routing_res["prediction"] = "ESCALATED_SUPPORT"
                routing_res["reason"] = "Forced override due to CRITICAL severity."
        
        # STEP 5: OUTPUT
        final_decision = {
            "incident_id": incident_id,
            "incident_type": cat_res["prediction"],
            "complaint_categories": comp_res["prediction"],
            "severity_level": sev_res["prediction"],
            "assigned_team": routing_res["prediction"],
            "priority": "EXPEDITED" if sev_res["prediction"] in ["HIGH", "CRITICAL"] else "NORMAL",
            "requires_human_review": len(conflicts) > 0 or sev_res["prediction"] == "CRITICAL",
            "location": location_data
        }
        
        # ASYNC EXECUTION
        await self.async_queue.dispatch(final_decision)
        
        combined_result["final_decision"] = final_decision
        combined_result["agents"] = {
            "classification": cat_res,
            "severity": sev_res,
            "routing": routing_res,
            "complaint": comp_res
        }
        combined_result["conflicts"] = conflicts
        combined_result["resolution_strategy"] = resolution_strategy
        
        # SELF-LEARNING FAISS STORAGE (using dynamic policy threshold)
        confidence_avg = (cat_res["confidence"] + sev_res["confidence"] + routing_res["confidence"] + comp_res["confidence"]) / 4.0
        store_threshold = policy["confidence_storage_threshold"]
        
        if confidence_avg > store_threshold and not conflicts:
            dup_sim_thresh = policy["rag_override_similarity"]
            is_dup = any(1.0 / (1.0 + c.get("distance", 1.0)) > dup_sim_thresh for c in similar_incidents)
            if not is_dup:
                mem_meta = final_decision.copy()
                mem_meta.update({
                    "source": "negotiation_consensus",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "confidence": confidence_avg
                })
                self.memory.add_memory(text=text, metadata=mem_meta)
                logger.info(f"Self-Learning: Stored high-confidence ({confidence_avg:.2f}) prediction to memory.")
            else:
                logger.info(f"Self-Learning: Skipped duplicate storage (Sim > {dup_sim_thresh:.2f})")
        else:
            logger.info(f"Self-Learning: Skipped storage (Conf {confidence_avg:.2f} <= {store_threshold:.2f} or Conflicts remain)")

        return combined_result
        
    def analyze_hotspots(self) -> List[Dict[str, Any]]:
        """
        Exposes the clustering engine to generate a list of current hotspots based on FAISS metadata.
        """
        records = self.memory.get_all_metadata()
        return self.cluster_engine.analyze_hotspots(records)
