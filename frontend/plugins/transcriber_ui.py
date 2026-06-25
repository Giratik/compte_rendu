#/frontend/plugins/transcriber_ui.py

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
            st.info(f"🕒 Vous êtes en position {st.session_state.transcription_queue_position} dans la file d'attente")

            # Auto-start transcription if it's our turn (position 1)
            if st.session_state.transcription_queue_position == 1 and not st.session_state.is_transcribing and uploaded_file is not None:
                st.info("🚀 C'est votre tour ! La transcription démarre automatiquement...")
                st.session_state.is_transcribing = True
                st.rerun()

        bouton_disabled = (uploaded_file is None) or st.session_state.is_transcribing
        label_bouton = "⌛ Transcription en cours..." if st.session_state.is_transcribing else "Lancer la transcription"

        if st.button(label_bouton, disabled=bouton_disabled, key="btn_run_transcription"):
            st.session_state.is_transcribing = True
            st.rerun()

        # Background queue position polling for users in queue
        if (st.session_state.transcription_queue_token and
            st.session_state.transcription_queue_position and
            st.session_state.transcription_queue_position > 1 and
            not st.session_state.is_transcribing):

            # Implement background polling for queue position
            try:
                # Try the new queue position endpoint first
                try:
                    response = requests.get(f"{API_URL}/transcribe/queue-position", params={
                        "queue_token": st.session_state.transcription_queue_token
                    })
                    response.raise_for_status()
                    position_data = response.json()
                    new_position = position_data["position"]
                except requests.exceptions.HTTPError as http_error:
                    if http_error.response.status_code == 404:
                        # Fallback: if the endpoint doesn't exist, use the main transcription endpoint
                        # to check position by making a request with just the queue token
                        files = {"file": ("dummy.txt", b"dummy", "text/plain")}
                        data = {"queue_token": st.session_state.transcription_queue_token}

                        response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                        response.raise_for_status()
                        response_data = response.json()

                        if response_data.get("status") == "waiting":
                            new_position = response_data["position"]
                        elif response_data.get("status") == "error":
                            # Token is invalid - this means either:
                            # 1. It's our turn and we should start transcription
                            # 2. The token has expired
                            # Let's check if we should start transcription
                            if (st.session_state.transcription_queue_position == 2 and
                                uploaded_file is not None and
                                not st.session_state.is_transcribing):
                                # If we were in position 2 and token is now invalid, it might be our turn
                                st.info("🚀 Il semble que ce soit votre tour ! La transcription démarre...")
                                st.session_state.is_transcribing = True
                                st.rerun()
                                return
                            else:
                                # Token is truly invalid, reset queue state
                                st.error(f"Erreur de file d'attente: {response_data['message']}")
                                st.session_state.transcription_queue_token = None
                                st.session_state.transcription_queue_position = None
                                time.sleep(5)
                                st.rerun()
                                return
                        else:
                            # If we get a different status, fall back to the original polling method
                            st.session_state.is_transcribing = True
                            st.rerun()
                            return
                    else:
                        raise

                old_position = st.session_state.transcription_queue_position
                st.session_state.transcription_queue_position = new_position

                # If we moved up to position 1, start transcription automatically
                if st.session_state.transcription_queue_position == 1 and uploaded_file is not None:
                    st.info("🚀 C'est maintenant votre tour ! La transcription démarre automatiquement...")
                    st.session_state.is_transcribing = True
                    st.rerun()
                    return

                # Show updated position if it changed
                if old_position != st.session_state.transcription_queue_position:
                    st.info(f"📈 Votre position a été mise à jour: {st.session_state.transcription_queue_position}")

                # Adjust polling frequency based on position
                if st.session_state.transcription_queue_position <= 2:
                    time.sleep(2)  # Check frequently when near front
                else:
                    time.sleep(5)  # Check less frequently when further back

                st.rerun()
                return

            except Exception as e:
                st.error(f"Erreur lors de la vérification de la position: {e}")
                time.sleep(5)  # Wait before retrying

        # Check if we should start transcription automatically (when we reach position 1)
        if (st.session_state.transcription_queue_token and
            st.session_state.transcription_queue_position == 1 and
            not st.session_state.is_transcribing and
            uploaded_file is not None):
            st.session_state.is_transcribing = True
            st.rerun()

        if st.session_state.is_transcribing and uploaded_file is not None:
            with st.spinner("Envoi au serveur et transcription en cours..."):
                start_time = time.time()
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
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
                        # Still waiting in queue
                        old_position = st.session_state.transcription_queue_position
                        st.session_state.transcription_queue_position = response_data["position"]
                        st.info(f"🕒 {response_data['message']}")

                        # Adjust polling frequency based on position
                        # If we're getting closer to the front, check more frequently
                        if st.session_state.transcription_queue_position <= 2:
                            # Near the front - check every 2 seconds
                            time.sleep(2)
                        else:
                            # Further back - check every 5 seconds
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