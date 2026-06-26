import streamlit as st
import re
from plugins.APIclient import list_collections

st.set_page_config(page_title="Configuration des Prompts", page_icon="⚙️", layout="wide")



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


def set_rag_stats():
    # J'assume que list_collections() est appelée correctement ici, 
    # potentiellement en lui passant ton client ChromaDB si nécessaire.
    collections_disponibles = list_collections()
    
    # Sécurité : au cas où ChromaDB est vide ou inaccessible
    if not collections_disponibles:
        s = "aucune_collection"
    else:
        # Recherche regex : on cherche "RH" (insensible à la casse grâce à re.IGNORECASE)
        # c'est-à-dire que ça matchera "rh", "RH", "documents_RH", "Rh_test", etc.
        collection_infos = next(
            (c for c in collections_disponibles if re.search(r'informations_generales', c, re.IGNORECASE)), 
            None # Valeur par défaut si rien n'est trouvé
        )
        
        # Si la regex trouve une correspondance, on l'utilise.
        # Sinon (fallback), on prend le premier élément de la liste pour ne pas faire planter l'app.
        s = collection_infos if collection_infos else collections_disponibles[0]

    return {
        "collection": s,
    }



if "prompt_chunk_system" not in st.session_state:
    st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
if "prompt_global_system" not in st.session_state:
    st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM

def render_config_page():
    st.title("⚙️ Configuration des Prompts (Session)")
    st.markdown("Modifiez ici les instructions système...")

    try:
        # 1. Récupération des collections via l'API frontend
        collections_disponibles = list_collections()

        # Si la BDD est vide, on fournit un fallback
        if not collections_disponibles:
            collections_disponibles = ["aucune_collection_trouvee"]
            st.warning("Aucune collection trouvée dans ChromaDB.")

    except Exception as e:
        # Sécurité : Si l'API est inaccessible, on évite le crash de l'UI
        st.error(f"Erreur de connexion à l'API RAG : {e}")
        collections_disponibles = [st.session_state.rag_config["collection"]]

    # 2. Gestion de l'index par défaut du selectbox
    collection_actuelle = st.session_state.rag_config["collection"]
    try:
        index_par_defaut = collections_disponibles.index(collection_actuelle)
    except ValueError:
        # Si la collection en session n'existe plus, on sélectionne la première de la liste
        index_par_defaut = 0

    # 3. Affichage du menu déroulant
    st.session_state.rag_config["collection"] = st.selectbox(
        "Collection ChromaDB", 
        options=collections_disponibles,
        index=index_par_defaut
        )
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