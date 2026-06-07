FROM python:3.11-slim

# Install system dependencies (libgl1 replaces deprecated libgl1-mesa-glx on Debian Trixie+)
RUN apt-get update && apt-get install -y \
    libgl1 \
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

# Start command (runs Flask app directly to save memory and avoid Gunicorn master/worker memory overhead)
CMD ["python", "app.py"]
