import os
import tempfile
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from transcription_tools.utility_functions.whisperx_transcriber import transcribe_audio_with_whisperx, convert_audio_to_wav

# Création du routeur pour ce "plugin"
router = APIRouter(prefix="/transcribe", tags=["Transcription"])

@router.post("/")
async def transcribe_audio(
    file: UploadFile = File(...), 
    model_choice: str = Form("large-v3"), 
):
    file_extension = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(await file.read())
        tmp_input_path = tmp_file.name

    audio_path_to_process = None

    try:
        audio_path_to_process = convert_audio_to_wav(tmp_input_path)
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
        if os.path.exists(tmp_input_path):
            os.remove(tmp_input_path)
        if audio_path_to_process and os.path.exists(audio_path_to_process):
            os.remove(audio_path_to_process)