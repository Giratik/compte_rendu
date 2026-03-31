import ffmpeg
import os

def extract_audio(input_file, output_file="audio.wav"):
    if not os.path.exists(output_file):
        ffmpeg.input(input_file).output(output_file, format="wav", ac=1, ar=16000).run()
    return output_file