"""FastAPI router exposing core RAG engine functionalities as HTTP endpoints.

Endpoints provided:
* GET  /rag/collections                      – list available ChromaDB collections
* GET  /rag/collections/{name}/dates         – list available doc_date values for a collection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from rag_communication.rag_engine import (
    make_chroma_client,
    list_collections,
    get_collection,
    list_doc_dates,
)

router = APIRouter(prefix="/rag", tags=["RAG Engine"])


@router.get("/collections")
def get_collections_endpoint():
    client = make_chroma_client()
    try:
        return {"collections": list_collections(client)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/dates")
def get_collection_dates_endpoint(collection_name: str):
    client = make_chroma_client()
    try:
        collection = get_collection(client, collection_name)
        return list_doc_dates(collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


