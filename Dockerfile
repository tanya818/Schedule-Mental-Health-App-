# Image for the FastAPI app. docker-compose.yml builds this and runs it next to Postgres.
FROM python:3.12-slim

# Print logs straight away and don't write .pyc files into the mounted code folder.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# Install dependencies first, so Docker can reuse this layer when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Production-style default. docker-compose.yml overrides this with --reload for development.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
