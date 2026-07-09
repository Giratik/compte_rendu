#backend/minutes_redactor_tools/functions_folder/chunk_analysis.py

"""
Chunk analysis and processing functions for meeting transcriptions.
Handles text splitting, summarization, and report generation.
"""

from typing import Optional
import re
from rag_communication.core import CONTEXT_SIZE
from minutes_redactor_tools.functions_folder.ollama_client import inferring_ollama


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

async def summarize_chunk(chunk: str, model: str, chunk_index: int, total_chunks: int, custom_system_prompt: Optional[str] = None) -> str:
    # Use custom system prompt if provided, otherwise use default
    if custom_system_prompt:
        system_content = custom_system_prompt
    else:
        system_content = (
            "Tu es un assistant de prise de notes de réunion. "
            "On te fournit un extrait de transcription. "
            "Ta tâche : noter UNIQUEMENT ce qui est explicitement dit dans cet extrait. "
            "Rédiges les notes comme si tu assistais en direct à la réunion. "
            "RÈGLES ABSOLUES :\n"
            "- Ne mentionne QUE des informations présentes mot pour mot dans le texte fourni.\n"
            "- N'invente rien, ne complète pas, ne fais aucune inférence.\n"
            "- Si un point n'est pas clairement exprimé dans l'extrait, ne l'écris pas.\n"
            "- Format : bullet points courts (•), en français.\n"
            "- Si l'extrait est trop court ou peu informatif, écris simplement '• (extrait peu informatif)'."
        )

    messages = [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                f"Voici l'extrait {chunk_index + 1} sur {total_chunks} de la transcription d'une réunion :\n\n"
                f"---\n{chunk}\n---\n\n"
                "Note uniquement ce qui est dit dans CET extrait, rien d'autre."
            )
        }
    ]
    try:
        response = await inferring_ollama(messages, model, context_size=CONTEXT_SIZE)
        return response.message.content
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


#async def extract_comparisons(chunks: list[str], model: str) -> str:
#    full_text = "\n\n".join([f"[Extrait {i+1}]\n{c}" for i, c in enumerate(chunks)])
#    messages = [
#        {
#            "role": "system",
#            "content": (
#                "Tu es un assistant spécialisé dans l'extraction de données factuelles. "
#                "On te fournit la transcription brute d'une réunion. "
#                "Ta SEULE mission : repérer et extraire les mentions d'outils, logiciels, solutions ou produits "
#                "qui ont été présentés, testés ou comparés lors de cette réunion. "
#                "Pour chaque outil/produit trouvé, extrais UNIQUEMENT ce qui est explicitement dit : "
#                "nom, prix/coût, performance/efficacité, avantages mentionnés, inconvénients mentionnés, "
#                "avis exprimés par les participants. "
#                "RÈGLES ABSOLUES :\n"
#                "- N'invente aucune donnée. Si un champ n'est pas mentionné, écris 'non mentionné'.\n"
#                "- Cite les chiffres et mots exacts du texte (prix, scores, pourcentages…).\n"
#                "- Si aucun outil/produit n'est comparé, réponds UNIQUEMENT : AUCUN_COMPARATIF\n"
#                "- Format : une fiche par outil, séparées par ---"
#            )
#        },
#        {
#            "role": "user",
#            "content": (
#                f"Transcription complète :\n\n---\n{full_text}\n---\n\n"
#                "Extrais les fiches comparatives. "
#                "Si aucun outil n'est comparé, réponds uniquement AUCUN_COMPARATIF."
#            )
#        }
#    ]
#    try:
#        response = await inferring_ollama(messages, model)
#        result = response.message.content
#        return "" if "AUCUN_COMPARATIF" in result else result
#    except Exception:
#        return ""


