FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy source code to /app/src
COPY src/ ./src/

# Change working directory to src
WORKDIR /app/src

# Install dependencies directly with pip
RUN pip install --no-cache-dir fastapi[standard] uvicorn google-cloud-firestore google-cloud-secret-manager google-genai firebase-admin==6.5.0

# Verify firebase-admin installation
RUN python -c "import firebase_admin; print('Firebase Admin SDK installed successfully')"

# Set environment variables
ENV PORT=8000
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start command with direct uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "30"]