# One image for both the API (gunicorn) and the bot worker; compose picks the command.
FROM python:3.13-slim

# Show logs immediately, and keep the image free of .pyc files and pip's download cache.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies before code: this layer is reused until requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Bring the schema and the bots up to date, then serve. Both steps are safe to repeat on every start.
# exec makes gunicorn replace the shell, so it receives docker's stop signal and shuts down cleanly.
CMD ["sh", "-c", "python migrate.py && python -m bots.seed && exec gunicorn --bind 0.0.0.0:5000 --workers 2 --access-logfile - --error-logfile - app:app"]
