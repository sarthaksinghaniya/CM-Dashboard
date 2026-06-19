from typing import Dict, Any, List
import logging
import numpy as np
from .model_loader import ModelLoader
from app.ml.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class MLInferenceService:
    """
    Service layer providing inference functionality using fine-tuned models.
    """
    def __init__(self):
        self.loader = ModelLoader()
        self.loader.load_models()
        self.embedder = EmbeddingService()
        
    def get_embeddings(self, text: str) -> List[float]:
        """
        Generates BERT embeddings for the given text.
        """
        try:
            # We use the embedding service which handles SentenceTransformer
            # It expects a list of strings, so we wrap it
            embeddings_matrix = self.embedder.generate_embeddings([text])
            return embeddings_matrix[0].tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
        
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Runs the main classifier and severity inference on the provided text.
        Returns predicted category, severity, and confidence scores.
        """
        try:
            embeddings = self.get_embeddings(text)
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
                
            X_input = np.array([embeddings])
            
            classifier = self.loader.get_classifier()
            severity_model = self.loader.get_severity_model()
            encoders = self.loader.get_encoders()
            
            if not classifier or not encoders:
                logger.warning("Models not fully loaded. Returning fallback predictions.")
                return self._fallback_predict()

            # Predict Category
            cat_probs = classifier.predict_proba(X_input)[0]
            cat_idx = np.argmax(cat_probs)
            cat_pred = encoders['category'].inverse_transform([cat_idx])[0]
            cat_conf = float(cat_probs[cat_idx])
            
            # Predict Severity
            sev_probs = severity_model.predict_proba(X_input)[0]
            sev_idx = np.argmax(sev_probs)
            sev_pred = encoders['severity'].inverse_transform([sev_idx])[0]
            sev_conf = float(sev_probs[sev_idx])
            
            # Average confidence
            confidence = (cat_conf + sev_conf) / 2.0
            
            return {
                "category_pred": cat_pred.upper(),
                "severity_pred": sev_pred.upper(),
                "confidence_score": confidence
            }
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return self._fallback_predict()
            
    def _fallback_predict(self) -> Dict[str, Any]:
        return {
            "category_pred": "OTHER",
            "severity_pred": "LOW",
            "confidence_score": 0.5
        }
