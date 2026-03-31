import subprocess

def ask_ollama(prompt, model="mistral"):
    command = ['ollama', 'run', model]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    response, error = process.communicate(input=prompt)
    return response.strip()
