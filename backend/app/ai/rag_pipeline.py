import os
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.app.ai.embeddings import embed_query, embed_texts
from backend.app.ai.vector_store import VectorStore
from backend.app.utils.logger import app_logger

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _get_store(store_dir: Optional[str] = None) -> VectorStore:
    if store_dir is None:
        store_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "ml", "data", "vector_store"
        )
    return VectorStore(store_dir)


# ── Document loading ──────────────────────────────────────────────────────────

def load_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_pdf(path: str) -> str:
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except ImportError:
        app_logger.warning("pdfplumber not installed; cannot parse PDF: %s", path)
        return ""


def load_docx(path: str) -> str:
    try:
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        app_logger.warning("python-docx not installed; cannot parse DOCX: %s", path)
        return ""


def load_document(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return load_pdf(path)
    if ext in (".docx", ".doc"):
        return load_docx(path)
    return load_text_file(path)


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 20]


# ── Indexing ──────────────────────────────────────────────────────────────────

def index_document(
    file_path: str,
    category: str = "general",
    store_dir: Optional[str] = None,
) -> int:
    """Load, chunk, embed and store a document. Returns number of chunks indexed."""
    text = load_document(file_path)
    if not text.strip():
        app_logger.warning("Empty document: %s", file_path)
        return 0

    chunks = chunk_text(text)
    vectors = embed_texts(chunks)
    filename = os.path.basename(file_path)

    metadata = [
        {
            "text": chunk,
            "source": filename,
            "file_path": file_path,
            "category": category,
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]

    store = _get_store(store_dir)
    store.add(vectors, metadata)
    app_logger.info("Indexed %d chunks from %s", len(chunks), filename)
    return len(chunks)


def index_directory(
    directory: str,
    category: str = "general",
    store_dir: Optional[str] = None,
) -> Dict[str, int]:
    """Index all supported documents in a directory."""
    results = {}
    supported = {".txt", ".pdf", ".docx", ".doc", ".md"}
    for fname in os.listdir(directory):
        if os.path.splitext(fname)[1].lower() in supported:
            path = os.path.join(directory, fname)
            count = index_document(path, category=category, store_dir=store_dir)
            results[fname] = count
    return results


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    top_k: int = 5,
    store_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve the most relevant document chunks for a query."""
    store = _get_store(store_dir)
    if store.count() == 0:
        return []

    q_vec = embed_query(query)
    results = store.search(q_vec, top_k=top_k)
    return [
        {
            "text": meta["text"],
            "source": meta.get("source", "unknown"),
            "category": meta.get("category", ""),
            "score": round(1 / (1 + dist), 4),  # convert distance to similarity score
        }
        for meta, dist in results
    ]
