import os
import tempfile
import traceback
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from transcription_tools.utility_functions.whisperx_transcriber import transcribe_audio_with_whisperx, convert_audio_to_wav_async
from transcription_tools.utility_functions.transcription_queue import transcription_queue

# Création du routeur pour ce "plugin"
router = APIRouter(prefix="/transcribe", tags=["Transcription"])

@router.post("/")
async def transcribe_audio(
    file: UploadFile = File(...), 
    model_choice: str = Form("large-v3"), 
    queue_token: str = Form(None),
    session_id: str = Form(None),
):
    # Handle queue logic
    if not queue_token:
        # New request - add to queue
        # Generate session_id if not provided
        if not session_id:
            session_id = f"user_{hash(file.filename) % 10000}"
        position, queue_token = await transcription_queue.add_to_queue(session_id)
        return {
            "status": "queued",
            "position": position,
            "queue_token": queue_token,
            "message": f"Vous êtes en position {position} dans la file d'attente"
        }

    # Check if it's our turn
    can_proceed = await transcription_queue.acquire_transcription_slot(queue_token)
    if not can_proceed:
        # Check current position
        position = await transcription_queue.get_queue_position(queue_token)
        if position is None:
            return {"status": "error", "message": "Token de file d'attente invalide"}
        
        return {
            "status": "waiting",
            "position": position,
            "message": f"Veuillez patienter, vous êtes en position {position}"
        }

    # It's our turn - proceed with transcription
    file_extension = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(await file.read())
        tmp_input_path = tmp_file.name

    audio_path_to_process = None

    try:
        audio_path_to_process = await convert_audio_to_wav_async(tmp_input_path)
        full_text = await transcribe_audio_with_whisperx(
            audio_path=audio_path_to_process,
            model_choice=model_choice,
            device="cuda",
            batch_size=4,
            compute_type="int8_float16"
        )

        return {"transcript": full_text}

    except Exception as e:
        print("ERREUR CRITIQUE DANS LA TRANSCRIPTION :")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await transcription_queue.release_transcription_slot()
        if os.path.exists(tmp_input_path):
            os.remove(tmp_input_path)
        if audio_path_to_process and os.path.exists(audio_path_to_process):
            os.remove(audio_path_to_process)
