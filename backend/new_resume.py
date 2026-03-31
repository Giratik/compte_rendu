import requests
import ollama 
def summarize_chunk(chunk, chunk_index, total_chunks, temperature=0.1, model_name="mistral-nemo"):
    """Étape 1 (Map) : Extrait les faits bruts d'une petite portion de texte."""
    
    prompt = f"""Tu es un assistant analytique. Voici la partie {chunk_index}/{total_chunks} de la retranscription d'une longue réunion.
Ta tâche est d'extraire TOUS les faits importants, décisions, chiffres, et actions mentionnés dans cet extrait précis.
Sois exhaustif, concis, et utilise des listes à puces. Ne fais aucune introduction ni conclusion.

Extrait à analyser :
{chunk}"""

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options= {
            "temperature": temperature,
            "keep_alive": "5m", 
            "num_ctx": 8192 # Suffisant pour un morceau
        }
    )
        
    return response["message"]["content"]
    

def synthesize_summaries(combined_text, temperature=0.2, model_name="mistral-nemo", num_ctx=16384):
    """Étape 2 (Reduce) : Applique le Super-Prompt sur tous les faits extraits."""

    
    system_prompt = """Tu es un assistant de direction expert, reconnu pour ta rigueur absolue et ta capacité de synthèse. 
Ta mission est d'analyser une liste chronologique de notes de réunion et d'en rédiger le compte rendu final exhaustif et professionnel.

Voici tes règles STRICTES :
1. FACTUEL : Ne déduis rien, n'invente aucune information.
2. OBJECTIVITÉ : Garde un ton neutre et professionnel.
3. CONCIS MAIS COMPLET : Va droit au but, mais n'oublie aucune métrique, chiffre, ou date.

Tu DOIS impérativement formater ta réponse selon la structure Markdown suivante :

# 📝 Compte Rendu de Réunion

## 🎯 Objectif principal / Sujet global
(Résume en 2 ou 3 phrases le but central de cet échange)

## 🗣️ Points de discussion majeurs
* (Point 1 : Détaillez les arguments ou informations partagées)
* (Point 2 : ...)

## ✅ Décisions Actées
(S'il n'y en a pas, écris "Aucune décision formelle prise".)
* [Décision] : (Détail)

## 🚀 Plan d'action (Prochaines étapes)
(Précise "Qui" et "Quand" si mentionné).
* [ ] Action : ... | Assigné à : ... | Délai : ...
"""

    final_prompt = f"{system_prompt}\n\nVoici les notes extraites chronologiquement de la réunion :\n\n{combined_text}"


    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": final_prompt}],
        options={
            "temperature": temperature,
            "num_ctx": num_ctx,
        }
    )
    return response["message"]["content"]
