
from minutes_redactor_tools.routers import chunks_summary
from transcription_tools.routers import transcription
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import os

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434" )
DEBUG_LOG_TOGGLE = os.environ.get("DEBUG_LOG_TOGGLE", "OFF")

# Import de tes fonctions locales existantes

from minutes_redactor_tools.functions_folder.conversion_output import generer_docx

app = FastAPI(title="API Transcription & Résumé")

app.include_router(transcription.router)

app.include_router(chunks_summary.router_chunk_split)
app.include_router(chunks_summary.router_summarize)
app.include_router(chunks_summary.router_generate_global_summary)

# --- MODÈLES DE DONNÉES (Pour valider les requêtes JSON) ---




#pas implémenté
class DocxRequest(BaseModel):
    markdown_text: str


#@app.get("/ressources/files")
#async def get_templates():
#    chemin_fichier = 'ressources/templates_reunions.json'
#    try:
#        with open(chemin_fichier, 'r', encoding='utf-8') as f:
#            donnees = json.load(f)
#            return donnees['templates']
#    except FileNotFoundError:
#        # C'est la bonne façon de remonter une erreur 404 à Streamlit
#        raise HTTPException(status_code=404, detail="Fichier introuvable")
    

#@app.get("/models/loaded")
#async def get_loaded_models():
#    async with httpx.AsyncClient() as client:
#        response = await client.get(f"{OLLAMA_URL}/api/ps", timeout=5)
#        response.raise_for_status()
#        return response.json().get("models", [])


#@app.post("/models/unload")
#async def unload_model(model_name: str):
#    """Force le déchargement d'un modèle."""
#    async with httpx.AsyncClient() as client:
#        response = await client.post(
#            f"{OLLAMA_URL}/api/generate",
#            json={"model": model_name, "keep_alive": 0},
#            timeout=5
#        )
#        response.raise_for_status()
#        return {"message": f"Modèle {model_name} déchargé."}


# --- 1. ENDPOINT DE TRANSCRIPTION ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "API Opérationnelle"}






#@app.post("/create_template/")
#async def api_create_template(file: UploadFile = File(...), chosen_model: str = Form(...)):
#    try:
#        # Note : Il faudra peut-être adapter ta fonction creation_template_from_file 
#        # pour qu'elle accepte des bytes ou un chemin de fichier au lieu d'un objet st.file_uploader
#        file_bytes = await file.read()
#        template = creation_template_from_file(file_bytes, chosen_model)
#        return {"template": template}
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))

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
    


