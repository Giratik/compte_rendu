import asyncio
import whisperx
import torch
import gc
import subprocess
import tempfile
import os


def _transcribe_sync(
    audio_path: str,
    model_choice: str,
    device: str,
    batch_size: int,
    compute_type: str
) -> str:
    """Version synchrone, exécutée dans un thread séparé."""
    asr_options = {
        "beam_size": 5,
        "condition_on_previous_text": False,
        "compression_ratio_threshold": 2.4
    }

    model_name = "large-v3" if model_choice == "large-v3" else model_choice
    model = whisperx.load_model(
        model_name,
        device,
        compute_type=compute_type,
        asr_options=asr_options
    )

    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=batch_size, language="fr")

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device=device
    )
    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
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

    return full_text


async def transcribe_audio_with_whisperx(
    audio_path: str,
    model_choice: str = "large-v3",
    device: str = "cuda",
    batch_size: int = 16,
    compute_type: str = "float16"
) -> str:
    """
    Transcribe audio using WhisperX with alignment.
    Exécute le travail bloquant dans un thread pour ne pas geler le event loop.
    """
    return await asyncio.to_thread(
        _transcribe_sync,
        audio_path,
        model_choice,
        device,
        batch_size,
        compute_type
    )

def convert_audio_to_wav(input_path: str) -> str:
    """
    Convert audio file to WAV format (16kHz, mono, PCM 16-bit).
    
    Args:
        input_path: Path to the input audio file
    
    Returns:
        Path to the converted WAV file
    """
    tmp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    output_path = tmp_audio_file.name
    tmp_audio_file.close()
    
    command = [
        "ffmpeg", "-i", input_path, "-vn",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y",
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return output_path


async def convert_audio_to_wav_async(input_path: str) -> str:
    return await asyncio.to_thread(convert_audio_to_wav, input_path)