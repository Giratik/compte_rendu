import streamlit as st
import requests
import json
import re
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Notes AI",
    page_icon="📋",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Background */
.stApp {
    background-color: #0d0f14;
    color: #e8e4dc;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }

/* Title block */
.title-block {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #2a2d35;
    margin-bottom: 2rem;
}
.title-block h1 {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #e8e4dc;
    margin: 0;
}
.title-block span {
    color: #f0c040;
}
.title-block p {
    color: #6b7280;
    font-size: 0.9rem;
    margin: 0.4rem 0 0 0;
    font-family: 'JetBrains Mono', monospace;
}

/* Chunk card */
.chunk-card {
    background: #13161d;
    border: 1px solid #2a2d35;
    border-left: 3px solid #f0c040;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9ca3af;
    line-height: 1.7;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
}
.chunk-card::-webkit-scrollbar { width: 4px; }
.chunk-card::-webkit-scrollbar-track { background: #13161d; }
.chunk-card::-webkit-scrollbar-thumb { background: #2a2d35; border-radius: 2px; }

/* Chunk header */
.chunk-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.8rem;
}
.chunk-badge {
    background: #f0c040;
    color: #0d0f14;
    font-size: 0.65rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.05em;
}
.chunk-label {
    color: #4b5563;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
}

/* Summary box */
.summary-pending {
    background: #13161d;
    border: 1px dashed #2a2d35;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    color: #4b5563;
    font-size: 0.82rem;
    font-style: italic;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: 80px;
}

/* Status bar */
.status-bar {
    background: #13161d;
    border: 1px solid #2a2d35;
    border-radius: 6px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #6b7280;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22c55e;
    display: inline-block;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.status-dot.idle { background: #4b5563; animation: none; }

/* Column headers */
.col-header {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4b5563;
    font-family: 'JetBrains Mono', monospace;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #2a2d35;
    margin-bottom: 1.2rem;
}

/* Global summary */
.global-summary-box {
    background: #13161d;
    border: 1px solid #f0c040;
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 1rem;
}

/* Streamlit overrides */
.stTextArea textarea {
    background: #1a1d24 !important;
    border: 1px solid #2a2d35 !important;
    border-radius: 6px !important;
    color: #e8e4dc !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTextArea textarea:focus {
    border-color: #f0c040 !important;
    box-shadow: 0 0 0 1px #f0c040 !important;
}
.stButton button {
    background: #f0c040 !important;
    color: #0d0f14 !important;
    border: none !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.03em !important;
    border-radius: 5px !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton button:hover {
    background: #ffd700 !important;
}
.stFileUploader {
    background: #13161d !important;
    border: 1px dashed #2a2d35 !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploaderDropzone"] {
    background: #13161d !important;
}
.stSlider [data-baseweb="slider"] {
    background: transparent !important;
}
.stExpander {
    background: #13161d !important;
    border: 1px solid #2a2d35 !important;
    border-radius: 6px !important;
}
.stExpander summary {
    color: #e8e4dc !important;
}
label, .stSelectbox label, .stSlider label {
    color: #9ca3af !important;
    font-size: 0.8rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stSelectbox div[data-baseweb="select"] {
    background: #13161d !important;
    border-color: #2a2d35 !important;
}
.stMarkdown hr {
    border-color: #2a2d35 !important;
}
div[data-testid="stVerticalBlock"] > div > div > div[data-testid="column"] {
    border-right: 1px solid #2a2d35;
    padding-right: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://10.75.12.10:11434"

# ── Helpers ───────────────────────────────────────────────────────────────────

def remove_timestamps(text: str) -> str:
    """Remove common timestamp formats from transcription."""
    # HH:MM:SS or HH:MM
    text = re.sub(r'\[?\d{1,2}:\d{2}(:\d{2})?\]?', '', text)
    # Speaker labels like "John Doe: " or "[00:01] John:"
    text = re.sub(r'\[\d{1,2}:\d{2}\]\s*', '', text)
    return text.strip()


def split_into_chunks(text: str, chunk_size: int, overlap: int = 50) -> list[str]:
    """Split text into word-based chunks with optional overlap."""
    words = text.split()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def list_ollama_models() -> list[str]:
    """Fetch available models from Ollama."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return models if models else ["llama3", "mistral", "gemma"]
    except Exception:
        pass
    return ["llama3", "mistral", "gemma"]


def summarize_chunk(chunk: str, model: str, chunk_index: int, total_chunks: int) -> str:
    """Call Ollama to summarize a chunk, streaming the result."""
    system_prompt = (
        "Tu es un assistant de prise de notes de réunion. "
        "On te fournit un extrait de transcription. "
        "Ta tâche : noter UNIQUEMENT ce qui est explicitement dit dans cet extrait. "
        "RÈGLES ABSOLUES :\n"
        "- Ne mentionne QUE des informations présentes mot pour mot dans le texte fourni.\n"
        "- N'invente rien, ne complète pas, ne fais aucune inférence.\n"
        "- Si un point n'est pas clairement exprimé dans l'extrait, ne l'écris pas.\n"
        "- Format : bullet points courts (•), en français.\n"
        "- Si l'extrait est trop court ou peu informatif, écris simplement '• (extrait peu informatif)'."
    )
    user_prompt = (
        f"Voici l'extrait {chunk_index + 1} sur {total_chunks} de la transcription d'une réunion :\n\n"
        f"---\n{chunk}\n---\n\n"
        "Note uniquement ce qui est dit dans CET extrait, rien d'autre."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120,
        )
        if r.status_code == 200:
            return r.json()["message"]["content"].strip()
        return f"⚠️ Erreur {r.status_code}: {r.text[:200]}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Impossible de joindre Ollama (10.75.12.10:11434)"
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


def generate_global_summary(summaries: list[str], model: str) -> str:
    """Generate a global summary from all chunk summaries."""
    combined = "\n\n".join(
        [f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)]
    )
    system_prompt = (
        "Tu es un assistant de prise de notes de réunion professionnel. "
        "On te fournit les notes chronologiques d'UNE SEULE réunion, découpée en parties pour l'analyse. "
        "Ce n'est pas plusieurs réunions : c'est une unique réunion du début à la fin. "
        "Synthétise l'ensemble en un compte-rendu global unique, en français. "
        "Structure attendue :\n"
        "1. Résumé exécutif (2-3 phrases)\n"
        "2. Points clés abordés\n"
        "3. Décisions prises\n"
        "4. Actions à mener (avec responsables si mentionnés)\n"
        "Ne parle jamais de 'série de réunions', 'plusieurs réunions' ou 'différentes sessions'. "
        "C'est une seule réunion."
    )
    user_prompt = (
        f"Voici les notes prises au fil de la réunion (en {len(summaries)} parties chronologiques) :\n\n"
        f"{combined}\n\n"
        "Rédige le compte-rendu de cette réunion."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
        if r.status_code == 200:
            return r.json()["message"]["content"].strip()
        return f"⚠️ Erreur {r.status_code}"
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


def extract_comparisons(chunks: list, model: str) -> str:
    """Scan all raw chunks for tool/product comparisons and return structured extraction."""
    full_text = "\n\n".join([f"[Extrait {i+1}]\n{c}" for i, c in enumerate(chunks)])
    system_prompt = (
        "Tu es un assistant spécialisé dans l'extraction de données factuelles. "
        "On te fournit la transcription brute d'une réunion. "
        "Ta SEULE mission : repérer et extraire les mentions d'outils, logiciels, solutions ou produits "
        "qui ont été présentés, testés ou comparés lors de cette réunion. "
        "Pour chaque outil/produit trouvé, extrais UNIQUEMENT ce qui est explicitement dit : "
        "nom, prix/coût, performance/efficacité, avantages mentionnés, inconvénients mentionnés, "
        "avis exprimés par les participants. "
        "RÈGLES ABSOLUES :\n"
        "- N'invente aucune donnée. Si un champ n'est pas mentionné, écris 'non mentionné'.\n"
        "- Cite les chiffres et mots exacts du texte (prix, scores, pourcentages…).\n"
        "- Si aucun outil/produit n'est comparé, réponds UNIQUEMENT : AUCUN_COMPARATIF\n"
        "- Format : une fiche par outil, séparées par ---"
    )
    user_prompt = (
        f"Transcription complète :\n\n---\n{full_text}\n---\n\n"
        "Extrais les fiches comparatives. Si aucun outil n'est comparé, réponds uniquement AUCUN_COMPARATIF."
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ], "stream": False},
            timeout=300,
        )
        if r.status_code == 200:
            result = r.json()["message"]["content"].strip()
            return "" if "AUCUN_COMPARATIF" in result else result
        return ""
    except Exception:
        return ""


def generate_global_summary_with_comparisons(summaries: list, comparisons: str, model: str) -> str:
    """Generate a global summary that includes a dedicated comparisons section if present."""
    combined = "\n\n".join([f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)])
    comparisons_block = (
        f"\n\n=== DONNÉES COMPARATIVES (outils/produits testés — données brutes à conserver) ===\n{comparisons}\n==="
        if comparisons else ""
    )
    section_5 = (
        "5. Comparatif des outils/solutions évalués — reprends les données chiffrées telles quelles "
        "(prix, scores, avantages, inconvénients, verdict des participants), sans les résumer ni les arrondir.\n"
        if comparisons else ""
    )
    system_prompt = (
        "Tu es un assistant de prise de notes de réunion professionnel. "
        "On te fournit les notes chronologiques d'UNE SEULE réunion et, le cas échéant, "
        "une extraction factuelle des outils/produits comparés. "
        "Ce n'est pas plusieurs réunions : c'est une unique réunion du début à la fin. "
        "Synthétise en un compte-rendu structuré en français.\n"
        "Structure OBLIGATOIRE :\n"
        "1. Résumé exécutif (2-3 phrases)\n"
        "2. Points clés abordés\n"
        "3. Décisions prises\n"
        "4. Actions à mener (responsables si mentionnés)\n"
        + section_5 +
        "Ne parle jamais de 'série de réunions' ou 'plusieurs réunions'. "
        "Pour la section comparatif, recopie fidèlement les données chiffrées sans les compresser."
    )
    user_prompt = (
        f"Notes chronologiques ({len(summaries)} parties) :\n\n{combined}"
        f"{comparisons_block}\n\nRédige le compte-rendu complet."
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ], "stream": False},
            timeout=240,
        )
        if r.status_code == 200:
            return r.json()["message"]["content"].strip()
        return f"⚠️ Erreur {r.status_code}"
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


# ── Session state init ────────────────────────────────────────────────────────
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "summaries" not in st.session_state:
    st.session_state.summaries = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "global_summary" not in st.session_state:
    st.session_state.global_summary = ""
if "current_chunk" not in st.session_state:
    st.session_state.current_chunk = -1

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1>Meeting <span>Notes</span> AI</h1>
    <p>→ transcription → chunks → analyse ollama → compte-rendu</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar config ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="col-header">⚙ Configuration</div>', unsafe_allow_html=True)

    # Fetch models
    with st.spinner("Chargement des modèles…"):
        available_models = list_ollama_models()

    selected_model = st.selectbox(
        "Modèle Ollama",
        options=available_models,
        index=0,
    )

    chunk_words = st.slider(
        "Taille des chunks (mots)",
        min_value=100,
        max_value=800,
        value=300,
        step=50,
    )

    overlap_words = st.slider(
        "Chevauchement (mots)",
        min_value=0,
        max_value=100,
        value=30,
        step=10,
    )

    remove_ts = st.checkbox("Supprimer les timestamps", value=True)

    st.markdown("---")
    st.markdown('<div style="color:#4b5563;font-size:0.7rem;font-family:\'JetBrains Mono\',monospace;">Ollama @ 10.75.12.10:11434</div>', unsafe_allow_html=True)

    # Connection check
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            st.markdown('<div style="color:#22c55e;font-size:0.7rem;font-family:\'JetBrains Mono\',monospace;">● connecté</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#ef4444;font-size:0.7rem;font-family:\'JetBrains Mono\',monospace;">● erreur connexion</div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<div style="color:#ef4444;font-size:0.7rem;font-family:\'JetBrains Mono\',monospace;">● hors ligne</div>', unsafe_allow_html=True)

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Déposez votre transcription (.txt)",
    type=["txt"],
    label_visibility="collapsed",
)

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8", errors="replace")

    if remove_ts:
        clean_text = remove_timestamps(raw_text)
    else:
        clean_text = raw_text

    chunks = split_into_chunks(clean_text, chunk_words, overlap_words)

    # Reset if file changed
    if chunks != st.session_state.chunks:
        st.session_state.chunks = chunks
        st.session_state.summaries = [""] * len(chunks)
        st.session_state.current_chunk = -1
        st.session_state.global_summary = ""

    n = len(chunks)

    # Status bar
    done = sum(1 for s in st.session_state.summaries if s)
    st.markdown(f"""
    <div class="status-bar">
        <span class="status-dot {'idle' if not st.session_state.processing else ''}"></span>
        <span>{uploaded_file.name}</span>
        <span style="color:#2a2d35">|</span>
        <span>{len(raw_text):,} caractères</span>
        <span style="color:#2a2d35">|</span>
        <span>{n} chunks</span>
        <span style="color:#2a2d35">|</span>
        <span style="color:#f0c040">{done}/{n} analysés</span>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    col_b1, col_b2, col_b3, _ = st.columns([1, 1, 1, 4])
    with col_b1:
        run_all = st.button("▶ Analyser tout", use_container_width=True)
    with col_b2:
        run_missing = st.button("⟳ Manquants", use_container_width=True)
    with col_b3:
        reset_btn = st.button("✕ Réinitialiser", use_container_width=True)

    if reset_btn:
        st.session_state.summaries = [""] * len(chunks)
        st.session_state.global_summary = ""
        st.session_state.current_chunk = -1
        st.rerun()

    # ── Processing ────────────────────────────────────────────────────────────
    if run_all:
        indices_to_process = list(range(n))
        st.session_state.summaries = [""] * n
        st.session_state.global_summary = ""
    elif run_missing:
        indices_to_process = [i for i, s in enumerate(st.session_state.summaries) if not s]
    else:
        indices_to_process = []

    if indices_to_process:
        st.session_state.processing = True
        progress_bar = st.progress(0, text="Initialisation…")

        for pos, idx in enumerate(indices_to_process):
            st.session_state.current_chunk = idx
            progress_bar.progress(
                (pos + 1) / len(indices_to_process),
                text=f"Analyse chunk {idx + 1}/{n}…"
            )
            result = summarize_chunk(
                st.session_state.chunks[idx],
                selected_model,
                idx,
                n,
            )
            st.session_state.summaries[idx] = result

        st.session_state.processing = False
        st.session_state.current_chunk = -1
        progress_bar.empty()
        st.rerun()

    st.markdown("---")

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="col-header">📄 Extraits de la transcription</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="col-header">🤖 Notes générées par le LLM</div>', unsafe_allow_html=True)

    # Render each chunk pair
    for i, chunk in enumerate(st.session_state.chunks):
        with col_left:
            # Chunk card
            is_active = (st.session_state.current_chunk == i)
            border_color = "#f0c040" if is_active else "#2a2d35" if not st.session_state.summaries[i] else "#22c55e"
            st.markdown(f"""
            <div class="chunk-header">
                <span class="chunk-badge">#{i+1:02d}</span>
                <span class="chunk-label">{len(chunk.split())} mots</span>
                {'<span style="color:#f0c040;font-size:0.7rem;font-family:\'JetBrains Mono\',monospace;">⟳ en cours…</span>' if is_active else ''}
            </div>
            <div class="chunk-card" style="border-left-color:{border_color}">{chunk[:600]}{'…' if len(chunk) > 600 else ''}</div>
            """, unsafe_allow_html=True)

        with col_right:
            summary = st.session_state.summaries[i]
            if not summary and st.session_state.current_chunk == i:
                st.markdown('<div class="summary-pending">⟳ Analyse en cours…</div>', unsafe_allow_html=True)
            elif not summary:
                st.markdown('<div class="summary-pending">En attente d\'analyse…</div>', unsafe_allow_html=True)
            else:
                # Editable text area
                edited = st.text_area(
                    f"Notes #{i+1:02d}",
                    value=summary,
                    key=f"summary_{i}",
                    height=200,
                    label_visibility="collapsed",
                )
                if edited != summary:
                    st.session_state.summaries[i] = edited

        # Separator between chunks
        if i < n - 1:
            st.markdown('<div style="border-bottom:1px solid #1e2128;margin:0.8rem 0 1.2rem 0"></div>', unsafe_allow_html=True)

    # ── Global summary ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="col-header">📋 Compte-rendu global</div>', unsafe_allow_html=True)

    summaries_done = [s for s in st.session_state.summaries if s.strip()]
    n_done = len(summaries_done)

    col_g1, col_g2, _ = st.columns([1.2, 1.2, 4])
    with col_g1:
        gen_global = st.button(
            f"✦ Générer ({n_done}/{n})",
            use_container_width=True,
            disabled=(n_done == 0),
        )
    with col_g2:
        if st.session_state.global_summary:
            if st.button("⬇ Copier le texte", use_container_width=True):
                st.code(st.session_state.global_summary, language=None)

    if gen_global and summaries_done:
        with st.spinner("Génération du compte-rendu global…"):
            st.session_state.global_summary = generate_global_summary(summaries_done, selected_model)

    if st.session_state.global_summary:
        st.markdown('<div class="global-summary-box">', unsafe_allow_html=True)
        edited_global = st.text_area(
            "Compte-rendu global (modifiable)",
            value=st.session_state.global_summary,
            height=350,
            key="global_edit",
            label_visibility="collapsed",
        )
        if edited_global != st.session_state.global_summary:
            st.session_state.global_summary = edited_global
        st.markdown('</div>', unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="⬇ Télécharger le compte-rendu (.txt)",
            data=st.session_state.global_summary,
            file_name="compte_rendu_reunion.txt",
            mime="text/plain",
        )

else:
    # Empty state
    st.markdown("""
    <div style="
        text-align:center;
        padding: 5rem 2rem;
        color: #2a2d35;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    ">
        <div style="font-size:3rem;margin-bottom:1rem;opacity:0.3">📋</div>
        <div>Déposez un fichier .txt pour commencer</div>
        <div style="font-size:0.7rem;margin-top:0.5rem;color:#1e2128">
            Formats supportés : transcription brute, avec timestamps HH:MM:SS, [HH:MM]
        </div>
    </div>
    """, unsafe_allow_html=True)