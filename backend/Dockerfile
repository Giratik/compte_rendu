# backend/Dockerfile
FROM python:3.10-slim

# FFmpeg est obligatoire pour WhisperX et Pyannote, git pour cloner WhisperX
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Installation de PyTorch (Version CUDA 12.1 pour utiliser le GPU)
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Installation des librairies de base de ton API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Installation de Pyannote et WhisperX
RUN pip install pyannote.audio
RUN pip install git+https://github.com/m-bain/whisperX.git

# 4. Copie de tout ton code backend (y compris le dossier ressources/)
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]