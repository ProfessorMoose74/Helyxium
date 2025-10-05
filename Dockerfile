# Multi-stage build for Helyxium VR Bridge Platform
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libusb-1.0-0-dev \
    libudev-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxi-dev \
    libxrandr-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:0

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libusb-1.0-0 \
    libudev1 \
    libgl1 \
    libglu1-mesa \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 helyxium && \
    mkdir -p /home/helyxium/.config/helyxium && \
    chown -R helyxium:helyxium /home/helyxium

# Set working directory
WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# Change ownership
RUN chown -R helyxium:helyxium /app

# Switch to non-root user
USER helyxium

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core.application import HelyxiumApp; print('OK')" || exit 1

# Default command
CMD ["python", "main.py"]
