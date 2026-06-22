import os
import sys
import logging
import pickle
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger("cm_dashboard.services.memory.faiss")

class FaissMemory:
    """
    Hardened, Lazy-Loading Vector Storage Service.
    Safe for cross-platform deployment; prevents startup failures on environments 
    lacking native faiss wheels or binaries until an actual invocation is made.
    """
    def __init__(
        self, 
        index_path: str = "data/complaints_faiss.index", 
        metadata_path: str = "data/complaints_metadata.pkl"
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path

        self.embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)
        
        # Core storage variables initialized as None to delay import-time execution
        self._faiss_module = None
        self.index = None
        self.metadata_store = {}
        self._is_initialized = False

    def _lazy_init_faiss(self):
        """
        Dynamically imports FAISS and loads tracking indexes only when needed.
        Guarantees that missing system binaries will not prevent FastAPI from starting up.
        """
        if self._is_initialized:
            return

        try:
            # Lazy internal mapping import
            import faiss
            self._faiss_module = faiss
            logger.info("[FAISS_MEMORY] Successfully loaded native faiss library context dynamically.")
        except ImportError as err:
            logger.critical(
                "[FAISS_MEMORY] C++ Binary dependency 'faiss' is missing in this runtime environment. "
                "Vector-space storage operations are deactivated."
            )
            raise RuntimeError("CRITICAL: FAISS native library is unavailable in this container context.") from err

        # Secure folder paths
        os.makedirs(os.path.dirname(self.index_path) or '.', exist_ok=True)

        # Thread-safe dual storage index recovery structure
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = self._faiss_module.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata_store = pickle.load(f)
                logger.info(f"[FAISS_MEMORY] Recovered {self.index.ntotal} historical embedding coordinates securely.")
            except Exception as e:
                logger.error(f"[FAISS_MEMORY] Index recovery failed due to corruption ({str(e)}). Resetting mapping arrays.")
                self._initialize_empty_index()
        else:
            self._initialize_empty_index()

        self._is_initialized = True

    def _initialize_empty_index(self):

     dimension = 384

     self.index = self._faiss_module.IndexFlatIP(
        dimension
     )

     self.metadata_store = {}

     logger.info(
        "[FAISS_MEMORY] Empty index created."
    )

    def search_similar(
    self,
    query_text: str,
    top_k: int = 3
):

     try:
        self._lazy_init_faiss()
     except RuntimeError:
        return []

     if self.index.ntotal == 0:
        return []

     try:

        embedding = self.embedding_model.encode(
            [query_text],
            normalize_embeddings=True
        )

        embedding = np.array(
            embedding,
            dtype=np.float32
        )

        distances, indices = self.index.search(
            embedding,
            top_k
        )

        results = []

        for score, idx in zip(
            distances[0],
            indices[0]
        ):

            if idx == -1:
                continue

            metadata = self.metadata_store.get(
                idx,
                {}
            )

            results.append(
                {
                    "distance": float(score),
                    "metadata": metadata
                }
            )

        return results

     except Exception as exc:

        logger.exception(
            "FAISS search failed"
        )

        return []