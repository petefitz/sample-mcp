#!/bin/bash

# Build and run MCP server in Docker
# This script provides convenient commands for Docker operations

set -e

case "$1" in
    build)
        echo "Building MCP File Listing Server Docker image..."
        docker build -t mcp-github-server .
        ;;
    
    run)
        echo "Running MCP File Listing Server in Docker..."
        docker run -it --rm \
            --name mcp-github-server \
            mcp-github-server
        ;;
    
    interactive)
        echo "Running MCP server in interactive mode..."
        docker run -it --rm \
            --name mcp-github-server-interactive \
            mcp-github-server bash
        ;;
    
    compose-up)
        echo "Starting services with Docker Compose..."
        docker-compose up -d
        ;;
    
    compose-down)
        echo "Stopping services with Docker Compose..."
        docker-compose down
        ;;
    
    inspector)
        echo "Running MCP Inspector in Docker..."
        docker run -it --rm \
            -p 3000:3000 \
            --name mcp-inspector \
            mcp-github-server \
            sh -c "npm install -g @modelcontextprotocol/inspector && npx @modelcontextprotocol/inspector python server.py"
        ;;
    
    test)
        echo "Testing MCP server in Docker..."
        docker run --rm \
            -v "$(pwd):/app" \
            mcp-github-server \
            python test_server.py
        ;;
    
    logs)
        echo "Showing container logs..."
        docker logs mcp-pete-github-server
        ;;
    
    *)
        echo "Usage: $0 {build|run|interactive|compose-up|compose-down|inspector|test|logs}"
        echo ""
        echo "Commands:"
        echo "  build        - Build the Docker image"
        echo "  run          - Run the MCP server container"
        echo "  interactive  - Run container with bash shell"
        echo "  compose-up   - Start services with Docker Compose"
        echo "  compose-down - Stop Docker Compose services"
        echo "  inspector    - Run MCP Inspector in container"
        echo "  test         - Run tests in container"
        echo "  logs         - Show container logs"
        exit 1
        ;;
esac
