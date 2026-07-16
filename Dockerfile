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

# Expose port (Railway will override with PORT env var)
EXPOSE 8080
ENV PORT=8080

# Run application with proper host binding
CMD ["python", "-u", "backend/app.py"]
