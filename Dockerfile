# Store Bought web app — container image for Render, Koyeb, Fly, etc.
#
# Build:  docker build -t store-bought .
# Run:    docker run -p 8000:8000 store-bought
#
# Hosting platforms inject the port to listen on via the $PORT environment
# variable; the start command below honours it (defaulting to 8000 locally).

FROM python:3.12-slim

# Fail fast and keep logs unbuffered; don't write .pyc files into the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy only what the running app needs (see .dockerignore for what's excluded).
COPY app/ ./app/
COPY data/ ./data/
COPY wsgi.py ./

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime. Two workers with a few threads
# each is plenty for this read-only, I/O-light app.
CMD exec gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --threads 4 --timeout 60 wsgi:app
