# backend/Dockerfile
# Image optimisée pour CUDA et PyTorch (basée sur Ubuntu 22.04)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Évite les prompts bloquants lors de l'installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Nettoyage des clés GPG NVIDIA (sécurité anti-crash)
# 2. Installation de Python 3.10 (natif), FFmpeg et Git
RUN rm -f /etc/apt/sources.list.d/cuda.list \
    && rm -f /etc/apt/sources.list.d/nvidia-ml.list \
    && apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Forcer le système à utiliser la commande 'python' pour appeler 'python3'
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

WORKDIR /app

# Installation de PyTorch CUDA 12.1
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Installation des dépendances
COPY requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements_backend.txt
RUN pip install faster-whisper
RUN pip install git+https://github.com/m-bain/whisperX.git

RUN python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('Systran/faster-whisper-large-v3'); \
print('OK')"

# Copie du code source
COPY . .

# Expose le port de FastAPI
EXPOSE 8001

# Lancement de l'API sur le port 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]