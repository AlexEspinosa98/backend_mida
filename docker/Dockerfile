# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias de sistema:
#  - libpango/libcairo/libgdk-pixbuf/libffi/shared-mime-info/fonts: WeasyPrint
#  - build-essential/cmake: compilar llama-cpp-python
#  - libpq5: cliente psycopg2 en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Modelo LLM local (Qwen2.5-3B-Instruct GGUF) horneado en la imagen ---
# Se descarga en build-time para que el contenedor funcione 100% offline en
# runtime (importante para un servidor on-premise sin salida garantizada a
# internet). Verificar en el momento del build el nombre exacto del
# repo/archivo GGUF en Hugging Face (los nombres de cuantización cambian);
# valores por defecto abajo, sobreescribibles con --build-arg.
ARG LLM_HF_REPO=Qwen/Qwen2.5-3B-Instruct-GGUF
ARG LLM_HF_FILE=qwen2.5-3b-instruct-q4_k_m.gguf
ARG LLM_MODEL_PATH=/app/models/model.gguf
RUN mkdir -p /app/models && \
    python -c "from huggingface_hub import hf_hub_download; import shutil; \
p = hf_hub_download(repo_id='${LLM_HF_REPO}', filename='${LLM_HF_FILE}'); \
shutil.copy(p, '${LLM_MODEL_PATH}')"
ENV LLM_MODEL_PATH=${LLM_MODEL_PATH}

COPY . .

RUN python manage.py collectstatic --noinput --settings=config.settings.production

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
