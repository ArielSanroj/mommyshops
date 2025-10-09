# Use Ubuntu base with Python 3.11 - Better package compatibility
FROM ubuntu:22.04

# Set non-interactive mode for apt-get to avoid tzdata prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 and required tools
RUN apt-get update && \
    apt-get install -y software-properties-common curl && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-distutils \
        libgl1-mesa-glx && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    rm -rf /var/lib/apt/lists/*

# Create symbolic links for python and pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip

# Install Tesseract for pytesseract with Spanish support
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with --ignore-installed to bypass any issues
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

# Install system dependencies for Playwright and install browsers
RUN apt-get update && \
    apt-get install -y \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        xdg-utils \
        wget && \
    rm -rf /var/lib/apt/lists/* && \
    playwright install --with-deps

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8001

# Set environment variables
ENV PORT=8001

# Run the application
CMD ["python", "test_minimal.py"]
