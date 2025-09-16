FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy source code first
COPY src/ ./src/

# Install dependencies directly with pip
RUN pip install --no-cache-dir fastapi[standard] uvicorn google-cloud-firestore google-cloud-secret-manager google-genai

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Start command with direct uvicorn
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "30"]