import whisper
import torch
import gc

# determine device based on CUDA availability
_device = "cuda" if torch.cuda.is_available() else "cpu"

# Transcribe audio using the tiny model
def transcribe_audio_tiny(file_path):
    model = whisper.load_model("tiny", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

# Transcribe audio using the base model
def transcribe_audio_base(file_path):
    model = whisper.load_model("base", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

def transcribe_audio_small(file_path):
    model = whisper.load_model("small", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

def transcribe_audio_medium(file_path):
    model = whisper.load_model("medium", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

def transcribe_audio_large(file_path):
    model = whisper.load_model("large", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

def transcribe_audio_turbo(file_path):
    model = whisper.load_model("turbo", device=_device)
    result = model.transcribe(file_path)
    return result['text'], model

def unload_model_from_memory(model):
    if torch.cuda.is_available():
        del model.encoder
        del model.decoder
        torch.cuda.empty_cache()
    gc.collect()
