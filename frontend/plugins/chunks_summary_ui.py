import streamlit as st
import os
import requests


API_URL = os.environ.get("API_URL", "http://localhost:8000")
DEFAULT_LLM_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "gemma4:e4b")
CHUNK_CONTEXT_SIZE = os.environ.get("CHUNK_CONTEXT_SIZE", 22000)
FULL_SUMMARY_CONTEXT_SIZE = os.environ.get("FULL_SUMMARY_CONTEXT_SIZE", 22000)
TEMPERATURE = os.environ.get("TEMPERATURE", 0.15)

CHUNK_WORDS_DEFAULT = int(os.environ.get("CHUNK_WORDS_DEFAULT", 6000)) # On passe de 300 à 6000

CHUNK_WORDS_MAX = int(os.environ.get("CHUNK_WORDS_MAX", 12000)) # Plafond haut


OVERLAP_WORDS_DEFAULT = int(os.environ.get("OVERLAP_WORDS_DEFAULT", 150)) # Légèrement augmenté pour lier les gros blocs

OVERLAP_WORDS_MAX = int(os.environ.get("OVERLAP_WORDS_MAX", 500))


from config.prompts import DEFAULT_CHUNK_SYSTEM, DEFAULT_GLOBAL_SYSTEM


def render_summarizer():

    if "prompt_chunk_system" not in st.session_state:
        st.session_state.prompt_chunk_system = DEFAULT_CHUNK_SYSTEM
    if "prompt_global_system" not in st.session_state:
        st.session_state.prompt_global_system = DEFAULT_GLOBAL_SYSTEM
    if st.session_state.transcript_text:
        st.markdown("---")
        st.write("### Génération du  Compte-rendu")
        #st.subheader("📝 Résultat de la transcription")
        
        transcript_editor = st.text_area("Texte à analyser", value=st.session_state.transcript_text, height=250)
        transcript_editor = st.session_state.transcript_text

        raw_text = transcript_editor #.read().decode("utf-8", errors="replace")

        words_list = raw_text.split()
        total_words = len(words_list)



        selected_model = DEFAULT_LLM_MODEL

 
