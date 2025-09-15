FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system build deps only if needed (kept minimal for slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (pruned by .dockerignore)
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000"]
