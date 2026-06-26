import os

CONTEXT_SIZE = int(os.environ.get("CONTEXT_SIZE", 30000))
URL_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8100))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "embeddinggemma:latest")