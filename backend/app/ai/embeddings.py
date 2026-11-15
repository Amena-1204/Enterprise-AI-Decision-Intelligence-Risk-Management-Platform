import os
from typing import List, Optional

import numpy as np

from backend.app.utils.logger import app_logger

_openai_client = None
_local_model = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                _openai_client = OpenAI(api_key=api_key)
        except ImportError:
            pass
    return _openai_client


def _get_local_model():
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer("all-MiniLM-L6-v2")
            app_logger.info("Loaded local sentence-transformer model")
        except ImportError:
            app_logger.warning("sentence-transformers not installed; embeddings unavailable")
    return _local_model


def embed_texts(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Return embeddings for a list of texts. Tries OpenAI first, then local model."""
    if not texts:
        return []

    client = _get_openai_client()
    if client:
        try:
            embedding_model = model or os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
            response = client.embeddings.create(input=texts, model=embedding_model)
            return [item.embedding for item in response.data]
        except Exception as e:
            app_logger.warning("OpenAI embedding failed: %s — falling back to local", e)

    local = _get_local_model()
    if local:
        vectors = local.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

    # Last resort: zero vectors (allows system to run without embeddings)
    app_logger.error("No embedding backend available; returning zero vectors")
    return [[0.0] * 384 for _ in texts]


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
