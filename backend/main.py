from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import subprocess
import torch
import gc
import whisperx
import io
import json
import traceback
import httpx

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434" )

# Import de tes fonctions locales existantes
from transcript_summarize import summarize_chunk, synthesize_summaries, creation_template_from_file
from conversion_output import generer_docx
from email_utils import envoyer_email_notification
#from ollama_client import inferring_ollama

app = FastAPI(title="API Transcription & Résumé")

# --- MODÈLES DE DONNÉES (Pour valider les requêtes JSON) ---
class ChunkRequest(BaseModel):
    chunk: str
    chunk_index: int
    total_chunks: int
    temperature: float
    model_name: str
    passes: int

class SynthesizeRequest(BaseModel):
    combined_notes: str
    prompt_cr: Optional[str] = None
    format_cr: Optional[str] = None
    temperature: float
    model_name: str
    num_ctx: int
    email_destinataire: Optional[str] = None

#pas implémenté
class DocxRequest(BaseModel):
    markdown_text: str


@app.get("/ressources/files")
async def get_templates():
    chemin_fichier = 'ressources/templates_reunions.json'
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            donnees = json.load(f)
            return donnees['templates']
    except FileNotFoundError:
        # C'est la bonne façon de remonter une erreur 404 à Streamlit
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    

@app.get("/models/loaded")
async def get_loaded_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{OLLAMA_URL}/api/ps", timeout=5)
        response.raise_for_status()
        return response.json().get("models", [])


@app.post("/models/unload")
async def unload_model(model_name: str):
    """Force le déchargement d'un modèle."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model_name, "keep_alive": 0},
            timeout=5
        )
        response.raise_for_status()
        return {"message": f"Modèle {model_name} déchargé."}


# --- 1. ENDPOINT DE TRANSCRIPTION ---
@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...), model_choice: str = Form("large-v3"), email_destinataire: str = Form(None)):
    file_extension = os.path.splitext(file.filename)[1].lower()

    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(await file.read())
        tmp_input_path = tmp_file.name

    audio_path_to_process = tmp_input_path

    try:
        # Nettoyage FFmpeg
        tmp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio_path_to_process = tmp_audio_file.name
        tmp_audio_file.close() 

        command = [
            "ffmpeg", "-i", tmp_input_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y",
            audio_path_to_process
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        device = "cuda" 
        batch_size = 16 
        compute_type = "float16" 
        asr_options = {"beam_size": 5, "condition_on_previous_text": False, "compression_ratio_threshold": 2.4}

        # Transcription
        model_name = "large-v3" if model_choice == "large-v3" else model_choice
        model = whisperx.load_model(model_name, device, compute_type=compute_type, asr_options=asr_options)
        audio = whisperx.load_audio(audio_path_to_process)
        result = model.transcribe(audio, batch_size=batch_size, language="fr")
        
        del model
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()

        # Alignement
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        del model_a
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()

        full_text = " ".join([segment.get("text", "").strip() for segment in result["segments"]])

        if email_destinataire:
            envoyer_email_notification(
                destinataire=email_destinataire,
                sujet="🎙️ Votre transcription est terminée !",
                message="Le serveur a terminé de transcrire votre fichier audio. Vous pouvez retourner sur l'application pour lancer le résumé."
            )
        return {"transcript": full_text}

    except Exception as e:
        print("ERREUR CRITIQUE DANS LA TRANSCRIPTION :")
        traceback.print_exc()  # Force l'affichage de l'erreur dans les logs Docker
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_input_path): os.remove(tmp_input_path)
        if audio_path_to_process != tmp_input_path and os.path.exists(audio_path_to_process): os.remove(audio_path_to_process)

# --- 2. ENDPOINTS OLLAMA ---
@app.post("/summarize_chunk/")
async def api_summarize_chunk(req: ChunkRequest):
    try:
        resume = summarize_chunk(
            req.chunk, req.chunk_index, req.total_chunks, 
            req.temperature, req.model_name, passes=req.passes
        )
        return {"summary": resume}
    except Exception as e:
        print(f"ERREUR CRITIQUE CAPTURÉE : {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/synthesize/")
async def api_synthesize(req: SynthesizeRequest):
    try:
        final_summary = synthesize_summaries(
            req.combined_notes, prompt_cr=req.prompt_cr, format_cr=req.format_cr,
            temperature=req.temperature, model_name=req.model_name, num_ctx=req.num_ctx
        )

        if req.email_destinataire:
            envoyer_email_notification(
                destinataire=req.email_destinataire,
                sujet="✍️ Votre compte-rendu est prêt !",
                message="L'IA a terminé la rédaction de votre compte-rendu de réunion. Vous pouvez le télécharger au format Word sur l'application."
            )
        return {"final_summary": final_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_template/")
async def api_create_template(file: UploadFile = File(...), chosen_model: str = Form(...)):
    try:
        # Note : Il faudra peut-être adapter ta fonction creation_template_from_file 
        # pour qu'elle accepte des bytes ou un chemin de fichier au lieu d'un objet st.file_uploader
        file_bytes = await file.read()
        template = creation_template_from_file(file_bytes, chosen_model)
        return {"template": template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. ENDPOINT DOCX ---
@app.post("/generate_docx/")
async def api_generate_docx(req: DocxRequest):
    try:
        docx_io = generer_docx(req.markdown_text)
        return Response(
            content=docx_io.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


