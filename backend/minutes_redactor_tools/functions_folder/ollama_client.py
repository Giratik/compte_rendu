# ollama_client.py
from ollama import AsyncClient
import time
import httpx
import os

URL_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
ENABLE_LLM_REASONING = os.environ.get("ENABLE_LLM_REASONING", "True").lower() in ("true", "1", "yes")
client = AsyncClient(
    host=URL_OLLAMA,
    timeout=httpx.Timeout(connect=5.0, read=600.0, write=10.0, pool=5.0)
)

CONTEXT_SIZE = int(os.environ.get("CONTEXT_SIZE", 22000))

async def inferring_ollama(messages, model, temperature=0.4, stream=False,
                            context_size=CONTEXT_SIZE, seed=None, keep_alive=300, think=False, **kwargs):

    start = time.time()
    try:
        response = await client.chat(
            model=model,
            messages=messages,
            keep_alive=keep_alive,
            options={"temperature": temperature, "num_ctx": context_size, "seed": seed, "think": think},
            stream=stream
        )
        duration = time.time() - start
        tokens_in = response.prompt_eval_count
        tokens_out = response.eval_count
        speed = tokens_out / duration if duration > 0 else 0
        print(f"[Ollama] {model} | in={tokens_in}tk out={tokens_out}tk | {duration:.1f}s | {speed:.1f} tk/s")
        return response
    except Exception as e:
        raise RuntimeError(f"⚠️ Erreur Ollama : {e}")
