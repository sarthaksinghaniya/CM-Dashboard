from typing import Dict, Any, List
import logging
from collections import Counter
from .base_agent import BaseAgent
from app.services.ml.inference import MLInferenceService

logger = logging.getLogger(__name__)

class IntelligentAgent(BaseAgent):
    """
    Hybrid Intelligent Crisis Management AI Agent.
    Mathematically blends Fine-Tuned ML predictions with RAG FAISS Memory precedents.
    """
    
    def __init__(self):
        super().__init__()
        self.inference_service = MLInferenceService()

    def _analyze_memory(self, context: List[Dict[str, Any]]):
        """Analyzes RAG context to compute agreement scores and most common properties."""
        if not context:
            return {"agreement_score": 0.0, "max_similarity": 0.0, "common_cat": None, "common_sev": None, "common_dept": None}
            
        categories = [c.get("incident_type") or c.get("category") for c in context]
        severities = [c.get("severity_level") or c.get("severity") for c in context]
        departments = [c.get("assigned_team") or c.get("department") for c in context]
        
        # Distance to Similarity conversion (FAISS L2 distance -> Similarity heuristic)
        # Assuming lower distance = higher similarity. Let's invert it roughly: 1.0 / (1.0 + distance)
        distances = [c.get("distance", 1.0) for c in context]
        similarities = [1.0 / (1.0 + d) for d in distances]
        max_similarity = max(similarities) if similarities else 0.0
        
        cat_counts = Counter(categories)
        sev_counts = Counter(severities)
        dept_counts = Counter(departments)
        
        common_cat, cat_freq = cat_counts.most_common(1)[0] if categories else (None, 0)
        common_sev = sev_counts.most_common(1)[0][0] if severities else None
        common_dept = dept_counts.most_common(1)[0][0] if departments else None
        
        agreement_score = cat_freq / len(context) if context else 0.0
        
        return {
            "agreement_score": agreement_score,
            "max_similarity": max_similarity,
            "common_cat": common_cat,
            "common_sev": common_sev,
            "common_dept": common_dept
        }

    async def process(self, text: str, context: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Executes the Hybrid RAG + Fine-Tuned Model Pipeline.
        """
        # STEP 1: MODEL PREDICTION
        model_pred = self.inference_service.predict(text)
        cat_pred = model_pred.get("category_pred", "OTHER")
        sev_pred = model_pred.get("severity_pred", "LOW")
        confidence = model_pred.get("confidence_score", 0.5)
        
        # Default Department mapping if not from memory
        dept_mapping = {"FIRE": "FIRE_DEPARTMENT", "MEDICAL": "EMS", "POLICE": "LAW_ENFORCEMENT"}
        dept_pred = dept_mapping.get(cat_pred, "GENERAL_SUPPORT")
        
        if not context:
            # No memory -> strictly use model
            return {
                "category": cat_pred,
                "severity": sev_pred,
                "department": dept_pred,
                "confidence": confidence,
                "source": "model",
                "reason": "Decision derived strictly from fine-tuned model (no historical context found)."
            }

        # STEP 2: MEMORY ANALYSIS
        mem_analysis = self._analyze_memory(context)
        agreement = mem_analysis["agreement_score"]
        sim = mem_analysis["max_similarity"]
        mem_cat = mem_analysis["common_cat"]
        mem_sev = mem_analysis["common_sev"]
        mem_dept = mem_analysis["common_dept"]

        # STEP 3 & 4: HYBRID DECISION LOGIC & CONFIDENCE RE-SCALING
        final_cat = cat_pred
        final_sev = sev_pred
        final_dept = dept_pred
        source = "model"
        reason = ""

        if agreement > 0.7 and sim > 0.8:
            # Override model prediction with memory decision
            final_cat = mem_cat or cat_pred
            final_sev = mem_sev or sev_pred
            final_dept = mem_dept or dept_pred
            source = "memory"
            
            if final_cat == cat_pred:
                confidence = min(1.0, confidence + 0.1) # Boost
            else:
                confidence = max(0.1, confidence - 0.15) # Reduce
                
            reason = f"Memory override triggered (Agreement: {agreement:.2f}, Sim: {sim:.2f}). Highly consistent past precedents matched."
            
        elif 0.4 <= agreement <= 0.7:
            # Blend: We'll adopt the memory category if model confidence is low, else keep model
            if confidence < 0.6 and mem_cat:
                final_cat = mem_cat
                final_sev = mem_sev or sev_pred
                final_dept = mem_dept or dept_pred
                source = "hybrid"
                reason = "Weighted hybrid blend applied. Model confidence was low, shifted towards historical precedent."
            else:
                source = "hybrid"
                if final_cat == mem_cat:
                    confidence = min(1.0, confidence + 0.05)
                else:
                    confidence = max(0.1, confidence - 0.05)
                reason = "Hybrid blend applied. Model prediction remained dominant despite moderate historical disagreement."
                
        else:
            # Use model prediction
            if final_cat == mem_cat:
                confidence = min(1.0, confidence + 0.05)
            else:
                confidence = max(0.1, confidence - 0.1)
            reason = "Model prediction utilized. Historical precedents were too scattered or weak to influence."

        # STEP 5: OUTPUT
        return {
            "category": final_cat,
            "severity": final_sev,
            "department": final_dept,
            "confidence": round(confidence, 3),
            "source": source,
            "reason": reason
        }
