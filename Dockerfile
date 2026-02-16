FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source and pre-built static files
COPY src/ src/
COPY static/ static/
COPY frontend/public/images/ frontend/public/images/
COPY .env.example .env.example

# Create data directory
RUN mkdir -p data

EXPOSE 8080

CMD ["python", "-m", "src.main"]
