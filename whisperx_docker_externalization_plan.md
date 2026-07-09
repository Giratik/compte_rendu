# Plan d'externalisation de WhisperX dans une image Docker dédiée

## Analyse de la situation actuelle

### Problème identifié
- WhisperX est actuellement installé directement dans l'image Docker du backend
- Cela entraîne une redondance des librairies entre différents projets
- Le téléchargement de WhisperX se fait à chaque démarrage, ce qui est coûteux en temps et en ressources

### Architecture actuelle
- **Backend Dockerfile**: Installe WhisperX via `pip install git+https://github.com/m-bain/whisperX.git`
- **Backend requirements.txt**: Inclut `whisperx` et `torch` comme dépendances
- **Utilisation**: Le module `whisperx_transcriber.py` utilise directement les fonctions de WhisperX pour la transcription audio

## Solution proposée: Externalisation de WhisperX

### Architecture cible
```
[Client] → [Backend API] → [Service WhisperX dédié] (via gRPC/REST)
```

### Étapes de mise en œuvre

#### 1. Création d'une image Docker dédiée à WhisperX

**Dockerfile pour le service WhisperX** (`whisperx-service/Dockerfile`):
```dockerfile
# Image optimisée pour WhisperX avec CUDA
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Installation des dépendances système
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configuration Python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

WORKDIR /app

# Installation de PyTorch et WhisperX
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install git+https://github.com/m-bain/whisperX.git
RUN pip install faster-whisper
RUN pip install grpcio grpcio-tools protobuf

# Copie du code du service
COPY whisperx_service.py .
COPY whisperx.proto .

# Génération du code gRPC
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. whisperx.proto

EXPOSE 50051
CMD ["python", "whisperx_service.py"]
```

#### 2. Définition de l'interface de service (gRPC)

**Fichier `whisperx.proto`**:
```protobuf
syntax = "proto3";

package whisperx;

service WhisperXService {
    rpc TranscribeAudio (TranscriptionRequest) returns (TranscriptionResponse);
}

message TranscriptionRequest {
    string audio_path = 1;
    string model_choice = 2;
    string device = 3;
    int32 batch_size = 4;
    string compute_type = 5;
}

message TranscriptionResponse {
    string transcript = 1;
    string error = 2;
}
```

#### 3. Implémentation du service WhisperX

**Fichier `whisperx_service.py`**:
```python
import grpc
from concurrent import futures
import whisperx
import torch
import gc
import os
import whisperx_pb2
import whisperx_pb2_grpc

class WhisperXServicer(whisperx_pb2_grpc.WhisperXServiceServicer):
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def TranscribeAudio(self, request, context):
        try:
            # Implémentation similaire à _transcribe_sync actuelle
            asr_options = {
                "beam_size": 5,
                "condition_on_previous_text": False,
                "compression_ratio_threshold": 2.4
            }

            model = whisperx.load_model(
                request.model_choice,
                self.device,
                compute_type=request.compute_type,
                asr_options=asr_options
            )

            audio = whisperx.load_audio(request.audio_path)
            result = model.transcribe(audio, batch_size=request.batch_size, language="fr")

            # Cleanup
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Alignment
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"],
                device=self.device
            )
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            del model_a
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            full_text = " ".join([
                segment.get("text", "").strip()
                for segment in result["segments"]
            ])

            return whisperx_pb2.TranscriptionResponse(transcript=full_text)

        except Exception as e:
            return whisperx_pb2.TranscriptionResponse(error=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    whisperx_pb2_grpc.add_WhisperXServiceServicer_to_server(WhisperXServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("WhisperX service started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

#### 4. Modification du backend pour utiliser le service externalisé

**Modification de `whisperx_transcriber.py`**:
```python
# Remplacer l'import direct de whisperx par l'import gRPC
import grpc
import whisperx_pb2
import whisperx_pb2_grpc

# Configuration de la connexion au service WhisperX
WHISPERX_SERVICE_ADDRESS = "whisperx-service:50051"

def get_whisperx_client():
    channel = grpc.insecure_channel(WHISPERX_SERVICE_ADDRESS)
    return whisperx_pb2_grpc.WhisperXServiceStub(channel)

async def transcribe_audio_with_whisperx(
    audio_path: str,
    model_choice: str = "large-v3",
    device: str = "cuda",
    batch_size: int = 4,
    compute_type: str = "int8"
) -> str:
    """
    Transcribe audio using external WhisperX service.
    """
    client = get_whisperx_client()
    request = whisperx_pb2.TranscriptionRequest(
        audio_path=audio_path,
        model_choice=model_choice,
        device=device,
        batch_size=batch_size,
        compute_type=compute_type
    )

    response = client.TranscribeAudio(request)

    if response.error:
        raise Exception(f"WhisperX service error: {response.error}")

    return response.transcript
```

#### 5. Mise à jour du docker-compose.yml

**Ajout du service WhisperX**:
```yaml
services:
  whisperx-service:
    build:
      context: ./whisperx-service
      dockerfile: Dockerfile
    container_name: whisperx_service
    volumes:
      - /home/paulvidouze/.cache/huggingface:/root/.cache/huggingface
      - /home/paulvidouze/.cache/torch:/root/.cache/torch
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - default

  backend:
    # Configuration existante, mais suppression des dépendances WhisperX
    build:
      context: ./backend
      dockerfile: Dockerfile
    # ... reste de la configuration existante
    depends_on:
      - whisperx-service
