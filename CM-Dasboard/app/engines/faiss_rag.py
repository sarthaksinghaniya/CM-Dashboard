"""
FAISS RAG Memory Engine — thread-safe, crash-proof vector store.

Hardening:
  • Singleton with lazy init (won't crash on import if FAISS missing)
  • Thread-safe via Lock on all index mutations
  • Duplicate vector rejection via distance threshold
  • RL reward application with deprecation/boosting
  • All public methods wrapped in try/except — never crashes caller
  • Async wrappers for non-blocking usage in asyncio pipelines
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from threading import Lock

logger = logging.getLogger("cm_dashboard.engines.faiss_rag")

# Lazy imports — FAISS may not be installed in all environments
try:
    import numpy as np
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("[FAISS] faiss-cpu not installed — vector memory disabled.")

_faiss_lock = Lock()


class FaissMemory:
    """Production-grade FAISS Memory & RAG Core with thread-safety."""

    _instance: Optional["FaissMemory"] = None

    def __new__(cls, embedding_dim: int = 384):
        if cls._instance is None:
            inst = super(FaissMemory, cls).__new__(cls)
            inst.embedding_dim = embedding_dim
            inst._current_id = 0
            inst.metadata_store: Dict[int, Dict[str, Any]] = {}

            # Lazy-load embedding service
            try:
                from app.services.memory.embedding import MemoryEmbeddingService
                inst.embedding = MemoryEmbeddingService()
            except Exception as exc:
                logger.error(f"[FAISS] Embedding service init failed: {exc}")
                inst.embedding = None

            # Init FAISS index
            if FAISS_AVAILABLE:
                inst.index = faiss.IndexFlatL2(embedding_dim)
            else:
                inst.index = None

            cls._instance = inst
        return cls._instance

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add_memory(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a text embedding to FAISS. Returns False on duplicate or failure."""
        if not FAISS_AVAILABLE or self.index is None or self.embedding is None:
            logger.warning("[FAISS] Memory unavailable — skipping add.")
            return False

        try:
            vec = self.embedding.embed(text).reshape(1, -1)
        except Exception as exc:
            logger.error(f"[FAISS] Embedding generation failed: {exc}")
            return False

        with _faiss_lock:
            try:
                # Duplicate prevention
                if self.index.ntotal > 0:
                    distances, indices = self.index.search(vec, 1)
                    if indices[0][0] != -1 and distances[0][0] < 0.01:
                        logger.info(
                            f"Duplicate semantic embedding rejected "
                            f"[Distance: {distances[0][0]:.4f}]."
                        )
                        return False

                self.index.add(vec)
                self.metadata_store[self._current_id] = {
                    "text": text,
                    "deprecated": False,
                    **(metadata or {}),
                }
                self._current_id += 1
                return True
            except Exception as exc:
                logger.error(f"[FAISS] add_memory internal error: {exc}")
                return False

    def save_memory(
        self, index_path: str = "memory.faiss", meta_path: str = "meta.json"
    ):
        """Persist FAISS index + metadata to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return
        with _faiss_lock:
            try:
                faiss.write_index(self.index, index_path)
                with open(meta_path, "w") as f:
                    json.dump(self.metadata_store, f)
                logger.info(f"Saved FAISS memory to {index_path} and {meta_path}")
            except Exception as exc:
                logger.error(f"[FAISS] save_memory failed: {exc}")

    def load_memory(
        self, index_path: str = "memory.faiss", meta_path: str = "meta.json"
    ):
        """Load FAISS index + metadata from disk."""
        if not FAISS_AVAILABLE:
            return
        with _faiss_lock:
            try:
                if os.path.exists(index_path) and os.path.exists(meta_path):
                    self.index = faiss.read_index(index_path)
                    with open(meta_path, "r") as f:
                        raw = json.load(f)
                        self.metadata_store = {int(k): v for k, v in raw.items()}
                    self._current_id = max(self.metadata_store.keys(), default=-1) + 1
                    logger.info(
                        f"Loaded FAISS memory from {index_path} and {meta_path}"
                    )
                else:
                    logger.info("No existing FAISS memory found. Starting fresh.")
            except Exception as exc:
                logger.error(f"[FAISS] load_memory failed: {exc}")
                # Start fresh rather than crash
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata_store = {}
                self._current_id = 0

    def apply_rl_reward(
        self, text: str, reward: float, metadata: Dict[str, Any] = None
    ):
        """Apply RL signal: deprecate on negative reward, boost on positive."""
        if not FAISS_AVAILABLE or self.index is None or self.embedding is None:
            return

        try:
            if reward <= -1.0:
                vec = self.embedding.embed(text).reshape(1, -1)
                with _faiss_lock:
                    if self.index.ntotal == 0:
                        return
                    D, I = self.index.search(vec, 1)
                    idx = int(I[0][0])
                    if idx != -1 and idx in self.metadata_store:
                        self.metadata_store[idx]["deprecated"] = True
                        logger.info(
                            f"RL Loop: Deprecated bad memory [ID: {idx}] "
                            f"due to negative reward."
                        )
            elif reward >= 1.0:
                logger.info("RL Loop: Boosting high-reward memory.")
                self.add_memory(text, metadata)
        except Exception as exc:
            logger.error(f"[FAISS] apply_rl_reward error: {exc}")

    def search_similar(
        self,
        text: str,
        top_k: int = 5,
        distance_threshold: float = 1.5,
    ) -> List[Dict[str, Any]]:
        """Thread-safe semantic similarity search. Filters deprecated matches."""
        if not FAISS_AVAILABLE or self.index is None or self.embedding is None:
            return []

        try:
            query_vec = self.embedding.embed(text).reshape(1, -1)
        except Exception as exc:
            logger.error(f"[FAISS] search embedding failed: {exc}")
            return []

        with _faiss_lock:
            try:
                if self.index.ntotal == 0:
                    return []

                k = min(top_k * 2, self.index.ntotal)
                distances, indices = self.index.search(query_vec, k)

                results = []
                for dist, idx in zip(distances[0], indices[0]):
                    if idx != -1 and dist <= distance_threshold:
                        meta = self.metadata_store.get(int(idx), {})
                        if not meta.get("deprecated", False):
                            results.append({
                                "faiss_id": int(idx),
                                "distance": float(dist),
                                "metadata": meta,
                            })
                    if len(results) >= top_k:
                        break
                return results
            except Exception as exc:
                logger.error(f"[FAISS] search_similar error: {exc}")
                return []

    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Thread-safe metadata retrieval (non-deprecated only)."""
        with _faiss_lock:
            return [
                meta
                for meta in self.metadata_store.values()
                if not meta.get("deprecated", False)
            ]

    # ------------------------------------------------------------------
    # Async wrappers for non-blocking pipeline usage
    # ------------------------------------------------------------------

    async def async_add_memory(
        self, text: str, metadata: Dict[str, Any] = None
    ) -> bool:
        return await asyncio.to_thread(self.add_memory, text, metadata)

    async def async_search_similar(
        self, text: str, top_k: int = 5, distance_threshold: float = 1.5
    ) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(
            self.search_similar, text, top_k, distance_threshold
        )

    async def async_apply_rl_reward(
        self, text: str, reward: float, metadata: Dict[str, Any] = None
    ):
        await asyncio.to_thread(self.apply_rl_reward, text, reward, metadata)


# Dependency Injection Helper
def get_memory_service() -> FaissMemory:
    return FaissMemory()
