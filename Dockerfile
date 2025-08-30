FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pydantic-settings pydantic httpx numpy fastapi uvicorn openai
EXPOSE 8000
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000"]
