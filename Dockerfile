FROM python:3.10-slim

# Install system dependencies for audio processing and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY app/requirements.txt /app/app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r app/requirements.txt

# Copy application source
COPY . /app

# Expose ports: 8000 (Game 1 KOON), 8001 (Game 2 Tìm Nắng)
EXPOSE 8000 8001

# Default command
CMD ["python", "app/server.py"]
