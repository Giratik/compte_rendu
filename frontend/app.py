import streamlit as st
import time
import json
import os
import requests

# --- Configuration ---
st.set_page_config(page_title="Transcription & Résumé", layout="wide")
st.title("Transcription & Compte Rendu de réunion")

import os
# Récupère l'URL définie dans docker-compose, sinon utilise localhost en local
API_URL = os.environ.get("API_URL", "http://localhost:8001")
DEFAULT_LLM_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "mistral-nemo")
CHUNK_CONTEXT_SIZE = os.environ.get("CHUNK_CONTEXT_SIZE", 9999)
FULL_SUMMARY_CONTEXT_SIZE = os.environ.get("FULL_SUMMARY_CONTEXT_SIZE", 12288)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
TEMPERATURE = os.environ.get("TEMPERATURE", 0.15)

# Initialisation des variables de session
for key in ["transcript_text", "format_instructions_fichier", "final_summary", "combined_notes", "is_transcribing"]:
    if key not in st.session_state:
        # On initialise is_transcribing à False par défaut
        if key == "is_transcribing":
            st.session_state[key] = False
        else:
            st.session_state[key] = None if key != "transcript_text" else ""



# --- UI ---
with st.sidebar:
    loaded = None
    st.subheader("🧠 Modèles Ollama en mémoire")
    st.text("Ce bouton n'est pas destiné à rester. Si un modèle se trouve en mémoire, vous ne pourrez pas utiliser le modèle de transcription, donc veillez à cliquer sur le bouton pour vider le modèle en mémoire et recharger la page pour valider sa disparition")
    try:
        loaded = requests.get(f"{API_URL}/models/loaded")
        loaded.raise_for_status()
    except Exception as e:
                st.error(f"Erreur de communication avec le serveur : {e}. Les modèles n'ont pas été récupérés")
    #loaded = get_loaded_models()

    if loaded != None:
        st.info("Aucun modèle en mémoire.")
    else:
        for m in loaded.json():
            col1, col2 = st.columns([2, 1])
            col1.write(m["name"])
            col2.write(f"{round(m.get('size', 0) / 1e9, 2)} Go")
            if st.button("🗑️ Libérer", key=m["name"]):
                try:
                    response = requests.post(f"{API_URL}/models/unload?model_name={m['name']}")
                    response.raise_for_status()
                except Exception as e:
                    st.error(f"Erreur : {e}")
                st.rerun()




@st.cache_data(ttl=60)
def charger_templates_api():
    url = f"{API_URL}/ressources/files"
    
    try:
        reponse = requests.get(url, timeout=10)
        reponse.raise_for_status()
        return reponse.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des templates : {e}")
        return []

# Appel de la fonction
templates = charger_templates_api()

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



# --- CHOIX DU MODE D'ENTRÉE ---
#st.write("### Étape 1 : Source du texte")
#user_email = st.text_input("📩 Votre adresse email (Optionnel, pour recevoir une notification à la fin) = > ça fonctionne pas ", placeholder="jean.duponteaudeparis.fr")

user_email = None
input_mode = st.radio(
    "Comment voulez-vous fournir le texte ?",
    ["Transcrire un fichier Audio/Vidéo", "Uploader un fichier Texte existant (.txt)"],
    horizontal=True
)

if input_mode == "Transcrire un fichier Audio/Vidéo":
    uploaded_file = st.file_uploader(
        "Déposez votre fichier audio ou vidéo", 
        type=["wav", "mp3", "m4a", "flac", "mp4", "avi", "mov", "mkv"],
    )

    # Sécurité : Le bouton est grisé si pas de fichier OU si déjà en cours
    bouton_disabled = (uploaded_file is None) or st.session_state.is_transcribing
    # On change dynamiquement le texte du bouton pour informer l'utilisateur
    label_bouton = "⌛ Transcription en cours..." if st.session_state.is_transcribing else "Lancer la transcription"

    if st.button(label_bouton, disabled=bouton_disabled):
        st.session_state.is_transcribing = True
        st.rerun() # Force la mise à jour de l'UI pour griser le bouton

