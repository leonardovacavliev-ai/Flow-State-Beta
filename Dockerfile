FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application files
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs
COPY esp_support_links.csv ./

# Create necessary directories
RUN mkdir -p backend/chroma_db

# Expose port (Railway will set PORT via environment variables)
EXPOSE 5000

# Run application
CMD ["python", "backend/app.py"]
