import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Handles generating dense vector embeddings from text using BERT-based models.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Converts a list of text strings into a numpy array of embeddings.
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        # show_progress_bar=True helps track progress for large datasets
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings
