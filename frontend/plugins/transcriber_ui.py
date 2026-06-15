import streamlit as st
import requests
import time
import os

API_URL = os.environ.get("API_URL", "http://localhost:8001")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")

def render_transcriber():
    """Plugin UI autonome pour la transcription"""
    st.subheader("🎙️ Module de Transcription")
    
    # Gestion locale de l'état du plugin
    if "is_transcribing" not in st.session_state:
        st.session_state.is_transcribing = False

    input_mode = st.radio(
        "Comment voulez-vous fournir le texte ?",
        ["Fichier Audio/Vidéo", "Fichier Texte existant (.txt)"],
        horizontal=True,
        key="transcriber_input_mode"
    )

    if input_mode == "Fichier Audio/Vidéo":
        uploaded_file = st.file_uploader(
            "Déposez votre fichier audio ou vidéo", 
            type=["wav", "mp3", "m4a", "flac", "mp4", "avi", "mov", "mkv"],
            key="transcriber_uploader"
        )

        bouton_disabled = (uploaded_file is None) or st.session_state.is_transcribing
        label_bouton = "⌛ Transcription en cours..." if st.session_state.is_transcribing else "Lancer la transcription"

        if st.button(label_bouton, disabled=bouton_disabled, key="btn_run_transcription"):
            st.session_state.is_transcribing = True
            st.rerun() 

        if st.session_state.is_transcribing and uploaded_file is not None:
            with st.spinner("Envoi au serveur et transcription en cours..."):
                start_time = time.time()
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"model_choice": WHISPER_MODEL}
                
                try:
                    response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                    response.raise_for_status()

                    # On sauvegarde le résultat dans le state global pour que d'autres plugins (comme le résumé) puissent l'utiliser
                    st.session_state.transcript_text = response.json()["transcript"]

                    # Calculate and display token count
                    token_count = len(st.session_state.transcript_text.split())
                    st.session_state.token_count = token_count

                    execution_time = time.time() - start_time
                    st.success(f"Transcription terminée en {int(execution_time // 60)} min !")
                    st.toast('🎙️ La transcription audio est terminée !', icon='✅')
                    # Display token count
                    if 'token_count' in st.session_state:
                        st.info(f"📊 Nombre de tokens dans le transcript : {st.session_state.token_count}")
                except Exception as e:
                    st.error(f"Erreur de communication : {e}")
                finally:
                    st.session_state.is_transcribing = False
                    st.rerun()

    elif input_mode == "Fichier Texte existant (.txt)":
        uploaded_text = st.file_uploader("Déposez votre fichier texte (.txt)", type=["txt"], key="txt_uploader")
        if uploaded_text is not None:
            if st.button("Charger ce texte", key="btn_load_txt"):
                st.session_state.transcript_text = uploaded_text.getvalue().decode("utf-8")
                # Calculate and display token count for text file
                token_count = len(st.session_state.transcript_text.split())
                st.session_state.token_count = token_count
                st.success("✅ Fichier texte chargé avec succès !")
                # Display token count
                if 'token_count' in st.session_state:
                    st.info(f"📊 Nombre de tokens dans le transcript : {st.session_state.token_count}")
