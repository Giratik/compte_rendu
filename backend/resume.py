import ollama

def summarize_with_ollama(transcript, temperature=0.5, model=None):
    prompt = f"""Voici une transcription de réunion :
        
    {transcript}
    \n\n   
    Agis en tant que **Secrétaire de séance expert**. À partir de la transcription suivante, rédige un compte rendu de réunion professionnel, structuré et synthétique.
    **Directives spécifiques :**
    1. **Identification** : Identifie et associe les noms des participants à leurs interventions respectives en te basant sur le contenu des échanges.
    2. **Synthèse** : Ne fais pas de retranscription mot à mot. Synthétise les idées en utilisant un style impersonnel (ex: 'Il est décidé de...' plutôt que 'Pascal dit que...').
    3. **Formatage** :
    * Utilise des **listes à puces** pour les points de discussion.
    * Présente la section 'Actions à faire' sous forme de **tableau** (Action | Responsable | Échéance si mentionnée).
    * Mets en **gras** les termes techniques et les décisions critiques.
    
    **Structure attendue :**
    * **Titre de la réunion** (déduit du contexte)
    * **Résumé exécutif** (3 lignes max)
    * **Participants & Rôles**
    * **Synthèse des échanges par thématique**
    * **Décisions actées**
    * **Tableau de suivi des actions**
    """
    
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={
            #"seed": 12345,
            "temperature": temperature,
            "num_ctx": 32768,
            "num_gen": 2048
            #"keep_alive":0
        }
    )
    return response["message"]["content"]

