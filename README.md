# MCP File Listing & Weather Server

A Model Context Protocol (MCP) server that provides file listing and weather information capabilities.

## Features

### File Operations
- **`list_files` tool**: List all files and directories in a specified folder path
- **Error handling**: Graceful handling of invalid paths, permission errors, and inaccessible files
- **Metadata included**: Returns file/directory names, types, sizes, and modification times
- **Sorted output**: Results are alphabetically sorted by filename

### Weather Information  
- **`get_weather` tool**: Get current weather information for any city worldwide
- **`get_weather_forecast` tool**: Get weather forecasts up to 5 days ahead
- **Multiple units**: Support for Celsius, Fahrenheit, and Kelvin temperature units
- **Comprehensive data**: Temperature, humidity, wind, pressure, visibility, and conditions

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

The server runs as an MCP server using stdio transport:

```bash
python server.py
```

### Configuration with MCP Clients

To use this server with MCP clients like Claude Desktop, add it to your MCP configuration:

#### Claude Desktop Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "file-listing": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {}
    }
  }
}
```

#### Example Usage

Once configured, you can use the file listing tool in your MCP client:

- "List the files in my Desktop folder"
- "Show me what's in the /home/user/documents directory"
- "What files are in C:\\Users\\username\\Downloads?"

## Tool Reference

### list_files

Lists all files and directories in the specified folder path.

**Parameters:**
- `folder_path` (string): The absolute or relative path to the directory to list

**Returns:**
- `path`: The resolved absolute path that was listed
- `total_items`: Number of items found
- `files`: Array of file/directory objects with:
  - `name`: File or directory name
  - `path`: Full path to the item
  - `type`: "file" or "directory"
  - `size`: File size in bytes (null for directories)
  - `modified`: Last modification time as timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

## Error Handling

The server handles various error conditions gracefully:

- **Path doesn't exist**: Returns error message with empty file list
- **Path is not a directory**: Returns error message with empty file list
- **Permission denied**: Returns error message for the folder or skips inaccessible items
- **Invalid path format**: Returns error message with details

## Security Considerations

- The server can access any directory that the Python process has permissions for
- Be careful when specifying paths - the server will attempt to list any valid directory path
- Consider running with appropriate user permissions to limit directory access

## Development

### Project Structure
```
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── README.md          # This documentation
└── .github/
    └── copilot-instructions.md  # Project context for AI assistants
```

### Testing

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python server.py
```

## License

This project is open source. See the LICENSE file for details.