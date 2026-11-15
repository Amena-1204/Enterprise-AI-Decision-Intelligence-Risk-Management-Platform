import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.utils.logger import app_logger

_INDEX_FILE = "faiss.index"
_META_FILE = "metadata.json"


class VectorStore:
    """Simple FAISS-backed vector store with JSON metadata."""

    def __init__(self, store_dir: str):
        self.store_dir = store_dir
        os.makedirs(store_dir, exist_ok=True)
        self._index = None
        self._metadata: List[Dict[str, Any]] = []
        self._dim: Optional[int] = None
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        meta_path = os.path.join(self.store_dir, _META_FILE)
        index_path = os.path.join(self.store_dir, _INDEX_FILE)
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        if os.path.exists(index_path) and self._metadata:
            try:
                import faiss
                self._index = faiss.read_index(index_path)
                self._dim = self._index.d
                app_logger.info("Vector store loaded: %d vectors", self._index.ntotal)
            except ImportError:
                app_logger.warning("faiss not installed; vector store will use numpy fallback")
            except Exception as e:
                app_logger.error("Failed to load FAISS index: %s", e)

    def _save(self) -> None:
        meta_path = os.path.join(self.store_dir, _META_FILE)
        index_path = os.path.join(self.store_dir, _INDEX_FILE)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f)
        if self._index is not None:
            try:
                import faiss
                faiss.write_index(self._index, index_path)
            except Exception as e:
                app_logger.error("Failed to save FAISS index: %s", e)

    # ── Add vectors ───────────────────────────────────────────────────────────

    def add(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        if not vectors:
            return
        arr = np.array(vectors, dtype=np.float32)
        dim = arr.shape[1]

        try:
            import faiss
            if self._index is None:
                self._index = faiss.IndexFlatL2(dim)
                self._dim = dim
            self._index.add(arr)
        except ImportError:
            # Numpy fallback: store raw vectors in metadata
            for i, meta in enumerate(metadata):
                meta["_vector"] = vectors[i]

        self._metadata.extend(metadata)
        self._save()
        app_logger.info("Added %d vectors to store", len(vectors))

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self._metadata:
            return []

        q = np.array([query_vector], dtype=np.float32)

        try:
            import faiss
            if self._index is not None and self._index.ntotal > 0:
                k = min(top_k, self._index.ntotal)
                distances, indices = self._index.search(q, k)
                results = []
                for dist, idx in zip(distances[0], indices[0]):
                    if idx < len(self._metadata):
                        results.append((self._metadata[idx], float(dist)))
                return results
        except ImportError:
            pass

        # Numpy cosine similarity fallback
        results = []
        for meta in self._metadata:
            vec = meta.get("_vector")
            if vec:
                sim = float(np.dot(query_vector, vec) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(vec) + 1e-9
                ))
                results.append((meta, 1 - sim))  # convert to distance
        results.sort(key=lambda x: x[1])
        return results[:top_k]

    def count(self) -> int:
        return len(self._metadata)

    def clear(self) -> None:
        self._index = None
        self._metadata = []
        self._save()
