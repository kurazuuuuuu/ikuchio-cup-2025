FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy backend project files
COPY backend/ikuchio-cup-2025/pyproject.toml backend/ikuchio-cup-2025/uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY backend/ikuchio-cup-2025/src ./src

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]