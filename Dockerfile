FROM python:3.11-slim

WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application
COPY . .

# Create cache directory if it doesn't exist
RUN mkdir -p /app/cache

# Expose ports for the API and dashboard
EXPOSE 8002 8080

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 