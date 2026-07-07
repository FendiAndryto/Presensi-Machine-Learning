FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (libpq-dev for PostgreSQL, libgl1/libglib/libsm/libxext for opencv, cmake+libopenblas for dlib/face_recognition)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y opencv-python opencv-contrib-python opencv-contrib-python-headless 2>/dev/null || true && \
    pip install --no-cache-dir --upgrade opencv-python-headless

# Copy the rest of the application code
COPY . /app/

# Ensure necessary folders exist and remove any accidental local cache/venv
RUN mkdir -p dataset trainer static encodings && \
    find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /app/.venv /app/venv /app/env

# Expose port
EXPOSE 8000

# Run using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
