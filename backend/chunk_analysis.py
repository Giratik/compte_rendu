"""
Chunk analysis and processing functions for meeting transcriptions.
Handles text splitting, summarization, and report generation.
"""

import re
from ollama_client import inferring_ollama


# ── Text processing ────────────────────────────────────────────────────────────

def remove_timestamps(text: str) -> str:
    """Remove common timestamp formats from a transcription."""
    text = re.sub(r'\[?\d{1,2}:\d{2}(:\d{2})?\]?', '', text)
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


# ── LLM tasks ─────────────────────────────────────────────────────────────────

def summarize_chunk(chunk: str, model: str, chunk_index: int, total_chunks: int) -> str:
    """Summarize a single transcript chunk as live meeting notes."""
    system = (
        "Tu es un assistant de prise de notes de réunion. "
        "On te fournit un extrait de transcription. "
        "Ta tâche : noter UNIQUEMENT ce qui est explicitement dit dans cet extrait. "
        "Rédiges les notes comme si tu assistais en direct à la réunion"
        "RÈGLES ABSOLUES :\n"
        "- Ne mentionne QUE des informations présentes mot pour mot dans le texte fourni.\n"
        "- N'invente rien, ne complète pas, ne fais aucune inférence.\n"
        "- Si un point n'est pas clairement exprimé dans l'extrait, ne l'écris pas.\n"
        "- Format : bullet points courts (•), en français.\n"
        "- Si l'extrait est trop court ou peu informatif, écris simplement '• (extrait peu informatif)'."
    )
    user = (
        f"Voici l'extrait {chunk_index + 1} sur {total_chunks} de la transcription d'une réunion :\n\n"
        f"---\n{chunk}\n---\n\n"
        "Note uniquement ce qui est dit dans CET extrait, rien d'autre."
    )
    try:
        return inferring_ollama(model, system, user, timeout=120)
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


def extract_comparisons(chunks: list[str], model: str) -> str:
    """
    Scan all raw chunks for tool/product comparisons (price, efficiency, etc.).
    Returns a structured extraction, or empty string if nothing found.
    """
    full_text = "\n\n".join([f"[Extrait {i+1}]\n{c}" for i, c in enumerate(chunks)])
    system = (
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
    user = (
        f"Transcription complète :\n\n---\n{full_text}\n---\n\n"
        "Extrais les fiches comparatives. "
        "Si aucun outil n'est comparé, réponds uniquement AUCUN_COMPARATIF."
    )
    try:
        result = inferring_ollama(model, system, user, timeout=300)
        return "" if "AUCUN_COMPARATIF" in result else result
    except Exception:
        return ""


def generate_global_summary(summaries: list[str], model: str) -> str:
    """Generate a global meeting summary from chunk summaries."""
    combined = "\n\n".join(
        [f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)]
    )
    system = (
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
    user = (
        f"Voici les notes prises au fil de la réunion (en {len(summaries)} parties chronologiques) :\n\n"
        f"{combined}\n\n"
        "Rédige le compte-rendu de cette réunion."
    )
    
    # 👇 1. Format the messages into the list-of-dicts format Ollama expects
    formatted_messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
    
    try:
        # 👇 2. Pass arguments properly by keyword to avoid positional mismatch
        response = inferring_ollama(messages=formatted_messages, model=model)
        return response.message.content # Extrait le texte de l'objet réponse Ollama
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


def generate_global_summary_with_comparisons(summaries: list[str], comparisons: str, model: str) -> str:
    """
    Generate a global meeting summary from chunk summaries.
    If comparisons is non-empty, a dedicated section is appended with raw figures preserved.
    """
    combined = "\n\n".join(
        [f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)]
    )
    comparisons_block = (
        f"\n\n=== DONNÉES COMPARATIVES (outils/produits testés — données brutes à conserver) ===\n"
        f"{comparisons}\n==="
        if comparisons else ""
    )
    section_5 = (
        "5. Comparatif des outils/solutions évalués — reprends les données chiffrées telles quelles "
        "(prix, scores, avantages, inconvénients, verdict des participants), sans les résumer ni les arrondir.\n"
        if comparisons else ""
    )
    system = (
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
    user = (
        f"Notes chronologiques ({len(summaries)} parties) :\n\n{combined}"
        f"{comparisons_block}\n\nRédige le compte-rendu complet."
    )
    
    # 👇 1. Format the messages into the list-of-dicts format Ollama expects
    formatted_messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
    
    try:
        # 👇 2. Pass arguments properly by keyword to avoid positional mismatch
        response = inferring_ollama(messages=formatted_messages, model=model)
        return response.message.content # Extrait le texte de l'objet réponse Ollama
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"