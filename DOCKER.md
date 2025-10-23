# Docker Deployment Guide for MCP File Listing Server

This guide explains how to run your MCP File Listing Server inside a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose (usually comes with Docker Desktop)

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t mcp-file-server .
```

### 2. Run the Container

```bash
# Basic run with volume mounts for file access
docker run -it --rm \
    -v "C:/Users:/host/Users:ro" \
    -v "C:/:/host/C:ro" \
    --name mcp-file-server \
    mcp-file-server
```

### 3. Using Docker Compose (Recommended)

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f mcp-file-server

# Stop the service
docker-compose down
```

## Container Configuration

### Volume Mounts

The container needs access to host directories to list files. Configure volume mounts based on what directories you want to access:

```bash
# Windows examples:
-v "C:/Users:/host/Users:ro"     # User directories (read-only)
-v "C:/:/host/C:ro"              # Entire C: drive (read-only)
-v "D:/:/host/D:ro"              # D: drive (read-only)

# Linux examples:
-v "/home:/host/home:ro"         # Home directories
-v "/:/host/root:ro"             # Root filesystem
```

### Path Translation

When running in Docker, the server automatically translates Windows paths:

- `C:\Users\pete\Desktop` → `/host/C/Users/pete/Desktop`
- `C:/Users/pete/Documents` → `/host/C/Users/pete/Documents`

You can also use container paths directly:
- `/host/Users/pete/Desktop`
- `/host/C/Program Files`

## Usage Methods

### Method 1: Direct Docker Run

```bash
# Interactive mode for testing
docker run -it --rm \
    -v "C:/Users:/host/Users:ro" \
    mcp-file-server python server.py
```

### Method 2: Docker Compose

Edit `docker-compose.yml` to adjust volume mounts, then:

```bash
docker-compose up -d
```

### Method 3: With MCP Inspector

```bash
# Run MCP Inspector in container (accessible at http://localhost:3000)
docker run -it --rm \
    -p 3000:3000 \
    -v "C:/Users:/host/Users:ro" \
    mcp-file-server \
    sh -c "npm install -g @modelcontextprotocol/inspector && npx @modelcontextprotocol/inspector python server.py"
```

### Method 4: Using the Helper Script

Make the script executable and use it:

```bash
chmod +x docker-run.sh

# Build image
./docker-run.sh build

# Run server
./docker-run.sh run

# Run with MCP Inspector
./docker-run.sh inspector

# Interactive shell
./docker-run.sh interactive
```

## Configuration for MCP Clients

### Claude Desktop Configuration

When running in Docker, update your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "file-listing": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "C:/Users:/host/Users:ro",
        "-v", "C:/:/host/C:ro", 
        "mcp-file-server",
        "python", "server.py"
      ],
      "env": {}
    }
  }
}
```

### Using Docker Compose with External Clients

If using docker-compose, you can connect to the running container:

```json
{
  "mcpServers": {
    "file-listing": {
      "command": "docker",
      "args": [
        "exec", "-i", "mcp-file-listing-server",
        "python", "server.py"
      ],
      "env": {}
    }
  }
}
```

## Security Considerations

### Read-Only Mounts
Always use read-only mounts (`:ro`) when possible to prevent accidental file modifications:

```bash
-v "C:/:/host/C:ro"  # Good - read-only
-v "C:/:/host/C"     # Risky - read-write
```

### Limited Access
Only mount directories you need:

```bash
# Good - specific access
-v "C:/Users/pete:/host/Users/pete:ro"

# Avoid - too broad access  
-v "C:/:/host/C:ro"
```

### Non-Root User
The Dockerfile creates a non-root user for better security:

```dockerfile
RUN useradd --create-home --shell /bin/bash mcp
USER mcp
```

## Troubleshooting

### Container Won't Start
```bash
# Check container logs
docker logs mcp-file-listing-server

# Run interactively to debug
docker run -it --rm mcp-file-server bash
```

### Path Access Issues
```bash
# Verify volume mounts
docker run --rm -v "C:/Users:/host/Users:ro" mcp-file-server ls -la /host/Users

# Test path translation
docker run --rm -v "C:/:/host/C:ro" mcp-file-server python -c "
from pathlib import Path
print(list(Path('/host/C/Users').iterdir()))
"
```

### Permission Errors
- Ensure volume mounts have appropriate permissions
- Use read-only mounts (`:ro`) to avoid permission issues
- Check Docker Desktop file sharing settings on Windows

## Development

### Building with Changes

```bash
# Rebuild after code changes
docker build --no-cache -t mcp-file-server .

# Or with docker-compose
docker-compose build --no-cache
```

### Testing in Container

```bash
# Run tests
docker run --rm -v "$(pwd):/app" mcp-file-server python test_server.py

# Interactive testing
docker run -it --rm -v "C:/Users:/host/Users:ro" mcp-file-server bash
```

## Production Deployment

For production use, consider:

1. **Multi-stage builds** to reduce image size
2. **Health checks** in docker-compose.yml
3. **Resource limits** (CPU, memory)
4. **Logging configuration** with proper log drivers
5. **Container orchestration** (Kubernetes, Docker Swarm)

Example production docker-compose.yml additions:

```yaml
services:
  mcp-file-server:
    # ... existing config
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```