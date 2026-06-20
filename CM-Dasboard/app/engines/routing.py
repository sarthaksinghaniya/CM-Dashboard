import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import PriorityEnum
from app.services.ml.inference import MLInferenceService
from app.services.memory.retriever import ContextRetriever
from app.engines.faiss_rag import FaissMemory
from app.services.agents.decision_agent import DecisionAgent
from app.engines.assignment import AssignmentEngine

logger = logging.getLogger("cm_dashboard.engines.routing")

class RoutingEngine:
    """
    Core engine responsible for NLP-driven Auto Routing of complaints.
    Integrates with FAISS RAG to leverage historical intelligence.
    """

    @staticmethod
    def get_department(category: str) -> str:
        cat = category.strip().upper()
        if not cat or cat == "OTHER":
            return "GENERAL_DEPT"
        
        category_map = {
            "ROAD": "PWD",
            "ELECTRICITY": "DISCOM",
            "WATER": "DJB",
            "HEALTH": "HEALTH",
            "WOMEN SAFETY": "POLICE",
            "SANITATION": "MCD"
        }
        
        if cat in category_map:
            return category_map[cat]
            
        if cat.endswith("_DEPT"):
            return cat
        return f"{cat}_DEPT"

    @staticmethod
    async def process_routing(text: str, district: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Executes the AI routing pipeline for a complaint.
        Returns a dict containing assigned_officer, department, category, and priority.
        """
        logger.info(f"[ROUTING_ENGINE] Processing NLP Routing for text snippet...")

        # Initialize AI Subsystems
        classifier = MLInferenceService()
        rag = ContextRetriever()
        memory = FaissMemory()
        agent = DecisionAgent()

        # 1. NLP Classification & Severity Scoring
        import asyncio
        classification_res = await asyncio.to_thread(classifier.predict, text)
        labels = classification_res.get("category_pred", ["OTHER"])
        confidence = classification_res.get("confidence_score", 0.5)
        
        pred_priority_str = await asyncio.to_thread(classifier.predict_severity, text)
        
        priority = PriorityEnum[pred_priority_str]
        category = labels[0] if labels else "OTHER"
        department = RoutingEngine.get_department(category)
        
        # 2. RAG Intelligence Lookup
        rag_res = await asyncio.to_thread(rag.get_context, text)
        similar_cases = rag_res.get("similar_cases", [])
        
        # 3. Agentic Verification
        decision_res = await agent.process(text, context=similar_cases, ml_predictions=labels)
        logger.info(f"[ROUTING_ENGINE] Decision Agent Resolution: {decision_res.get('decision')}")

        # 4. Officer Assignment
        assigned_officer = None
        if confidence >= 0.6:  # Threshold for automated assignment
            assigned_officer = await AssignmentEngine.assign_officer(department, district, session)

        # 5. Persistent ML Signal Memory
        metadata = {
            "decision": decision_res.get("decision"),
            "labels": labels,
            "department": department,
            "priority": pred_priority_str,
            "assigned_to": assigned_officer
        }
        await asyncio.to_thread(memory.add_memory, text, metadata)

        return {
            "assigned_to": assigned_officer,
            "department": department,
            "category": category,
            "priority": priority,
            "decision": decision_res.get("decision"),
            "confidence": confidence
        }
