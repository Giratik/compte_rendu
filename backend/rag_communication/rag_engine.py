#backend/engines/rag_engine.py

"""
backend.py — Logique RAG : ChromaDB, Ollama, BM25, Hybrid Search
─────────────────────────────────────────────────────────────────
"""

import re
import chromadb
from chromadb.utils import embedding_functions

from .core import CHROMA_HOST, CHROMA_PORT, OLLAMA_HOST, EMBEDDING_MODEL
from typing import Any


# ─── CLIENTS ──────────────────────────────────────────────────────────────────

def make_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


def make_embedding_fn() -> embedding_functions.OllamaEmbeddingFunction:
    return embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_HOST + "/api/embeddings",
        model_name=EMBEDDING_MODEL,
    )


def get_collection(chroma_client: chromadb.HttpClient, collection_name: str):
    return chroma_client.get_collection(
        name=collection_name,
        embedding_function=make_embedding_fn(),
    )


def list_collections(chroma_client: chromadb.HttpClient) -> list[str]:
    raw = chroma_client.list_collections()
    return [c.name if hasattr(c, "name") else c for c in raw]


def list_doc_dates(collection) -> list[str]:
    result = collection.get(include=["metadatas"])
    dates = {
        meta.get("doc_date", "")
        for meta in (result.get("metadatas") or [])
        if meta and meta.get("doc_date")
    }
    return sorted(dates)


def list_generative_models(ollama_client: Any) -> list[str]:
    raw = ollama_client.list()
    models = raw.models if hasattr(raw, "models") else raw.get("models", [])
    result = []
    for m in models:
        name = m.model if hasattr(m, "model") else m.get("model", m.get("name", ""))
        if name and "embed" not in name:
            result.append(name)
    return result








