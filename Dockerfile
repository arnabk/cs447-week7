FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config.yaml .
COPY pytest.ini .

# Create output directories
RUN mkdir -p /app/data /app/outputs

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "scripts/run_demo.py"]
