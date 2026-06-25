# frontend/pages/1_⚙️_Configuration.py

import streamlit as st

st.set_page_config(page_title="Configuration des Prompts", page_icon="⚙️", layout="wide")

st.title("⚙️ Configuration des Prompts (Session)")
st.p_description = st.markdown(
    "Modifiez ici les instructions système envoyées aux modèles locaux pour cette session. "
    "Si vous changez de page, vos modifications seront conservées tant que l'onglet reste ouvert."
)

# --- Valeurs par défaut (issues de votre chunk_analysis.py) ---
DEFAULT_CHUNK_SYSTEM = (
    "Tu es un assistant de prise de notes de réunion. On te fournit un extrait de transcription. "
    "Ta tâche : noter UNIQUEMENT ce qui est explicitement dit dans cet extrait. "
    "Rédiges les notes comme si tu assistais en direct à la réunion.\n"
    "RÈGLES ABSOLUES :\n"
    "- Ne mentionne QUE des informations présentes mot pour mot dans le texte fourni.\n"
    "- N'invente rien, ne complète pas, ne fais aucune inférence.\n"
    "- Si un point n'est pas clairement exprimé dans l'extrait, ne l'écris pas.\n"
    "- Format : bullet points courts (•), en français.\n"
    "- Si l'extrait est trop court ou peu informatif, écris simplement '• (extrait peu informatif)'."
)

DEFAULT_GLOBAL_SYSTEM = (
    "Tu es un assistant de prise de notes de réunion professionnel. "
    "On te fournit les notes chronologiques d'UNE SEULE réunion, découpée en parties pour l'analyse. "
    "Ce n'est pas plusieurs réunions : c'est une unique réunion du début à la fin. "
    "Synthétise l'ensemble en un compte-rendu global unique, en français.\n"
    "Structure attendue :\n"
    "1. Résumé exécutif (2-3 phrases)\n"
    "2. Points clés abordés\n"
    "3. Décisions prises\n"
    "4. Actions à mener (avec responsables si mentionnés)\n"
    "Ne parle jamais de 'série de réunions', 'plusieurs réunions' ou 'différentes sessions'. C'est une seule réunion."
)

DEFAULT_COMP_SYSTEM = (
    "Tu es un assistant spécialisé dans l'extraction de données factuelles. "
    "On te fournit la transcription brute d'une réunion. "
    "Ta SEULE mission : repérer et extraire les mentions d'outils, logiciels, solutions ou produits "
    "qui ont été présentés, testés ou comparés lors de cette réunion. "
    "Pour chaque outil/produit trouvé, extrais UNIQUEMENT ce qui est explicitement dit : "
    "nom, prix/coût, performance/efficacité, avantages mentionnés, inconvénients mentionnés, "
    "avis exprimés par les participants.\n"
    "RÈGLES ABSOLUES :\n"
    "- N'invente aucune donnée. Si un champ n'est pas mentionné, écris 'non mentionné'.\n"
    "- Cite les chiffres et mots exacts du texte (prix, scores, pourcentages…).\n"
    "- Si aucun outil/produit n'est comparé, réponds UNIQUEMENT : AUCUN_COMPARATIF\n"
    "- Format : une fiche par outil, séparées par ---"
)

# --- Initialisation dans le Session State ---
if "prompt_chunk_system" not in st.session_state:
    st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
if "prompt_global_system" not in st.session_state:
    st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM
if "prompt_comp_system" not in st.session_state:
    st.session_state.prompt_comp_system = DEFAULT_COMP_SYSTEM

# --- Interface utilisateur ---
tab1, tab2, tab3 = st.tabs([
    "🤖 Notes par Extrait (Chunks)", 
    "📋 Compte-rendu Global", 
    "📊 Extraction des Comparatifs"
])

with tab1:
    st.subheader("Prompt Système : Analyse des morceaux (Chunks)")
    st.session_state.prompt_chunk_system = st.text_area(
        "Instructions pour extraire les faits bruts de chaque bloc :",
        value=st.session_state.prompt_chunk_system,
        height=300,
        key="input_chunk_sys"
    )

with tab2:
    st.subheader("Prompt Système : Synthèse globale")
    st.session_state.prompt_global_system = st.text_area(
        "Instructions pour compiler tous les morceaux en compte-rendu final :",
        value=st.session_state.prompt_global_system,
        height=300,
        key="input_global_sys"
    )

with tab3:
    st.subheader("Prompt Système : Fiches Comparatives")
    st.session_state.prompt_comp_system = st.text_area(
        "Instructions pour le scan d'outils, tarifs et performances :",
        value=st.session_state.prompt_comp_system,
        height=300,
        key="input_comp_sys"
    )

# Actions globales de réinitialisation
st.markdown("---")
if st.button("🔄 Réinitialiser tous les prompts par défaut"):
    st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
    st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM
    st.session_state.prompt_comp_system = DEFAULT_COMP_SYSTEM
    st.success("Les prompts ont été réinitialisés avec succès !")
    st.rerun()