# Ce bloc ne s'exécute que si l'état est "en cours"
    if st.session_state.is_transcribing and uploaded_file is not None:
        with st.spinner("Envoi au serveur et transcription en cours..."):
            start_time = time.time()
            
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"model_choice": WHISPER_MODEL, "email_destinataire": user_email}
            
            try:
                response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                response.raise_for_status()
                
                st.session_state.transcript_text = response.json()["transcript"]
                
                execution_time = time.time() - start_time
                st.success(f"Transcription terminée en {int(execution_time // 60)} min !")
                st.toast('🎙️ La transcription audio est terminée !', icon='✅')
            except Exception as e:
                st.error(f"Erreur de communication : {e}")
            finally:
                # IMPORTANT : On libère le bouton quoi qu'il arrive (succès ou erreur)
                st.session_state.is_transcribing = False
                st.rerun()

elif input_mode == "Uploader un fichier Texte existant (.txt)":
    uploaded_text = st.file_uploader("Déposez votre fichier texte (.txt)", type=["txt"])
    if uploaded_text is not None:
        text_content = uploaded_text.getvalue().decode("utf-8")
        if st.button("Charger ce texte"):
            st.session_state.transcript_text = text_content
            st.success("✅ Fichier texte chargé avec succès !")

# --- AFFICHAGE ET RÉSUMÉ ---
if st.session_state.transcript_text:
    st.markdown("---")
    st.write("### Génération Compte-rendu")
    #st.subheader("📝 Résultat de la transcription")
    
    transcript_editor = st.text_area("Texte à analyser", value=st.session_state.transcript_text, height=250)
    transcript_editor = st.session_state.transcript_text

    mots = transcript_editor.split()
    nb_mots = len(mots)
    
    if nb_mots > 0:
        taille_morceau = 2000 
        chevauchement = 200   

        chunks = []
        i = 0
        while i < nb_mots:
            chunk_mots = mots[i : i + taille_morceau]
            chunks.append(" ".join(chunk_mots))
            i += (taille_morceau - chevauchement)
            
        nb_chunks = len(chunks)

        selection_option = st.radio("Choisissez ce que l'IA doit générer :",
                                    ["Un résumé de la réunion", "Un compte-rendu de la réunion"],
                                    )
        
        prompt_instructions = None
        format_instructions = None

        if "Un compte-rendu de la réunion" in selection_option:
            prompt_instructions = """Tu es un documentaliste intraitable et exhaustif. Ton but est de compiler les notes de réunion suivantes dans le format demandé, SANS JAMAIS généraliser ni omettre de détails.

Voici tes règles STRICTES :
1. FACTUEL ET EXHAUSTIF : Si les notes mentionnent un prix, une durée, une métrique, une anecdote ou un exemple précis (ex: mots corrigés), TU DOIS absolument l'inclure.
2. NE PAS RÉSUMER LES LISTES : Cite TOUS les outils, logiciels, entreprises et intervenants mentionnés dans les notes. Ne dis jamais "plusieurs outils", nomme-les tous un par un.
3. OBJECTIVITÉ : Garde un ton neutre et professionnel.
4. FIDÉLITÉ : N'invente aucune information, mais ne perds aucune donnée brute présente dans les notes.
"""
            format_instructions = """
# Compte Rendu de Réunion

---------
Date : {...}
Heure de début : {...}
---------

# Paricipant à la réunion
{nom}{prénom}
{nom}{prénom}
...

# Ordre du jour
{...}


## Objectif principal / Sujet global
(Résume en 2 ou 3 phrases le but central de cet échange)

## Intervenants et Personnes citées
* (Lister exhaustivement TOUTES les personnes mentionnées dans les notes : présents, absents, ou évoqués)

## Outils, Solutions et Tarifs mentionnés
(Lister TOUS les outils, logiciels ou entreprises cités, avec leurs prix, métriques ou caractéristiques exactes s'ils sont mentionnés dans les notes)
* [Nom de l'outil] : (Détails techniques, prix, durée d'essai, limitations, etc.)

## Points de discussion et Faits précis
(Détaillez les arguments, les retours d'expérience et les exemples techniques précis abordés. Soyez exhaustif)
* (Point 1 : ...)
* (Point 2 : ...)

## Décisions Actées
(S'il n'y en a pas, écris "Aucune décision formelle prise".)
* [Décision] : (Détail)

## Plan d'action (Prochaines étapes)
(Précise "Qui" et "Quand" si mentionné).
* [ ] Action : ... | Assigné à : ... | Délai : ...
"""

        if "Un résumé de la réunion" in selection_option:
            prompt_instructions = """Tu es un documentaliste intraitable et exhaustif. Ton but est de résumer les notes de réunion suivantes dans le format demandé.
            Tu dois produire un résumer pour permettre de comprendre les points de discussion de la réunion, les actions prises de sorte à ce que n'importe qui soit capable d'être correctement informé seulement avec le résumé."""

            format_instructions ="""
Tu es un assistant de direction spécialisé dans la synthèse d'informations. À partir de la transcription ou des notes fournies, rédige un résumé rapide et percutant (Executive Summary). Ignore les petites digressions ou les détails opérationnels mineurs. Respecte strictement la structure suivante :\n\n# L'Essentiel (TL;DR)\n(Résume le contexte, l'objectif et l'issue principale de la réunion en un seul paragraphe de 3 à 4 phrases maximum.)\n\n# Les Points Clés à Retenir\n(Mets en évidence les informations majeures, les grandes annonces ou les points de blocage importants. Utilise des puces pour faciliter la lecture rapide.)\n* ...\n* ...\n\n# Actions Critiques\n(Liste uniquement les prochaines étapes majeures qui découlent directement de cette réunion. Ne mets pas les micro-tâches.)\n* [Action] - [Responsable] - [Échéance]
"""
#
        # --- ACTION DE GÉNÉRATION ---
        if st.button("Lancer la génération"):
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # ÉTAPE 1 : MAP (Appels API en boucle)
                partial_summaries = []
                for index, chunk in enumerate(chunks):
                    num_etape = index + 1
                    progress_text.text(f"🔍 Section {num_etape}/{nb_chunks} : Analyse API en cours...")

                    payload = {
                        "chunk": chunk,
                        "chunk_index": num_etape,
                        "total_chunks": nb_chunks,
                        "temperature": TEMPERATURE,
                        "model_name": DEFAULT_LLM_MODEL,
                        "num_ctx": CHUNK_CONTEXT_SIZE,
                        "passes": 2
                    }

                    res_chunk = requests.post(f"{API_URL}/summarize_chunk/", json=payload)
                    res_chunk.raise_for_status()
                    resume_partiel = res_chunk.json()["summary"]
                    

                    partial_summaries.append(f"### Faits de la section {num_etape}\n{resume_partiel}")
                    progress_bar.progress(num_etape / (nb_chunks + 1)) 
                
                combined_notes_temp = "\n\n".join(partial_summaries)
                
                # ÉTAPE 2 : REDUCE (Synthèse via API)
                progress_text.text("✍️ Rédaction du compte rendu global par l'API...")
                
                payload_synth = {
                    "combined_notes": combined_notes_temp,
                    "prompt_cr": prompt_instructions,
                    "format_cr": format_instructions,
                    "temperature": TEMPERATURE,
                    "model_name": DEFAULT_LLM_MODEL,
                    "num_ctx": FULL_SUMMARY_CONTEXT_SIZE,
                    "email_destinataire": user_email
                }
                
                res_synth = requests.post(f"{API_URL}/synthesize/", json=payload_synth)
                res_synth.raise_for_status()
                final_summary_temp = res_synth.json()["final_summary"]
                
                progress_bar.progress(1.0)
                progress_text.text("✅ Terminé !")
                
                st.session_state.final_summary = final_summary_temp
                st.session_state.combined_notes = combined_notes_temp

                st.toast('La génération du compte-rendu est terminée', icon='🎉')
                
            except Exception as e:
                st.error(f"Erreur de l'API : {e}")
                
        # --- AFFICHAGE ET TÉLÉCHARGEMENT ---
        if st.session_state.final_summary:
            st.success(f"Résumé généré !")
            #st.markdown(st.session_state.final_summary)
            
            with st.expander("Voir les notes extraites (Brouillon)"):
                st.markdown(st.session_state.combined_notes)
            
            st.markdown("---")
            st.subheader("📥 Télécharger le document final")
            
            try:
                # Demande du DOCX au backend
                payload_docx = {"markdown_text": st.session_state.final_summary}
                res_docx = requests.post(f"{API_URL}/generate_docx/", json=payload_docx)
                ftype = "Résumé de la réunion"
                if "Un compte-rendu de la réunion" in selection_option :
                    ftype = "Compte-rendu de la réunion"
                if res_docx.status_code == 200:
                    st.download_button(
                        label="📄 Télécharger en Word (.docx)",
                        data=res_docx.content, # Les bytes bruts du fichier Word
                        file_name=f"{ftype}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.error("Erreur API lors de la génération du Word.")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")
