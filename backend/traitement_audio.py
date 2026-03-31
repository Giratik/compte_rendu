import whisper
import torch

import ffmpeg
import os


def extract_audio(input_file, output_file="audio.mp3"):
    if not os.path.exists(output_file):
        ffmpeg.input(input_file).output(output_file, format="mp3", ac=1, ar=16000).run()
    return output_file


model = whisper.load_model("small")


def diarize_and_transcribe(audio_file, pipeline):
    # Appliquer la diarisation
    
    diarization = pipeline(audio_file)

    results = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        start = turn.start
        end = turn.end
        segment = f"segment_{start:.2f}_{end:.2f}.wav"

        # Extraire le segment audio
        (
            ffmpeg
            .input(audio_file, ss=start, to=end)
            .output(segment, format="wav", ac=1, ar=16000)
            .overwrite_output()
            .run(quiet=True)
        )

        # Transcrire le segment avec Whisper
        transcription = model.transcribe(segment, language="fr")  # adapte la langue
        text = transcription["text"].strip()

        results.append({
            "speaker": speaker,
            "start": start,
            "end": end,
            "text": text
        })

        # Supprimer le fichier segment temporaire
        os.remove(segment)

    return results