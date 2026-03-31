# frontend/Dockerfile
FROM python:3.12.3

WORKDIR /app

# Requirements minimal : streamlit, requests
RUN pip install --no-cache-dir streamlit requests

COPY app.py .

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]