```

#### 6. Optimisation du Dockerfile backend

**Nouveau Dockerfile backend** (sans WhisperX et sans torch) :
```dockerfile
# backend/Dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN rm -f /etc/apt/sources.list.d/cuda.list \
    && rm -f /etc/apt/sources.list.d/nvidia-ml.list \
    && apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

WORKDIR /app

# Installation des dépendances (sans whisperx et sans torch/torchaudio)
COPY requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements_backend.txt

# Ajout des dépendances gRPC
RUN pip install grpcio grpcio-tools protobuf

# Copie du code source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.00.00", "--port", "8000", "--workers", "1"]
```

#### 7. Mise à jour des requirements_backend.txt

**Suppression des dépendances WhisperX**:
```text
# Web Framework & Server
fastapi
uvicorn
python-multipart
pydantic

# AI & LLM (Ollama)
ollama

# Manipulation de Documents (PDF & Word)
PyPDF2
python-docx
fpdf
htmldocx
markdown

# Utilitaires
typing-extensions

transformers == 5.9.0

chromadb==0.5.3

# gRPC pour la communication avec le service WhisperX
grpcio
grpcio-tools
protobuf
```

## Avantages de cette solution

1. **Réduction de la redondance**: WhisperX n'est installé qu'une seule fois dans son propre conteneur
2. **Meilleure isolation**: Le service WhisperX peut être mis à jour indépendamment du backend
3. **Scalabilité**: Possibilité de faire tourner plusieurs instances du service WhisperX
4. **Maintenance simplifiée**: Mises à jour de WhisperX sans impact sur le backend
5. **Réutilisation**: Le même service WhisperX peut être utilisé par plusieurs projets
6. **Optimisation des ressources**: Le conteneur WhisperX peut avoir ses propres limites de ressources
7. **Suppression des dépendances inutiles**: Le backend n'a plus besoin de torch/torchaudio après l'externalisation

## Analyse des dépendances torch/torchaudio

Dans votre projet de compte-rendu, **torch et torchaudio sont uniquement utilisés par WhisperX** pour :

1. **Vérification de la disponibilité CUDA**: `torch.cuda.is_available()`
2. **Gestion du cache CUDA**: `torch.cuda.empty_cache()`

Ces fonctions sont spécifiquement liées à l'exécution de WhisperX et seront **déplacées vers le service WhisperX dédié**. Après l'externalisation :

- **Le backend n'aura plus besoin de torch/torchaudio** - ces dépendances peuvent être supprimées du Dockerfile backend
- **Le service WhisperX conservera torch/torchaudio** - car il en a besoin pour exécuter les modèles
- **Réduction significative de la taille de l'image backend** - suppression d'environ 1-2GB de dépendances inutiles

Cette optimisation supplémentaire améliore encore l'architecture en éliminant les dépendances superflues du backend.

## Considérations techniques

1. **Gestion des fichiers audio**: Le service WhisperX doit avoir accès aux fichiers audio, soit via:
   - Montage de volumes communs
   - Transfert des fichiers via gRPC (moins recommandé pour les gros fichiers)
   - Utilisation d'un stockage partagé (NFS, S3, etc.)

2. **Gestion des erreurs**: Implémentation robuste de la gestion des erreurs et des timeouts

3. **Performance**: Le service gRPC doit être optimisé pour gérer plusieurs requêtes simultanées

4. **Cache des modèles**: Le service WhisperX téléchargera le modèle large-v3 au premier démarrage et le mettra en cache dans le conteneur. Les volumes de cache peuvent être montés pour persister le cache entre les redémarrages si souhaité.

5. **Sécurité**: S'assurer que la communication entre les services est sécurisée (SSL/TLS pour gRPC)

6. **Indépendance**: Le service est complètement autonome et n'a pas besoin de dépendre du cache local de l'hôte.

## Avantages de l'approche simplifiée

- **Indépendance totale**: Plus de dépendance au cache local de l'ordinateur hôte
- **Flexibilité**: Le modèle est téléchargé uniquement quand nécessaire
- **Maintenance simplifiée**: Pas besoin de gérer des images Docker volumineuses
- **Mises à jour faciles**: Les nouveaux modèles sont automatiquement téléchargés

## Étapes de migration recommandées

1. Créer le service WhisperX et le tester indépendamment
2. Modifier le backend pour utiliser le service externalisé
3. Tester la communication entre les services
4. Mettre à jour le docker-compose pour inclure le nouveau service
5. Déployer et monitorer les performances
6. Optimiser si nécessaire (ajustement des ressources, scaling, etc.)

## Structure de fichiers finale recommandée

```
/compte_rendu
├── backend/
│   ├── Dockerfile (sans WhisperX)
│   ├── requirements_backend.txt (sans WhisperX)
│   └── ... (code existant modifié)
├── whisperx-service/
│   ├── Dockerfile
│   ├── whisperx_service.py
│   ├── whisperx.proto
│   └── requirements.txt
├── docker-compose.yml (mis à jour)
└── ...
```

Cette approche permet une externalisation propre de WhisperX tout en maintenant la fonctionnalité existante et en améliorant l'architecture globale du système.