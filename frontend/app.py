import streamlit as st
import time
import json
import requests

# --- Configuration ---
st.set_page_config(page_title="Transcription & Résumé", layout="wide")
st.title("Transcription & Compte Rendu de réunion")

# L'URL de ton API FastAPI
API_URL = "http://127.0.0.1:8001"

# Initialisation des variables de session
for key in ["transcript_text", "format_instructions_fichier", "final_summary", "combined_notes"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "transcript_text" else ""

model_choice = "large-v3"
context_options = 16384
selected_temp = 0.15
light_model = "mistral-nemo"
heavy_model = "mistral-small:22b"
chosen_model = heavy_model


@st.cache_data # Permet de ne pas recharger le fichier à chaque interaction
def charger_templates(chemin_fichier):
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            donnees = json.load(f)
            return donnees['templates']
    except FileNotFoundError:
        st.error(f"Le fichier {chemin_fichier} est introuvable.")
        return []
    
templates = charger_templates('ressources/templates_reunions.json')

# --- CHOIX DU MODE D'ENTRÉE ---
st.write("### Étape 1 : Source du texte")
user_email = st.text_input("📩 Votre adresse email (Optionnel, pour recevoir une notification à la fin) = > ça fonctionne pas ", placeholder="jean.dupont@entreprise.com")
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

    if st.button("Lancer la transcription") and uploaded_file is not None:
        with st.spinner("Envoi au serveur et transcription en cours... (Ceci peut prendre du temps)"):
            start_time = time.time()
            
            # Préparation du fichier pour l'envoi via l'API
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"model_choice": model_choice, "email_destinataire": user_email}
            
            try:
                response = requests.post(f"{API_URL}/transcribe/", files=files, data=data)
                response.raise_for_status()
                
                st.session_state.transcript_text = response.json()["transcript"]
                
                execution_time = time.time() - start_time
                st.success(f"Transcription terminée en {int(execution_time // 60)} min et {int(execution_time % 60)} s !")
                st.toast('🎙️ La transcription audio est terminée !', icon='✅')
            except Exception as e:
                st.error(f"Erreur de communication avec le serveur : {e}")

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
    
    #transcript_editor = st.text_area("Texte à analyser", value=st.session_state.transcript_text, height=250)
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

        #st.markdown("---")
        #st.subheader("Quel type de modèle d'IA utiliser ?")
       # user_choice = st.pills("Types disponibles (léger par défaut):",
       #                         ["modèle léger = > rapide mais compte-rendu moins exhaustif", "modèle lourd = > Lent mais compte-rendu très exhaustif"])
       # if user_choice == "modèle lourd = > Lent mais compte-rendu très exhaustif":
       #     chosen_model = heavy_model
       # else:
       #     chosen_model = light_model
        chosen_model = heavy_model
        #st.subheader("Paramètres de la génération")

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

            #formatype = st.radio("Source du format template", ["Manuel", "A partir d'un fichier"])
            #
            #if formatype == "Manuel":
            #    if templates:
            #        # Création d'un dictionnaire pour faciliter la sélection
            #        # Clé : Nom du template | Valeur : Les données du template (description, prompt...)
            #        options_templates = {t['nom']: t for t in templates}
#
            #        choix_utilisateur = st.selectbox(
            #            "Choisissez un type de réunion :", 
            #            options=list(options_templates.keys())
            #        )
            #        
            #        # Récupération des données du modèle choisi
            #        template_actuel = options_templates[choix_utilisateur]
            #        
            #        # Affichage d'une petite bulle d'info avec la description
            #        #st.info(template_actuel['description'])
            #    format_instructions = st.text_area("Voici le format du compte-rendu", value=template_actuel['prompt'], height=150)
#
            ##possibilité de charger le template dans un fichier json
            ##ça permet d'avoir plus de templates à disposition
            #elif formatype == "A partir d'un fichier":
            #    bf = st.file_uploader("Charger votre fichier")
            #    if bf and st.button("Convertir le fichier"):
            #        with st.spinner("Extraction du format via l'API..."):
            #            files = {"file": (bf.name, bf.getvalue(), bf.type)}
            #            data = {"chosen_model": chosen_model}
            #            res = requests.post(f"{API_URL}/create_template/", files=files, data=data)
            #            if res.status_code == 200:
            #                st.session_state.format_instructions_fichier = res.json()["template"]
            #                st.success("Fichier correctement converti en template.")
            #            else:
            #                st.error("Erreur lors de la conversion.")
#
            #    if st.session_state.format_instructions_fichier:
            #        format_instructions = st.session_state.format_instructions_fichier
            #        with st.expander("Voir le format extrait"):
            #            st.text(format_instructions)
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
                        "temperature": selected_temp,
                        "model_name": chosen_model,
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
                    "temperature": selected_temp,
                    "model_name": chosen_model,
                    "num_ctx": context_options,
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
                
                if res_docx.status_code == 200:
                    st.text("la génération du word n'est pas encore top")
                    st.text("L'option générer un résumé de réunion utilise actuellement la même structure de rédaction que le compte-rendu")
                    st.download_button(
                        label="📄 Télécharger en Word (.docx)",
                        data=res_docx.content, # Les bytes bruts du fichier Word
                        file_name="Compte_Rendu.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.error("Erreur API lors de la génération du Word.")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")
