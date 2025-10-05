# Use Ubuntu base with Python 3.11 - Better package compatibility
FROM ubuntu:22.04

# Install Python 3.11 and required tools
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    python3.11 \
    python3.11-venv \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && rm -rf /var/lib/apt/lists/*

# Install libGL for OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Create symbolic links for python and pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with --ignore-installed to bypass uninstall issues
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8001

# Set environment variables
ENV PORT=8001

# Run the application
CMD ["python", "main.py"]


