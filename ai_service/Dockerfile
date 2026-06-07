FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (Railway passes PORT env var)
EXPOSE 5000

# Start command (uses shell format to expand the $PORT environment variable)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
