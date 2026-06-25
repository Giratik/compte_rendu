#backend/routers/chunk_summary.py

from fastapi import APIRouter
from pydantic import BaseModel
from minutes_redactor_tools.functions_folder.chunk_analysis import (
    remove_timestamps,
    split_into_chunks,
    summarize_chunk,
    extract_comparisons,
    generate_global_summary,
    generate_global_summary_with_comparisons,
)

from typing import Optional

# ── Request Models ─────────────────────────────────────────────────────────────

class ChunkSplitRequest(BaseModel):
    text: str
    chunk_size: int
    overlap: int = 50


class SummarizeChunkRequest(BaseModel):
    chunk: str
    model: str
    chunk_index: int
    total_chunks: int

    temperature: float
    model_name: str
    num_ctx: int
    passes: int

    custom_system_prompt: Optional[str] = None


class ExtractComparisonsRequest(BaseModel):
    chunks: list[str]
    model: str

    custom_system_prompt: Optional[str] = None


class GenerateGlobalSummaryRequest(BaseModel):
    summaries: list[str]
    model: str
    comparisons: str = ""

    custom_system_prompt: Optional[str] = None


# ── API Routers ────────────────────────────────────────────────────────────────

router_chunk_split = APIRouter(prefix="/split_into_chunks", tags=["chunk_splitting"])
router_summarize = APIRouter(prefix="/summarize_chunk", tags=["summarize_chunk"])
router_extract_comparisons = APIRouter(prefix="/extract_comparisons", tags=["extract_comparisons"])
router_generate_global_summary = APIRouter(prefix="/generate_global_summary", tags=["generate_global_summary"])


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router_chunk_split.post("/")
async def api_split_into_chunks(request: ChunkSplitRequest):
    """Split text into word-based chunks with optional overlap."""
    # Pas d'appel Ollama ici, pas besoin d'await — reste synchrone, c'est correct
    return split_into_chunks(request.text, request.chunk_size, request.overlap)


@router_summarize.post("/")
async def api_summarize_chunk(request: SummarizeChunkRequest) -> str:
    """Summarize a single transcript chunk as live meeting notes."""
    return await summarize_chunk(request.chunk, request.model, request.chunk_index, request.total_chunks)


@router_extract_comparisons.post("/")
async def api_extract_comparisons(request: ExtractComparisonsRequest) -> str:
    """
    Scan all raw chunks for tool/product comparisons (price, efficiency, etc.).
    Returns a structured extraction, or empty string if nothing found.
    """
    return await extract_comparisons(request.chunks, request.model)


@router_generate_global_summary.post("/")
async def api_generate_global_summary(request: GenerateGlobalSummaryRequest) -> str:
    """
    Generate a global meeting summary from chunk summaries.
    If comparisons is non-empty, a dedicated section is appended with raw figures preserved.
    """
    if request.comparisons:
        return await generate_global_summary_with_comparisons(request.summaries, request.comparisons, request.model)
    return await generate_global_summary(request.summaries, request.model)