# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code (use Docker-optimized version with path translation)
COPY server_docker.py ./server.py
COPY README.md .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Expose any ports if needed (optional for stdio MCP servers)
# EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV MCP_SERVER_MODE=docker

# Default command to run the MCP server
CMD ["python", "server.py"]