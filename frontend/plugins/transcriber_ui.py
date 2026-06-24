import streamlit as st
import requests
import time
import os
import uuid

API_URL = os.environ.get("API_URL", "http://localhost:8001")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")

def render_transcriber():
    """Plugin UI autonome pour la transcription"""
    st.subheader("🎙️ Module de Transcription")
    
    # Gestion locale de l'état du plugin
    if "is_transcribing" not in st.session_state:
        st.session_state.is_transcribing = False
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    input_mode = st.radio(
        "Comment voulez-vous fournir le texte ?",
        ["Fichier Audio/Vidéo", "Fichier Texte existant (.txt)"],
        horizontal=True,
        key="transcriber_input_mode"
    )

    if input_mode == "Fichier Audio/Vidéo":
        uploaded_file = st.file_uploader(
            "Déposez votre fichier audio ou vidéo",
            type=["wav", "mp3", "m4a", "flac", "mp4", "avi", "mov", "mkv", "webm"],
            key="transcriber_uploader"
        )

        # Initialize queue state
        if "transcription_queue_token" not in st.session_state:
            st.session_state.transcription_queue_token = None
        if "transcription_queue_position" not in st.session_state:
            st.session_state.transcription_queue_position = None

        # Show queue status if in queue
        if st.session_state.transcription_queue_token and st.session_state.transcription_queue_position:
            #st.info(f"🕒 Position {st.session_state.transcription_queue_position} dans la file")
            # Toujours relancer une vérification, peu importe la position affichée
            if not st.session_state.is_transcribing:
                st.session_state.is_transcribing = True
                st.rerun()

            # Auto-start transcription if it's our turn (position 1)
            if st.session_state.transcription_queue_position == 1 and not st.session_state.is_transcribing:
                st.success("🚀 C'est votre tour ! Démarrage de la transcription...")
                time.sleep(1.5)
                st.session_state.is_transcribing = True
                st.rerun()
            elif not st.session_state.is_transcribing:
                st.info(f"🕒 Position {st.session_state.transcription_queue_position} dans la file")
                st.session_state.is_transcribing = True
                st.rerun()
        bouton_disabled = (uploaded_file is None) or st.session_state.is_transcribing
        label_bouton = "⌛ Transcription en cours..." if st.session_state.is_transcribing else "Lancer la transcription"

        if st.button(label_bouton, disabled=bouton_disabled, key="btn_run_transcription"):
            st.session_state.is_transcribing = True
            st.rerun()

        if st.session_state.is_transcribing and uploaded_file is not None:
            with st.spinner("Envoi au serveur et transcription en cours..."):
                start_time = time.time()
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                                
                # Envoyé à chaque requête
                data = {"model_choice": WHISPER_MODEL, "session_id": st.session_state.session_id}

                # Add queue token if we have one
                if st.session_state.transcription_queue_token:
                    data["queue_token"] = st.session_state.transcription_queue_token

                try:
                    response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                    response.raise_for_status()

                    response_data = response.json()

                    if response_data.get("status") == "queued":
                        # First request - got queue position
                        st.session_state.transcription_queue_token = response_data["queue_token"]
                        st.session_state.transcription_queue_position = response_data["position"]
                        st.session_state.is_transcribing = False
                        st.rerun()
                        return

                    elif response_data.get("status") == "waiting":
                        st.session_state.transcription_queue_position = response_data["position"]
                        with st.spinner(f"🕒 Position {response_data['position']} dans la file. Si le message cesse d'appraître, alors votre fichier est traité."):
                            time.sleep(5)
                        st.rerun()
                        return

                    elif "transcript" in response_data:
                        # Success - got transcription
                        st.session_state.transcription_queue_token = None
                        st.session_state.transcription_queue_position = None

                        # On sauvegarde le résultat dans le state global pour que d'autres plugins (comme le résumé) puissent l'utiliser
                        st.session_state.transcript_text = response_data["transcript"]

                        # Calculate and display token count
                        token_count = len(st.session_state.transcript_text.split())
                        st.session_state.token_count = token_count

                        execution_time = time.time() - start_time
                        st.success(f"Transcription terminée en {int(execution_time // 60)} min !")
                        st.toast('🎙️ La transcription audio est terminée !', icon='✅')
                        # Display token count
                        if 'token_count' in st.session_state:
                            st.info(f"📊 Nombre de tokens dans le transcript : {st.session_state.token_count}")
                    else:
                        st.error(f"Réponse inattendue du serveur: {response_data}")

                except Exception as e:
                    st.error(f"Erreur de communication : {e}")
                    # Reset queue state on error
                    st.session_state.transcription_queue_token = None
                    st.session_state.transcription_queue_position = None
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
