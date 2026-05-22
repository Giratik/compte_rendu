import streamlit as st
import os
import requests

from plugins.transcriber_ui import render_transcriber
from plugins.summarizer_ui import render_summarizer

# --- Configuration ---
st.set_page_config(page_title="Transcription & Résumé", layout="wide")
st.title("Transcription & Compte Rendu de réunion")

# Récupère l'URL définie dans docker-compose, sinon utilise localhost en local
API_URL = os.environ.get("API_URL", "http://localhost:8001")

# Initialisation des variables de session
for key in ["transcript_text", "format_instructions_fichier", "final_summary", "combined_notes", "is_transcribing"]:
    if key not in st.session_state:
        # On initialise is_transcribing à False par défaut
        if key == "is_transcribing":
            st.session_state[key] = False
        else:
            st.session_state[key] = None if key != "transcript_text" else ""


# --- UI ---
#with st.sidebar:
#    loaded = None
#    st.subheader("🧠 Modèles Ollama en mémoire")
#    st.text("Ce bouton n'est pas destiné à rester. Si un modèle se trouve en mémoire, vous ne pourrez pas utiliser le modèle de transcription, donc veillez à cliquer sur le bouton pour vider le modèle en mémoire et recharger la page pour valider sa disparition")
#    try:
#        loaded = requests.get(f"{API_URL}/models/loaded")
#        loaded.raise_for_status()
#    except Exception as e:
#                st.error(f"Erreur de communication avec le serveur : {e}. Les modèles n'ont pas été récupérés")
#    #loaded = get_loaded_models()
#
#    if loaded != None:
#        st.info("Aucun modèle en mémoire.")
#    else:
#        for m in loaded.json():
#            col1, col2 = st.columns([2, 1])
#            col1.write(m["name"])
#            col2.write(f"{round(m.get('size', 0) / 1e9, 2)} Go")
#            if st.button("🗑️ Libérer", key=m["name"]):
#                try:
#                    response = requests.post(f"{API_URL}/models/unload?model_name={m['name']}")
#                    response.raise_for_status()
#                except Exception as e:
#                    st.error(f"Erreur : {e}")
#                st.rerun()

#tab_transcription, tab_resume = st.tabs(["🎙️ 1. Transcription", "📝 2. Compte-Rendu IA"])


#@st.cache_data(ttl=60)
#def charger_templates_api():
#    url = f"{API_URL}/ressources/files"
#    
#    try:
#        reponse = requests.get(url, timeout=10)
#        reponse.raise_for_status()
#        return reponse.json()
#    except requests.exceptions.RequestException as e:
#        st.error(f"Erreur lors de la récupération des templates : {e}")
#        return []
#
## Appel de la fonction
#templates = charger_templates_api()

#@st.cache_data # Permet de ne pas recharger le fichier à chaque interaction
#def charger_templates(chemin_fichier):
#    try:
#        with open(chemin_fichier, 'r', encoding='utf-8') as f:
#            donnees = json.load(f)
#            return donnees['templates']
#    except FileNotFoundError:
#        st.error(f"Le fichier {chemin_fichier} est introuvable.")
#        return []
#    
#templates = charger_templates('ressources/templates_reunions.json')




#with tab_transcription:
    # Appel du bloc prêt et fonctionnel
render_transcriber()

# --- AFFICHAGE ET RÉSUMÉ ---
render_summarizer()