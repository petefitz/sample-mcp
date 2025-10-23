# MCP Server File Listing Project

This is a Model Context Protocol (MCP) server written in Python that provides functionality to list files from local directories.

## Project Structure
- `server.py` - Main MCP server implementation
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

## Features
- List files and directories from a supplied local folder path
- Handle errors gracefully for invalid or inaccessible paths
- Follow MCP protocol specifications

## Usage
The server provides a `list_files` tool that accepts a folder path and returns a list of files and directories within that path.