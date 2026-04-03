# On ne garde que FFmpeg (indispensable pour lire les fichiers audio)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Fix pour les erreurs de signature GPG
RUN rm -f /etc/apt/sources.list.d/cuda.list \
    && rm -f /etc/apt/sources.list.d/nvidia-ml.list \
    && apt-get clean \
    && apt-get update --fix-missing || true

# Maintenant on installe les paquets
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Créer un lien symbolique pour que 'python' pointe vers 'python3'
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 1. Installation de PyTorch (Version CUDA pour le GPU)
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Installation de toutes tes librairies d'un seul coup (y compris WhisperX et Pyannote)
COPY requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements_backend.txt

# 3. Copie de ton code et de tes ressources
COPY . .


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
