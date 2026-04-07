import streamlit as st
import requests
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

def get_loaded_models():
    """Récupère les modèles actuellement en mémoire."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/ps", timeout=5)
        response.raise_for_status()
        return response.json().get("models", [])
    except Exception as e:
        st.error(f"Erreur : {e}")
        return []

def unload_model(model_name):
    """Force le déchargement d'un modèle."""
    try:
        requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model_name, "keep_alive": 0, "prompt": ""},
            timeout=10
        )
        return True
    except Exception as e:
        st.error(f"Erreur : {e}")
        return False

# --- UI ---
st.subheader("🧠 Modèles Ollama en mémoire")

loaded = get_loaded_models()

if not loaded:
    st.info("Aucun modèle en mémoire.")
else:
    for m in loaded:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(m["name"])
        col2.write(f"{round(m.get('size', 0) / 1e9, 2)} Go")
        if col3.button("🗑️ Libérer", key=m["name"]):
            if unload_model(m["name"]):
                st.success(f"`{m['name']}` déchargé !")
                st.rerun()

if loaded and st.button("🗑️ Tout libérer", type="primary"):
    for m in loaded:
        unload_model(m["name"])
    st.success("Tous les modèles ont été déchargés !")
    st.rerun()