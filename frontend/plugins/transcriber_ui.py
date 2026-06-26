import streamlit as st
import requests
import time
import os
import uuid

API_URL = os.environ.get("API_URL", "http://localhost:8000")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")

def render_transcriber():
    """Plugin UI autonome pour la transcription"""
    st.subheader("🎙️ Module de Transcription")
    
    # 1. Initialisation de l'état
    if "is_transcribing" not in st.session_state:
        st.session_state.is_transcribing = False
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "transcription_queue_token" not in st.session_state:
        st.session_state.transcription_queue_token = None
    if "transcription_queue_position" not in st.session_state:
        st.session_state.transcription_queue_position = None

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

        en_file_attente = st.session_state.transcription_queue_token is not None
        
        # --- 2. GESTION DU BOUTON PRINCIPAL ---
        bouton_disabled = (uploaded_file is None) or st.session_state.is_transcribing or en_file_attente
        
        if en_file_attente and st.session_state.transcription_queue_position > 1:
            label_bouton = f"🕒 En attente (Position {st.session_state.transcription_queue_position})"
        elif st.session_state.is_transcribing:
            label_bouton = "⌛ Transcription en cours..."
        else:
            label_bouton = "Lancer la transcription"

        if st.button(label_bouton, disabled=bouton_disabled, key="btn_run_transcription"):
            st.session_state.is_transcribing = True
            st.rerun()

        # --- 3. POLLING DE LA FILE D'ATTENTE (Background stable) ---
        if en_file_attente and not st.session_state.is_transcribing:
            if st.session_state.transcription_queue_position > 1:
                # Message informatif qui ne clignote pas
                st.info(f"⏳ Vous êtes en position **{st.session_state.transcription_queue_position}** dans la file d'attente. Veuillez patienter...")
                
                try:
                    # Utilisation du endpoint GET léger (sans envoyer le fichier lourd)
                    response = requests.get(f"{API_URL}/transcribe/queue-position", params={
                        "queue_token": st.session_state.transcription_queue_token
                    })
                    
                    if response.status_code == 200:
                        position_data = response.json()
                        if position_data.get("status") == "waiting":
                            st.session_state.transcription_queue_position = position_data.get("position")
                        elif position_data.get("status") == "processing":
                            st.session_state.transcription_queue_position = 1
                    else:
                        # Fallback silencieux en cas d'erreur réseau
                        time.sleep(3)
                        st.rerun()

                    # Si c'est notre tour, on bascule is_transcribing à True
                    if st.session_state.transcription_queue_position == 1:
                        st.success("🚀 C'est votre tour ! Démarrage imminent...")
                        time.sleep(1)
                        st.session_state.is_transcribing = True
                        st.rerun()
                    else:
                        # Attente adaptative avant le prochain rafraichissement
                        time.sleep(2 if st.session_state.transcription_queue_position <= 2 else 5)
                        st.rerun()

                except Exception as e:
                    time.sleep(5)
                    st.rerun()

            elif st.session_state.transcription_queue_position == 1:
                st.session_state.is_transcribing = True
                st.rerun()

        # --- 4. ENVOI DE LA TRANSCRIPTION (ou demande de place) ---
        if st.session_state.is_transcribing and uploaded_file is not None:
            
            # Le message s'adapte : on vérifie si on demande un ticket ou si on effectue la vraie transcription
            msg_spinner = "Envoi au serveur et transcription en cours (cela peut prendre plusieurs minutes)..." if en_file_attente else "Demande d'une place dans la file d'attente..."

            with st.spinner(msg_spinner):
                start_time = time.time()
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"model_choice": WHISPER_MODEL, "session_id": st.session_state.session_id}

                if st.session_state.transcription_queue_token:
                    data["queue_token"] = st.session_state.transcription_queue_token

                try:
                    response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                    response.raise_for_status()
                    response_data = response.json()

                    if response_data.get("status") in ["queued", "waiting"]:
                        # On a reçu un ticket d'attente, on bascule en mode attente (is_transcribing = False)
                        st.session_state.transcription_queue_token = response_data.get("queue_token", st.session_state.transcription_queue_token)
                        st.session_state.transcription_queue_position = response_data["position"]
                        st.session_state.is_transcribing = False 
                        st.rerun()

                    elif "transcript" in response_data:
                        # Succès de la transcription
                        st.session_state.transcription_queue_token = None
                        st.session_state.transcription_queue_position = None
                        st.session_state.transcript_text = response_data["transcript"]
                        st.session_state.token_count = len(st.session_state.transcript_text.split())
                        
                        execution_time = time.time() - start_time
                        st.success(f"Transcription terminée en {int(execution_time // 60)} min !")
                        st.toast('🎙️ La transcription audio est terminée !', icon='✅')
                        if 'token_count' in st.session_state:
                            st.info(f"📊 Nombre de tokens dans le transcript : {st.session_state.token_count}")
                        
                    else:
                        st.error(f"Réponse inattendue: {response_data}")
                        st.session_state.transcription_queue_token = None
                        st.session_state.transcription_queue_position = None
                        
                except Exception as e:
                    st.error(f"Erreur de communication : {e}")
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
                token_count = len(st.session_state.transcript_text.split())
                st.session_state.token_count = token_count
                st.success("✅ Fichier texte chargé avec succès !")
                if 'token_count' in st.session_state:
                    st.info(f"📊 Nombre de tokens dans le transcript : {st.session_state.token_count}")