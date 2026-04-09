import os
from ollama import Client
import time
import httpx

# 1. On récupère l'URL (si elle n'est pas dans Docker, on met ton IP par défaut)
# On utilise une variable personnalisée OLLAMA_URL pour être sûr
URL_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
client = Client(
    host=URL_OLLAMA,
    timeout=httpx.Timeout(
        connect=5.0,    # Connexion au serveur
        read=600.0,     # Attente de la réponse (le plus important)
        write=10.0,     # Envoi du prompt
        pool=5.0        # Attente d'une connexion disponible
    )
)

    
def inferring_ollama(messages, model, temperature=0.4, stream=False,
                     context_size=12000, seed=None, keep_alive=-1, **kwargs):
    start = time.time()
    try:
        response = client.chat(
            model=model,
            messages=messages,
            keep_alive=keep_alive,
            options={"temperature": temperature, "num_ctx": context_size, "seed": seed},
            stream=stream
        )
        duration = time.time() - start

        # Ollama retourne les métriques directement dans la réponse
        tokens_in  = response.prompt_eval_count    # tokens du prompt
        tokens_out = response.eval_count           # tokens générés
        speed      = tokens_out / duration if duration > 0 else 0

        print(
            f"[Ollama] {model} | "
            f"in={tokens_in}tk out={tokens_out}tk | "
            f"{duration:.1f}s | {speed:.1f} tk/s"
        )
        return response

    except TimeoutError:
        raise RuntimeError(f"⚠️ Ollama timeout après 300s (modèle: {model})")
    except Exception as e:
        raise RuntimeError(f"⚠️ Erreur Ollama : {e}")