FROM python:3.12-slim

# Install system dependencies including browser requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    exiftool \
    wget \
    xvfb \
    # Browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies and browser
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /data/output /data/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_ROOT=/data/output
ENV NETWORK_FILE=/data/networks.txt
ENV SOURCE_FILE=/data/sources.txt
ENV DISPLAY=:99

# Create entrypoint script with Xvfb support
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1024x768x16 &\n\
if [ ! -f /data/networks.txt ]; then\n\
    echo "Error: networks.txt not found in /data volume"\n\
    exit 1\n\
fi\n\
if [ ! -f /data/sources.txt ]; then\n\
    echo "Error: sources.txt not found in /data volume"\n\
    exit 1\n\
fi\n\
exec python -m scrapy "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
