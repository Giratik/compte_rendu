import streamlit as st

st.set_page_config(page_title="Configuration des Prompts", page_icon="⚙️", layout="wide")

st.title("⚙️ Configuration des Prompts (Session)")
st.markdown("Modifiez ici les instructions système...")

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

# LE NOUVEAU PROMPT GLOBAL FUSIONNÉ
DEFAULT_GLOBAL_SYSTEM = (
    "Tu es un assistant de prise de notes de réunion professionnel. "
    "On te fournit les notes chronologiques d'UNE SEULE réunion, découpée en parties pour l'analyse. "
    "Synthétise l'ensemble en un compte-rendu global unique, en français.\n\n"
    "Structure attendue :\n"
    "1. Résumé exécutif (2-3 phrases)\n"
    "2. Points clés abordés\n"
    "3. Décisions prises\n"
    "4. Actions à mener (avec responsables si mentionnés)\n"
    "5. Outils et Solutions (OPTIONNEL : À inclure UNIQUEMENT si des logiciels, produits, tarifs ou performances sont explicitement présentés ou comparés. Extraire les prix et avis mentionnés. Si aucun outil n'est mentionné, NE CRÉE PAS cette section).\n\n"
    "RÈGLE ABSOLUE : Ne parle jamais de 'série de réunions'. C'est une unique réunion."
)

if "prompt_chunk_system" not in st.session_state:
    st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
if "prompt_global_system" not in st.session_state:
    st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM

# Interface utilisateur simplifiée (2 onglets)
tab1, tab2 = st.tabs(["🤖 Notes par Extrait (Chunks)", "📋 Compte-rendu Global"])

with tab1:
    st.subheader("Prompt Système : Analyse des morceaux (Chunks)")
    st.session_state.prompt_chunk_system = st.text_area(
        "Instructions pour extraire les faits bruts :",
        value=st.session_state.prompt_chunk_system,
        height=300
    )

with tab2:
    st.subheader("Prompt Système : Synthèse globale")
    st.session_state.prompt_global_system = st.text_area(
        "Instructions pour la synthèse (inclut désormais la détection conditionnelle des produits) :",
        value=st.session_state.prompt_global_system,
        height=300
    )

st.markdown("---")
if st.button("🔄 Réinitialiser tous les prompts par défaut"):
    st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
    st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM
    st.success("Les prompts ont été réinitialisés avec succès !")
    st.rerun()