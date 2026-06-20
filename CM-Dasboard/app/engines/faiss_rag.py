import os
import json
import numpy as np
import faiss
import logging
import asyncio
from typing import List, Dict, Any
from app.services.memory.embedding import MemoryEmbeddingService
from threading import Lock

logger = logging.getLogger("cm_dashboard.engines.faiss_rag")

faiss_lock = Lock()

class FaissMemory:
    """
    Production-grade AI FAISS Memory & RAG Core.
    Features strict thread-safety, semantic deduplication, and async interfaces.
    """
    
    _instance = None
    
    def __new__(cls, embedding_dim: int = 384):
        if cls._instance is None:
            cls._instance = super(FaissMemory, cls).__new__(cls)
            cls._instance.embedding = MemoryEmbeddingService()
            cls._instance.embedding_dim = embedding_dim
            
            # Initialize FAISS IndexFlatL2
            cls._instance.index = faiss.IndexFlatL2(embedding_dim)
            cls._instance.metadata_store = {}
            cls._instance._current_id = 0
        return cls._instance

    def add_memory(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Synchronously generates embeddings and stores them safely in FAISS.
        Prevents duplicate semantic entries.
        """
        vec = self.embedding.embed(text).reshape(1, -1)
        
        with faiss_lock:
            # 1. Duplicate Prevention Check
            if self.index.ntotal > 0:
                distances, indices = self.index.search(vec, 1)
                if indices[0][0] != -1 and distances[0][0] < 0.01:
                    logger.info(f"Duplicate semantic embedding rejected [Distance: {distances[0][0]:.4f}].")
                    return False
            
            # 2. Insert and Map
            self.index.add(vec)
            self.metadata_store[self._current_id] = {
                "text": text,
                "deprecated": False,
                **(metadata or {})
            }
            self._current_id += 1
            return True

    def save_memory(self, index_path="memory.faiss", meta_path="meta.json"):
        """Safely serializes FAISS index and metadata to disk."""
        with faiss_lock:
            faiss.write_index(self.index, index_path)
            with open(meta_path, "w") as f:
                json.dump(self.metadata_store, f)
            logger.info(f"Saved FAISS memory to {index_path} and {meta_path}")

    def load_memory(self, index_path="memory.faiss", meta_path="meta.json"):
        """Safely deserializes FAISS index and metadata from disk."""
        with faiss_lock:
            if os.path.exists(index_path) and os.path.exists(meta_path):
                self.index = faiss.read_index(index_path)
                with open(meta_path, "r") as f:
                    store_str = json.load(f)
                    self.metadata_store = {int(k): v for k, v in store_str.items()}
                self._current_id = max(self.metadata_store.keys(), default=-1) + 1
                logger.info(f"Loaded FAISS memory from {index_path} and {meta_path}")
            else:
                logger.info("No existing FAISS memory found. Starting fresh.")
        
    def apply_rl_reward(self, text: str, reward: float, metadata: Dict[str, Any] = None):
        """
        Adjusts memory persistence based on RL reward.
        Thread-safe application of deprecation or boosting.
        """
        if reward <= -1.0:
            vec = self.embedding.embed(text).reshape(1, -1)
            with faiss_lock:
                if self.index.ntotal == 0:
                    return
                D, I = self.index.search(vec, 1)
                idx = int(I[0][0])
                if idx != -1 and idx in self.metadata_store:
                    self.metadata_store[idx]["deprecated"] = True
                    logger.info(f"RL Loop: Deprecated bad memory [ID: {idx}] due to negative reward.")
        elif reward >= 1.0:
            # We call add_memory directly, which handles its own internal lock and dup checking
            logger.info(f"RL Loop: Boosting high-reward memory.")
            self.add_memory(text, metadata)

    def search_similar(self, text: str, top_k: int = 5, distance_threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Thread-safe semantic similarity search. Filters out deprecated matches.
        """
        query_vec = self.embedding.embed(text).reshape(1, -1)
        
        with faiss_lock:
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
                            "metadata": meta
                        })
                if len(results) >= top_k:
                    break
            return results
        
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Thread-safe metadata retrieval."""
        with faiss_lock:
            return [meta for idx, meta in self.metadata_store.items() if not meta.get("deprecated", False)]

    # -------------------------------------------------------------------------
    # Async Wrappers for High-Concurrency Non-Blocking Execution
    # -------------------------------------------------------------------------
    
    async def async_add_memory(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        return await asyncio.to_thread(self.add_memory, text, metadata)
        
    async def async_search_similar(self, text: str, top_k: int = 5, distance_threshold: float = 1.5) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.search_similar, text, top_k, distance_threshold)
        
    async def async_apply_rl_reward(self, text: str, reward: float, metadata: Dict[str, Any] = None):
        await asyncio.to_thread(self.apply_rl_reward, text, reward, metadata)

# Dependency Injection Helper
def get_memory_service() -> FaissMemory:
    return FaissMemory()
