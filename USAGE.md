# MCP Server Usage Examples

This document shows how to use the File Listing MCP Server.

## Running the Server

To start the server directly:

```bash
# Using the virtual environment
cd d:\workspace\python\sample-mcp
.venv\Scripts\python.exe server.py
```

## Using with MCP Inspector

You can test and debug the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server.py
```

## Claude Desktop Configuration

Add this to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-listing": {
      "command": "python",
      "args": ["d:\\workspace\\python\\sample-mcp\\server.py"],
      "env": {}
    }
  }
}
```

## Example Tool Usage

Once connected to an MCP client, you can use the `list_files` tool:

### Example 1: List files in current directory
```
"List the files in the current MCP server directory"
```

### Example 2: List files in a specific directory  
```
"Show me what files are in my Desktop folder"
```

### Example 3: List files with specific path
```
"What's in the C:\Users\username\Documents directory?"
```

## Tool Response Format

The `list_files` tool returns:

```json
{
  "path": "D:\\workspace\\python\\sample-mcp",
  "total_items": 7,
  "files": [
    {
      "name": "README.md",
      "path": "D:\\workspace\\python\\sample-mcp\\README.md", 
      "type": "file",
      "size": 3283,
      "modified": 1761256718.8193111
    },
    {
      "name": ".vscode",
      "path": "D:\\workspace\\python\\sample-mcp\\.vscode",
      "type": "directory", 
      "size": null,
      "modified": 1761256741.3861735
    }
  ],
  "success": true
}
```

## Error Handling

The server gracefully handles various error conditions:

- **Invalid paths**: Returns error message with empty file list
- **Permission denied**: Returns error message for inaccessible directories
- **Non-existent paths**: Returns appropriate error response
- **Non-directory paths**: Informs that the path is not a directory

## Testing

Run the included test script to verify functionality:

```bash
.venv\Scripts\python.exe test_server.py
```

This will test the complete MCP protocol handshake and tool execution.