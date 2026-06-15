#frontend/app.py

import streamlit as st
import os
import requests

from plugins.transcriber_ui import render_transcriber
from plugins.chunks_summary_ui import render_summarizer
LOGO_PATH = "ressource/Eau_de_Paris_bleu.svg.png"
# --- Configuration ---
st.set_page_config(page_title="Transcription & Résumé", layout="wide")
st.title("Transcription & Compte Rendu de réunion")

if os.path.exists(LOGO_PATH):
        st.logo(LOGO_PATH)

# Initialisation des variables de session
for key in ["transcript_text", "format_instructions_fichier", "final_summary", "combined_notes", "is_transcribing"]:
    if key not in st.session_state:
        # On initialise is_transcribing à False par défaut
        if key == "is_transcribing":
            st.session_state[key] = False
        else:
            st.session_state[key] = None if key != "transcript_text" else ""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

#MainMenu, footer, header { visibility: none; }

.title-block { padding: 2rem 0 1.5rem 0; border-bottom: 1px solid #2a2d35; margin-bottom: 2rem; }
.title-block h1 { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em; color: #e8e4dc; margin: 0; }
.title-block span { color: #87CEEB; }
.title-block p { color: #6b7280; font-size: 0.9rem; margin: 0.4rem 0 0 0; font-family: 'JetBrains Mono', monospace; }

.col-header { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
    color: #4b5563; font-family: 'JetBrains Mono', monospace; padding-bottom: 0.8rem;
    border-bottom: 1px solid #2a2d35; margin-bottom: 1.2rem; }

.status-bar { background: #13161d; border: 1px solid #2a2d35; border-radius: 6px;
    padding: 0.8rem 1.2rem; margin-bottom: 1.5rem; display: flex; align-items: center;
    gap: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #6b7280; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
    display: inline-block; animation: pulse 2s infinite; }
.status-dot.idle { background: #4b5563; animation: none; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.chunk-card {  border: 1px solid #2a2d35;
    border-radius: 6px; padding: 1rem 1.2rem; margin-bottom: 0.5rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; 
    line-height: 1.7; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
.chunk-card::-webkit-scrollbar { width: 4px; }
.chunk-card::-webkit-scrollbar-track { background: #13161d; }
.chunk-card::-webkit-scrollbar-thumb { background: #2a2d35; border-radius: 2px; }

.chunk-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.8rem; }
.chunk-badge { background: #87CEEB; color: #0d0f14; font-size: 0.65rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; padding: 0.15rem 0.5rem;
    border-radius: 3px; letter-spacing: 0.05em; }
.chunk-label { color: #4b5563; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

.summary-pending { border: 1px dashed #2a2d35; border-radius: 6px;
    padding: 1rem 1.2rem; color: #4b5563; font-size: 0.82rem; font-style: italic;
    display: flex; align-items: center; gap: 0.5rem; min-height: 80px; }

.chunk-row { background: #13161d; border: 1px solid #2a2d35; border-radius: 8px;
    padding: 1.5rem; margin-bottom: 1.5rem; }

.stTextArea textarea { border: 1px solid #2a2d35 !important;
    border-radius: 6px !important; 
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; }
.stTextArea textarea:focus { border-color: #87CEEB !important; box-shadow: 0 0 0 1px #87CEEB !important; }

.stButton button { background: #87CEEB !important; color: #0d0f14 !important; border: none !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 0.82rem !important; letter-spacing: 0.03em !important;
    border-radius: 5px !important; padding: 0.5rem 1.2rem !important; }
.stButton button:hover { background: #ffd700 !important; }

div[data-testid="stFileUploaderDropzone"] { background: #13161d !important; }
label, .stSelectbox label, .stSlider label { color: #9ca3af !important;
    font-size: 0.8rem !important; font-family: 'JetBrains Mono', monospace !important; }
.stSelectbox div[data-baseweb="select"] { background: #13161d !important; border-color: #2a2d35 !important; }
.stMarkdown hr { border-color: #2a2d35 !important; }
</style>
""", unsafe_allow_html=True)


defaults = {
    "chunks": [],
    "summaries": [],
    "processing": False,
    "global_summary": "",
    "current_chunk": -1,
    "indices_to_process": [],
    "process_pos": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


#with tab_transcription:
    # Appel du bloc prêt et fonctionnel
render_transcriber()

if st.session_state.transcript_text:
    # --- AFFICHAGE ET RÉSUMÉ ---
    render_summarizer()