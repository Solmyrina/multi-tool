FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    cron \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x setup_weather_automation.sh start_with_automation.sh

# Expose the API port
EXPOSE 8000

# Start cron and run the application with automation
CMD service cron start && ./setup_weather_automation.sh && python api.py