async def generate_global_summary(summaries: list[str], model: str, custom_system_prompt: Optional[str] = None) -> str:
    combined = "\n\n".join(
        [f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)]
    )

    # Use custom system prompt if provided, otherwise use default
    if custom_system_prompt:
        system_content = custom_system_prompt
    else:
        system_content = (
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

    messages = [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                f"Voici les notes prises au fil de la réunion (en {len(summaries)} parties chronologiques) :\n\n"
                f"{combined}\n\n"
                "Rédige le compte-rendu de cette réunion."
            )
        }
    ]
    try:
        response = await inferring_ollama(messages, model, context_size=CONTEXT_SIZE)
        return response.message.content
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"


#async def generate_global_summary_with_comparisons(summaries: list[str], comparisons: str, model: str) -> str:
#    combined = "\n\n".join(
#        [f"[Partie {i+1}/{len(summaries)}]\n{s}" for i, s in enumerate(summaries)]
#    )
#    comparisons_block = (
#        f"\n\n=== DONNÉES COMPARATIVES (outils/produits testés — données brutes à conserver) ===\n"
#        f"{comparisons}\n==="
#        if comparisons else ""
#    )
#    section_5 = (
#        "5. Comparatif des outils/solutions évalués — reprends les données chiffrées telles quelles "
#        "(prix, scores, avantages, inconvénients, verdict des participants), sans les résumer ni les arrondir.\n"
#        if comparisons else ""
#    )
#    messages = [
#        {
#            "role": "system",
#            "content": (
#                "Tu es un assistant de prise de notes de réunion professionnel. "
#                "On te fournit les notes chronologiques d'UNE SEULE réunion et, le cas échéant, "
#                "une extraction factuelle des outils/produits comparés. "
#                "Ce n'est pas plusieurs réunions : c'est une unique réunion du début à la fin. "
#                "Synthétise en un compte-rendu structuré en français.\n"
#                "Structure OBLIGATOIRE :\n"
#                "1. Résumé exécutif (2-3 phrases)\n"
#                "2. Points clés abordés\n"
#                "3. Décisions prises\n"
#                "4. Actions à mener (responsables si mentionnés)\n"
#                + section_5 +
#                "Ne parle jamais de 'série de réunions' ou 'plusieurs réunions'. "
#                "Pour la section comparatif, recopie fidèlement les données chiffrées sans les compresser."
#            )
#        },
#        {
#            "role": "user",
#            "content": (
#                f"Notes chronologiques ({len(summaries)} parties) :\n\n{combined}"
#                f"{comparisons_block}\n\nRédige le compte-rendu complet."
#            )
#        }
#    ]
#    try:
#        response = await inferring_ollama(messages, model)
#        return response.message.content
#    except Exception as e:
#        return f"⚠️ Erreur: {str(e)}"
    





