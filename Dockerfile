FROM python:3.11-slim

WORKDIR /app

# Install dependencies at the versions production runs: requirements.txt pins
# the direct ones, constraints.txt everything they pull in (see both headers).
COPY backend/requirements.txt backend/constraints.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt -c backend/constraints.txt

# Copy application files
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs
COPY esp_support_links.csv ./
# Help-centre overrides for Find links (backend/find_links_job.py)
COPY scripts/help_centres.json ./scripts/

# Create necessary directories
RUN mkdir -p backend/chroma_db

# Set working directory to backend for app execution
WORKDIR /app/backend

# Expose port (Railway will set PORT env var dynamically)
EXPOSE 8080

# Run application with Gunicorn for production
# Railway will inject $PORT (default keeps `docker run` working locally).
# No --max-requests: the single worker hosts in-process state (crawl worker
# threads, analytics write queue, memory sessions) that a recycle would drop.
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --worker-class gthread --timeout 120 app:app
