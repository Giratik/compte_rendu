"""
plugins/APIclient.py
────────────────
Wrapper HTTP vers l'API FastAPI RAG.
Chaque fonction reproduit la signature attendue par les modules ui/
afin de rester un drop-in replacement des appels directs à backend.py.
"""

from __future__ import annotations
import re

import requests
from typing import Generator, List, Dict, Any, Optional

# ── URL de base (peut être surchargée via st.secrets ou variable d'env) ───────
import os
BASE_URL = os.getenv("API_URL", os.getenv("RAG_API_URL", "http://localhost:8000"))


# ─── helpers ──────────────────────────────────────────────────────────────────
 
def _get(path: str, **kwargs) -> Any:
    resp = requests.get(f"{BASE_URL}{path}", **kwargs)
    resp.raise_for_status()
    return resp.json()
 

 
# ─── Collections & modèles ────────────────────────────────────────────────────
 
def list_collections() -> List[str]:
    return _get("/rag/collections")["collections"]
 

def list_doc_dates(collection_name: str) -> List[str]:
    try:
        return _get(f"/rag/collections/{collection_name}/dates")
    except Exception:
        return []