#import PyPDF2
#import docx
#
#def extract_text(bf):
#    """Fonction utilitaire pour lire le texte d'un PDF ou d'un Word"""
#    text = ""
#    filename = bf.name.lower()
#    
#    try:
#        if filename.endswith(".pdf"):
#            pdf_reader = PyPDF2.PdfReader(bf)
#            for page in pdf_reader.pages:
#                text += page.extract_text() + "\n"
#                
#        elif filename.endswith((".docx", ".doc")):
#            doc = docx.Document(bf)
#            for para in doc.paragraphs:
#                text += para.text + "\n"
#    except Exception as e:
#        return f"Erreur de lecture : {str(e)}"
#        
#    return text
#
#
#def creation_template_from_file(bf, selected_model):
#    """
#    Lit un document de référence et utilise le LLM pour en extraire 
#    un template réutilisable (structure, ton, formatage).
#    """
#    # 1. On extrait le contenu brut du fichier
#    reference_text = extract_text(bf)
#    
#    # 2. On prépare le prompt pour demander au LLM d'extraire la structure
#    prompt_extraction = f"""
#    Voici un compte-rendu de réunion existant :
#    
#    {reference_text}
#    
#    Ta tâche : Analyse ce document et extrais-en un modèle (template) vide et des règles de formatage.
#    - Identifie les grandes parties (ex: Titre, Participants, Ordre du jour, Décisions, Actions à suivre).
#    - Identifie le style (puces, tableaux, style formel ou relâché).
#    - NE GARDE PAS le contenu spécifique de cette réunion (efface les noms, dates et sujets précis).
#    - Rédige ton résultat sous forme d'instructions claires que je pourrai donner à un assistant pour formater de futurs comptes-rendus.
#    
#    Réponds UNIQUEMENT avec la structure vide et les consignes de rédaction, sans texte d'introduction.
#    """
#    
#    # 3. On appelle Ollama (en mode non-streamé si possible, car c'est une tâche de fond)
#    message = [{"role": "user", "content": prompt_extraction}]
#    
#    # Si ta fonction inferring_ollama fait du stream par défaut, on peut tout récupérer dans une variable
#    #generateur = inferring_ollama(messages=messages, model=selected_model, stream=True)
#
#    response = inferring_ollama(
#        messages=message,
#        model=selected_model,
#        seed = 12345,
#        stream = False,
#        #timeout_s=120,
#        )
#    return response["message"]["content"]
#    
#    #template_genere = ""
#    #for chunk in generateur:
#    #    template_genere += chunk
#    #    
#    #return template_genere





from rag_communication.rag_engine import make_chroma_client, get_collection #

async def generate_global_summary_with_rag(summaries: list[str], model: str, collection_name: str, custom_system_prompt: Optional[str] = None) -> str:
    combined_notes = "\n\n".join([f"[Partie {i+1}]\n{s}" for i, s in enumerate(summaries)])

    context_rag = ""
    # 1. Interrogation de ChromaDB si une collection valide est sélectionnée
    if collection_name and collection_name != "aucune_collection":
        try:
            chroma_client = make_chroma_client() #
            collection = get_collection(chroma_client, collection_name) #

            # On utilise les notes combinées comme texte de requête
            results = collection.query(
                query_texts=[combined_notes[:5000]], # On limite la taille de la requête
                n_results=3
            )

            if results and 'documents' in results and results['documents'][0]:
                context_rag = "\n---\n".join(results['documents'][0])
        except Exception as e:
            print(f"Erreur lors de la récupération RAG : {e}")

    # 2. Construction des messages pour le LLM
    # Use custom system prompt if provided, otherwise use default
    if custom_system_prompt:
        system_content = custom_system_prompt
    else:
        system_content = (
            "Tu es un assistant de prise de notes de réunion professionnel.\n"
            "Tu dois rédiger un compte-rendu unique, structuré et fidèle.\n\n"
            "DIRECTIVE CRITIQUE SUR LE CONTEXTE DOCUMENTAIRE :\n"
            "- Le bloc 'CONTEXTE DE RÉFÉRENCE' fourni ci-après te sert uniquement de support pour valider "
            "l'orthographe des projets, expliciter les acronymes ou préciser la formulation technique des éléments de la réunion.\n"
            "- Tu ne dois JAMAIS importer des faits, des décisions ou des données du contexte si les notes de la réunion "
            "n'y font pas directement référence. Le contexte ne doit pas modifier la réalité de la réunion."
        )

    messages = [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                f"=== CONTEXTE DE RÉFÉRENCE INTERNE (À utiliser comme dictionnaire/glossaire uniquement) ===\n"
                f"{context_rag if context_rag else 'Aucun contexte supplémentaire disponible.'}\n\n"
                f"=== NOTES CHRONOLOGIQUES DE LA RÉUNION (Ta seule source de faits) ===\n"
                f"{combined_notes}\n\n"
                "Rédige le compte-rendu final structuré en français (Résumé exécutif, Points clés, Décisions, Actions)."
            )
        }
    ]
    
    try:
        response = await inferring_ollama(messages, model, context_size=CONTEXT_SIZE) #
        return response.message.content
    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"