import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from typing import Optional
from transcript_summarize import summarize_chunk, synthesize_summaries

router_summarize = APIRouter(prefix="/summarize_chunk", tags=["summarize_chunk"])
router_synthesize = APIRouter(prefix="/synthesize", tags=["synthesize"])

DEBUG_LOG_TOGGLE = os.environ.get("DEBUG_LOG_TOGGLE", "OFF")

# Structure attendue pour la requête POST
class ChunkRequest(BaseModel):
    chunk: str
    chunk_index: int
    total_chunks: int
    temperature: float
    model_name: str
    num_ctx: int
    passes: int


class SynthesizeRequest(BaseModel):
    combined_notes: str
    prompt_cr: Optional[str] = None
    format_cr: Optional[str] = None
    temperature: float
    model_name: str
    num_ctx: int



@router_summarize.post("/")
async def api_summarize_chunk(req: ChunkRequest):
    try:
        resume = summarize_chunk(
            chunk=req.chunk,
            chunk_index=req.chunk_index,
            total_chunks=req.total_chunks,
            temperature=req.temperature,
            model_name=req.model_name,
            num_ctx=req.num_ctx,
            passes=req.passes
        )
        return {"summary": resume}
    except Exception as e:
        print(f"ERREUR CRITIQUE CAPTURÉE : {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    


@router_synthesize.post("/")
async def api_synthesize(req: SynthesizeRequest):
    if DEBUG_LOG_TOGGLE == "ON":
        print("before try")
    try:
        if DEBUG_LOG_TOGGLE == "ON":
            print("entered try")
        final_summary = synthesize_summaries(
        combined_text=req.combined_notes,
        prompt_cr=req.prompt_cr,
        format_cr=req.format_cr,
        temperature=req.temperature,
        model_name=req.model_name,
        num_ctx=req.num_ctx,
)
        if DEBUG_LOG_TOGGLE == "ON":
            print("after function")

        return {"final_summary": final_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))