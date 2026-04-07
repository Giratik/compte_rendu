import os
from ollama import Client

# 1. On récupère l'URL (si elle n'est pas dans Docker, on met ton IP par défaut)
# On utilise une variable personnalisée OLLAMA_URL pour être sûr
URL_OLLAMA = os.environ.get("OLLAMA_URL", "http://10.75.12.5:11434")
client = Client(host=URL_OLLAMA)

def inferring_ollama(messages, model, temperature=0.4, stream=False, context_size=32768, seed = None, keep_alive = 300):
    # Appel à l'API avec le paramètre stream
    response = client.chat(
        model=model,
        messages=messages,
        keep_alive = keep_alive,
        options={
            "temperature": temperature,
            "num_ctx": context_size,
            "seed":seed,
        },
        stream=stream 
    )

    return response