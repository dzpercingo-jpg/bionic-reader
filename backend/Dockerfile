FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip \
 && pip install \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "python-multipart>=0.0.20" \
        "pymupdf>=1.24.0" \
        "python-docx>=1.1.2" \
        "ebooklib>=0.18" \
        "beautifulsoup4>=4.12.3" \
        "lxml>=5.3.0" \
        "markdown-it-py>=3.0.0" \
        "striprtf>=0.0.28" \
        "chardet>=5.2.0" \
        "pydantic>=2.9.0"

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
