import PyPDF2
import docx
import ollama

def summarize_chunk(chunk, chunk_index, total_chunks, temperature=0.1, model_name="mistral-nemo", passes=1):
    """Étape 1 (Map) : Extraction des faits avec option de double vérification."""
    
    # --- PASSAGE 1 : EXTRACTION INITIALE ---
    prompt_1 = f"""Tu es un assistant analytique. Voici la partie {chunk_index}/{total_chunks} de la retranscription d'une réunion.
Ta tâche est d'extraire de ce morceau de réunion les informations qui y sont contenus :
- Actions effectuées et résultats (s'il y en a)
- Décision prises
- chiffres
Sois exhaustif, concis et utilise des listes à puces. Ne fais aucune introduction.

Extrait à analyser :
{chunk}"""

    premier_jet = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt_1}],
        options= {
            "seed": 12345,
            "temperature": temperature,
            "keep_alive": "5m", 
            "num_ctx": 8192 # Suffisant pour un morceau
        }
    )
        

    
    # Si on a demandé un seul passage, on s'arrête là
    if passes == 1:
        return premier_jet["message"]["content"]

    # --- PASSAGE 2 : AUDIT ET ENRICHISSEMENT (Double vérification) ---
    prompt_2 = f"""Tu es un auditeur qualité intransigeant. 
Voici l'extrait original d'une réunion :
{chunk}

Voici le premier brouillon d'extraction des faits :
{premier_jet["message"]["content"]}

Ta mission : Ce brouillon a oublié des détails techniques, des arguments ou des nuances importantes présents dans le texte original. 
Identifie ce qui manque, et réécris une NOUVELLE liste à puces fusionnée, ENRICHIE et 100% EXHAUSTIVE. 
Ne fais aucune introduction, donne uniquement la liste finale améliorée."""

    payload_2 = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt_2}],
        options= {
            "seed": 12345,
            "temperature": temperature,
            "keep_alive": "5m", 
            "num_ctx": 8192 # Suffisant pour un morceau
        }
    )
    
    return payload_2["message"]["content"]

def synthesize_summaries(combined_text, prompt_cr, format_cr, temperature=0.15, model_name="mistral-nemo", num_ctx=16384):
    """Étape 2 (Reduce) : Applique le Super-Prompt sur tous les faits extraits."""

    if prompt_cr == None :
        prompt_cr = """
        Tu es un documentaliste intraitable et exhaustif. Ton but est de compiler les notes de réunion suivantes dans le format demandé, SANS JAMAIS généraliser ni omettre de détails.

Voici tes règles STRICTES :
1. FACTUEL ET EXHAUSTIF : Si les notes mentionnent un prix, une durée, une métrique, une anecdote ou un exemple précis (ex: mots corrigés), TU DOIS absolument l'inclure.
2. NE PAS RÉSUMER LES LISTES : Cite TOUS les outils, logiciels, entreprises et intervenants mentionnés dans les notes. Ne dis jamais "plusieurs outils", nomme-les tous un par un.
3. OBJECTIVITÉ : Garde un ton neutre et professionnel.
4. FIDÉLITÉ : N'invente aucune information, mais ne perds aucune donnée brute présente dans les notes.
        """

    if format_cr == None:
        format_cr = """
# Compte Rendu de Réunion

---------
Date : {...}
Heure de début : {...}
---------

# Paricipant à la réunion
{nom}{prénom}
{nom}{prénom}
...

# Ordre du jour
{...}


## Objectif principal / Sujet global
(Résume en 2 ou 3 phrases le but central de cet échange)

## Intervenants et Personnes citées
* (Lister exhaustivement TOUTES les personnes mentionnées dans les notes : présents, absents, ou évoqués)

## Outils, Solutions et Tarifs mentionnés
(Lister TOUS les outils, logiciels ou entreprises cités, avec leurs prix, métriques ou caractéristiques exactes s'ils sont mentionnés dans les notes)
* [Nom de l'outil] : (Détails techniques, prix, durée d'essai, limitations, etc.)

## Points de discussion et Faits précis
(Détaillez les arguments, les retours d'expérience et les exemples techniques précis abordés. Soyez exhaustif)
* (Point 1 : ...)
* (Point 2 : ...)

## Décisions Actées
(S'il n'y en a pas, écris "Aucune décision formelle prise".)
* [Décision] : (Détail)

## Plan d'action (Prochaines étapes)
(Précise "Qui" et "Quand" si mentionné).
* [ ] Action : ... | Assigné à : ... | Délai : ...
"""
    
    system_prompt = f"""{prompt_cr}

Tu DOIS impérativement formater ta réponse selon la structure Markdown suivante :

{format_cr}

"""

    final_prompt = f"{system_prompt}\n\nVoici les notes extraites chronologiquement de la réunion :\n\n{combined_text}"


    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": final_prompt}],
        options={
            "seed": 1234,
            "temperature": temperature,
            "num_ctx": num_ctx,
        }
    )
    return response["message"]["content"]


def extract_text(bf):
    """Fonction utilitaire pour lire le texte d'un PDF ou d'un Word"""
    text = ""
    filename = bf.name.lower()
    
    try:
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(bf)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
        elif filename.endswith((".docx", ".doc")):
            doc = docx.Document(bf)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        return f"Erreur de lecture : {str(e)}"
        
    return text

def creation_template_from_file(bf, selected_model):
    """
    Lit un document de référence et utilise le LLM pour en extraire 
    un template réutilisable (structure, ton, formatage).
    """
    # 1. On extrait le contenu brut du fichier
    reference_text = extract_text(bf)
    
    # 2. On prépare le prompt pour demander au LLM d'extraire la structure
    prompt_extraction = f"""
    Voici un compte-rendu de réunion existant :
    
    {reference_text}
    
    Ta tâche : Analyse ce document et extrais-en un modèle (template) vide et des règles de formatage.
    - Identifie les grandes parties (ex: Titre, Participants, Ordre du jour, Décisions, Actions à suivre).
    - Identifie le style (puces, tableaux, style formel ou relâché).
    - NE GARDE PAS le contenu spécifique de cette réunion (efface les noms, dates et sujets précis).
    - Rédige ton résultat sous forme d'instructions claires que je pourrai donner à un assistant pour formater de futurs comptes-rendus.
    
    Réponds UNIQUEMENT avec la structure vide et les consignes de rédaction, sans texte d'introduction.
    """
    
    # 3. On appelle Ollama (en mode non-streamé si possible, car c'est une tâche de fond)
    message = [{"role": "user", "content": prompt_extraction}]
    
    # Si ta fonction inferring_ollama fait du stream par défaut, on peut tout récupérer dans une variable
    #generateur = inferring_ollama(messages=messages, model=selected_model, stream=True)
    response = ollama.chat(
        model=selected_model,
        messages=message, 
        options={
            "seed": 12345,
        }
    )
    return response["message"]["content"]
    
    #template_genere = ""
    #for chunk in generateur:
    #    template_genere += chunk
    #    
    #return template_genere