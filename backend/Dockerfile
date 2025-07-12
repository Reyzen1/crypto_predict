# File: ./backend/Dockerfile
# Docker image for CryptoPredict MVP Backend
# Based on Python 3.11 slim image with FastAPI and ML dependencies

FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application source code
COPY . .

# Expose port that FastAPI will run on
EXPOSE 8000

# Default command to run the application
# Uses uvicorn with hot reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]