# ── Calcul dynamique de la taille de chunk optimale ──

        if total_words <= 12000:
            # Option A : One-Shot. Le texte tient très bien dans le contexte.
            chunk_words = total_words
            overlap_words = 0

        else:
            # Option B : Macro-Chunks. On divise pour avoir des blocs d'environ 6000 mots.
            # On calcule le nombre de chunks nécessaires pour équilibrer la charge
            nb_chunks = (total_words // 6000) + 1
            
            # On répartit le texte équitablement (+ une marge de sécurité)
            chunk_words = min(int(total_words // nb_chunks) + 200, CHUNK_WORDS_MAX)
            overlap_words = OVERLAP_WORDS_DEFAULT

        # Assurons-nous que chunk_words ne dépasse JAMAIS la limite MAX
        chunk_words = min(chunk_words, CHUNK_WORDS_MAX)



    # ── Parse & chunk ─────────────────────────────────────────────────────────────

    chunks = requests.post(f"{API_URL}/split_into_chunks/", json={"text": raw_text, "chunk_size": chunk_words, "overlap": overlap_words}).json()
    if chunks != st.session_state.chunks:
        st.session_state.chunks = chunks
        st.session_state.summaries = [""] * len(chunks)
        st.session_state.current_chunk = -1
        st.session_state.global_summary = ""
        st.session_state.processing = False
        st.session_state.indices_to_process = []
        st.session_state.process_pos = 0

    n = len(chunks)

    # Déclenchement automatique si le mode automatique est activé
    if (st.session_state.get("auto_process_enabled", False) and
        not st.session_state.processing and
        n > 0 and
        all(not s for s in st.session_state.summaries)):  # Aucun résumé existant
        st.session_state.indices_to_process = list(range(n))
        st.session_state.process_pos = 0
        st.session_state.processing = True
        st.toast("🚀 Mode automatique activé - Analyse en cours...", icon="🚀")


    # ── Status bar ────────────────────────────────────────────────────────────────
    done = sum(1 for s in st.session_state.summaries if s)
    dot_class = "idle" if not st.session_state.processing else ""
    st.markdown(f"""
    <div class="status-bar">
        <span class="status-dot {dot_class}"></span>
        <span style="color:#2a2d35">|</span>
        <span>{total_words} mots</span>
        <span style="color:#2a2d35">|</span>
        <span>{n} chunks</span>
        <span style="color:#2a2d35">|</span>
        <span> Taille des chunks : {chunk_words:.0f} mots</span>
        <span style="color:#2a2d35">|</span>
        <span style="color:#87CEEB">{done}/{n} analysés</span>
    </div>
    """, unsafe_allow_html=True)


    # Détecte si une reprise est possible
    n_missing = sum(1 for s in st.session_state.summaries if not s)
    can_resume = (
        not st.session_state.processing
        and n_missing > 0
        and done > 0  # au moins un a été fait → c'est une reprise, pas un départ
    )

    col_b1, col_b2, col_b3, col_b4, _ = st.columns([1, 1, 1, 1, 1])
    with col_b1:
            # Grisé si un traitement est en cours
            run_all = st.button("▶ Analyser tout", use_container_width=True, disabled=st.session_state.processing)
        
    with col_b2:
        # Grisé si un traitement est en cours
        run_missing = st.button("⟳ Manquants", use_container_width=True, disabled=st.session_state.processing)
        
    with col_b3:
        # Combiner la logique de reprise avec le verrouillage de traitement
        resume_btn = st.button(
            f"↺ Reprendre ({n_missing})" if can_resume else "↺ Reprendre",
            use_container_width=True,
            disabled=(not can_resume) or st.session_state.processing, # <-- AJOUT ICI
            help="Reprend depuis le dernier chunk non analysé" if can_resume else "Aucune reprise disponible",
        )
        
    with col_b4:
        # Empêcher la réinitialisation pendant que ça tourne
        reset_btn = st.button("✕ Réinitialiser", use_container_width=True, disabled=st.session_state.processing)
    st.markdown('<div style="text-align: left; margin-bottom: 10px;"><a href="#compte-rendu-global" style="color: #87CEEB; text-decoration: none; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem;">👇 Aller au bas de la page une fois le traitement terminé</a></div>', unsafe_allow_html=True)

    if reset_btn:
        st.session_state.summaries = [""] * n
        st.session_state.global_summary = ""
        st.session_state.current_chunk = -1
        st.session_state.processing = False
        st.session_state.indices_to_process = []
        st.session_state.process_pos = 0
        st.rerun()

    if run_all:
        st.session_state.indices_to_process = list(range(n))
        st.session_state.summaries = [""] * n
        st.session_state.global_summary = ""
        st.session_state.process_pos = 0
        st.session_state.processing = True

    elif run_missing:
        st.session_state.indices_to_process = [
            i for i, s in enumerate(st.session_state.summaries) if not s
        ]
        st.session_state.process_pos = 0
        st.session_state.processing = True

    elif resume_btn:
        # Reprend à partir du premier chunk sans summary,
        # en respectant l'ordre original des indices
        missing = [i for i, s in enumerate(st.session_state.summaries) if not s]
        if missing:
            st.session_state.indices_to_process = missing
            st.session_state.process_pos = 0
            st.session_state.processing = True
            st.toast(f"Reprise depuis le chunk #{missing[0]+1:02d}", icon="↺")

    # Barre de progression globale affichée uniquement pendant le traitement
    if st.session_state.processing and st.session_state.indices_to_process:
        total = len(st.session_state.indices_to_process)
        current = st.session_state.process_pos
        
        # Calcul du pourcentage (sécurisé entre 0 et 100)
        progress_pct = int((current / total) * 100) if total > 0 else 0
        progress_pct = min(max(progress_pct, 0), 100)
        
        st.progress(progress_pct, text=f"⏳ Analyse en cours... ({current}/{total})")

    st.markdown("---")


    # ── Chunk rows ────────────────────────────────────────────────────────────────
    st.markdown('<div id="debut-chunks" class="col-header">📄 Extraits &nbsp;·&nbsp; 🤖 Notes</div>', unsafe_allow_html=True)

    for i, chunk in enumerate(st.session_state.chunks):
        with st.expander(f"Chunk #{i+1:02d}", expanded=True):
           # st.markdown('<div class="chunk-row">', unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="chunk-header">
                    <span class="chunk-badge">#{i+1:02d}</span>
                    <span class="chunk-label">{len(chunk.split())} mots</span>
                </div>
                """, unsafe_allow_html=True)
            col_left, col_right = st.columns([1, 1], gap="large")
            # Left — raw transcript excerpt
            with col_left:
                # Simplification des couleurs : vert si terminé, sinon gris foncé
                border_color = "#22c55e" if st.session_state.summaries[i] else "#2a2d35"
                
                st.markdown(f"""
                <div class="chunk-card" style="border-left-color:{border_color}">
                    {chunk[:600]}{'…' if len(chunk) > 600 else ''}
                </div>
                """, unsafe_allow_html=True)

            # Right — LLM summary 
            with col_right:
                summary = st.session_state.summaries[i]
                
                if not summary:
                    st.markdown('<div class="summary-pending">En attente d\'analyse…</div>', unsafe_allow_html=True)
                else:
                    edited = st.text_area(
                        f"Notes #{i+1:02d}",
                        value=summary,
                        key=f"summary_{i}",
                        height=200,
                        label_visibility="collapsed",
                    )
                    if edited != summary:
                        st.session_state.summaries[i] = edited

            st.markdown('</div>', unsafe_allow_html=True)


# ── Step-by-step processing (runs after display) ──────────────────────────────
    if st.session_state.processing and st.session_state.indices_to_process:
        idx = st.session_state.indices_to_process[st.session_state.process_pos]
        st.session_state.current_chunk = idx

        # 1. Capture the JSON dictionary from the backend
        result = requests.post(
            f"{API_URL}/summarize_chunk/", # pointe vers chunk_analysis.py
            json={
                "chunk": st.session_state.chunks[idx], 
                "model": selected_model, 
                "chunk_index": idx, 
                "total_chunks": n,
                "temperature": TEMPERATURE,      
                "model_name": selected_model,    
                "num_ctx": CHUNK_CONTEXT_SIZE,   
                "passes": 1    ,
                "custom_system_prompt": st.session_state.prompt_chunk_system,                  
            }
        ).json()
        
        # 👇 2. Extract ONLY the string from the "summary" key before saving
        if isinstance(result, dict) and "summary" in result:
            st.session_state.summaries[idx] = result["summary"]
        else:
            # Fallback in case the backend returns an error message or raw string
            st.session_state.summaries[idx] = str(result)
            
        st.session_state.process_pos += 1

        if st.session_state.process_pos >= len(st.session_state.indices_to_process):
            st.session_state.processing = False
            st.session_state.current_chunk = -1
            st.session_state.indices_to_process = []
            st.session_state.process_pos = 0

        st.rerun()


    # ── Global summary ────────────────────────────────────────────────────────────
    st.markdown("---")

    st.markdown('<div style="text-align: left; margin-bottom: 10px;"><a href="#debut-chunks" style="color: #87CEEB; text-decoration: none; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem;">▲ Remonter au début de la liste des extraits</a></div>', unsafe_allow_html=True)
    st.markdown('<div id="compte-rendu-global" class="col-header">📋 Compte-rendu global</div>', unsafe_allow_html=True)

    summaries_done = [s for s in st.session_state.summaries if s.strip()]
    n_done = len(summaries_done)

    # Accepter automatiquement le disclaimer en mode automatique
    if st.session_state.get("auto_process_enabled", False):
        disclaimer_accepted = True
        st.checkbox(
            "⚠️ En générant le compte-rendu, vous vous rendez responsable de son contenu s'il venait à être diffusé.",
            value=True,
            disabled=True
        )
    else:
        disclaimer_accepted = st.checkbox(
            "⚠️ En générant le compte-rendu, vous vous rendez responsable de son contenu s'il venait à être diffusé."
        )

    col_g1, col_g2, _ = st.columns([1.2, 1.2, 4])
    
    with col_g1:
        gen_global = st.button(
            f"✦ Générer ({n_done}/{n})",
            use_container_width=True,
            # 👇 On verrouille si : 0 résumé fini OU case non cochée OU un traitement d'analyse est en cours
            disabled=(n_done == 0) or not disclaimer_accepted or st.session_state.processing,
        )
    # Génération automatique du compte-rendu final si le mode automatique est activé
    if (st.session_state.get("auto_process_enabled", False) and
        n_done == n and n_done > 0 and  # Tous les résumés sont terminés
        not st.session_state.global_summary and  # Pas encore de compte-rendu global
        disclaimer_accepted):
        with st.spinner("Génération du compte-rendu global final..."):
            st.session_state.global_summary = requests.post(
                f"{API_URL}/generate_global_summary/", 
                json={
                    "summaries": summaries_done,
                    "model": selected_model,
                    "collection_name": st.session_state.rag_config.get("collection", "aucune_collection"),
                    "custom_system_prompt": st.session_state.prompt_global_system
                }
            ).json()
        st.toast("📋 Compte-rendu global généré automatiquement !", icon="📋")
    #with col_g2:
    #    if st.session_state.global_summary:
    #        if st.button("⬇ Afficher brut", use_container_width=True):
    #            st.code(st.session_state.global_summary, language=None)

    if gen_global and summaries_done:
        with st.spinner("Génération du compte-rendu global final..."):
            st.session_state.global_summary = requests.post(
                f"{API_URL}/generate_global_summary/", 
                json={
                    "summaries": summaries_done,
                    "model": selected_model,
                    "collection_name": st.session_state.rag_config.get("collection", "aucune_collection"),
                    "custom_system_prompt": st.session_state.prompt_global_system
                }
            ).json() # pointe vers chunk_analysis.py

    if st.session_state.global_summary:

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

        st.download_button(
            label="⬇ Télécharger le compte-rendu (.txt)",
            data=st.session_state.global_summary,
            file_name="compte_rendu_reunion.txt",
            mime="text/plain",
        )

        try:
            # Demande du DOCX au backend
            payload_docx = {"markdown_text": st.session_state.global_summary}
            res_docx = requests.post(f"{API_URL}/generate_docx/", json=payload_docx)
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