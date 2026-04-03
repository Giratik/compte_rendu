# frontend/Dockerfile
FROM python:3.12.3

WORKDIR /app

COPY requirements_frontend.txt .
RUN pip install --no-cache-dir -r requirements_frontend.txt

COPY app.py .

# Expose le port de Streamlit
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]