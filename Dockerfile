FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the trained model during build so container starts instantly with 0 runtime download
RUN mkdir -p app/ml && \
    curl -L "https://huggingface.co/Avi7061/e-plus-eeg-model/resolve/main/eeg_best_model.joblib" -o app/ml/eeg_best_model.joblib

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
