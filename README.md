# MCP Server - GitHub & File Operations

A comprehensive Model Context Protocol (MCP) server that provides file listing, GitHub API access, and group management capabilities.

## Features

### File Operations
- **`list_files` tool**: List all files and directories in a specified folder path
- **Error handling**: Graceful handling of invalid paths, permission errors, and inaccessible files  
- **Metadata included**: Returns file/directory names, types, sizes, and modification times
- **Sorted output**: Results are alphabetically sorted by filename

### GitHub API Integration
- **`get_teams` tool**: Retrieve teams from GitHub organization
- **`get_repoteams` tool**: Get teams with access to a specific repository
- **`get_teamrepos` tool**: List repositories accessible by a team (separated into archived/active)
- **`get_team_members` tool**: Get members of a specific GitHub team
- **`update_file` tool**: Update files in GitHub repositories using Git API
- **Authentication**: Uses GitHub App authentication with JWT tokens
- **Pagination support**: Navigate large datasets efficiently

### Groups API Integration
- **`get_groups` tool**: Retrieve groups from secure API endpoints with Bearer token authentication
- **`get_usercount` tool**: Get user count for specific groups
- **Pagination support**: Navigate large datasets with configurable page size and navigation
- **Search functionality**: Filter groups by search terms
- **Comprehensive error handling**: Robust handling of network, authentication, and API errors

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (see Configuration section below)

## Configuration

Copy `.env.example` to `.env` and configure the following variables:

### Groups API Configuration
```bash
API_ENDPOINT=https://your-api.example.com
BEARER_TOKEN=your_bearer_token_here
```

### GitHub API Configuration
```bash
GITHUB_API_ENDPOINT=https://api.github.com
GITHUB_BEARER_TOKEN=your_github_token
GITHUB_ORG_NAME=your-organization

# GitHub App Authentication
GITHUB_APP_ID=123456
GITHUB_APP_NAME=your-app-name
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----"
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
    "github-file-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_ENDPOINT": "https://your-api.example.com",
        "BEARER_TOKEN": "your_token",
        "GITHUB_API_ENDPOINT": "https://api.github.com",
        "GITHUB_BEARER_TOKEN": "your_github_token",
        "GITHUB_ORG_NAME": "your-organization"
      }
    }
  }
}
```

## Tool Reference

### File Operations

#### list_files

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

**Example:**
```
List the files in /home/user/documents
```

### GitHub Tools

#### get_teams

Retrieve teams from the GitHub organization.

**Parameters:**
- `page` (int, optional): Page number for pagination (default: 1)
- `page_size` (int, optional): Number of teams per page (default: 100)

**Returns:**
- `teams`: List of team names (sorted, deduplicated)
- `team_count`: Number of teams found
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

#### get_repoteams

Retrieve teams with access to a specific repository.

**Parameters:**
- `repo_slug` (string): The repository name/slug

**Returns:**
- `repo`: The repository slug queried
- `teams`: List of team names with access
- `team_count`: Number of teams found
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

#### get_teamrepos

Retrieve repositories accessible by a specific team, separated into archived and active lists.

**Parameters:**
- `team_name` (string): The name of the team

**Returns:**
- `team_name`: The team name queried
- `archived_repos`: List of archived repository names
- `active_repos`: List of non-archived repository names
- `archived_count`: Number of archived repositories
- `active_count`: Number of active repositories
- `total_count`: Total number of repositories
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

#### get_team_members

Get members of a specific GitHub team.

**Parameters:**
- `team_name` (string): The name of the team
- `page` (int, optional): Page number for pagination (default: 1)
- `page_size` (int, optional): Number of members per page (default: 30)

**Returns:**
- `members`: List of member login names
- `member_count`: Number of members found
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

#### update_file

Update a file in a GitHub repository using the Git API.

**Parameters:**
- `repo_name` (string): The name of the repository
- `branch_name` (string): The branch to update the file in
- `file_path` (string): The path to the file in the repository
- `file_content` (string): The new content for the file
- `commit_message` (string): The commit message

**Returns:**
- `commit_sha`: The SHA of the commit made
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

### Groups API Tools

#### get_groups

Retrieve groups from the Groups API with pagination and search.

**Parameters:**
- `page` (int, optional): Page number for pagination (default: 1)
- `page_size` (int, optional): Number of groups per page (default: 10)
- `search` (string, optional): Search term to filter groups

**Returns:**
- `groups`: Dictionary mapping group names to IDs
- `groups_count`: Number of groups retrieved
- `original_groups_array`: Original API response array
- `pagination`: Pagination metadata (page, page_size, total, has_next, has_previous)
- `search`: The search term used (if any)
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

#### get_usercount

Get the number of users in a specific group.

**Parameters:**
- `group_id` (string): The ID of the group

**Returns:**
- `user_count`: Total number of users in the group
- `group_id`: The group ID queried
- `timestamp`: API response timestamp
- `success`: Boolean indicating success
- `error`: Error message (if any occurred)

## Error Handling

The server handles various error conditions gracefully:

- **Path doesn't exist**: Returns error message with empty file list
- **Path is not a directory**: Returns error message with empty file list
- **Permission denied**: Returns error message for the folder or skips inaccessible items
- **Invalid path format**: Returns error message with details
- **API authentication errors** (401): Returns clear authentication failure message
- **API authorization errors** (403): Returns permission denied message
- **API not found errors** (404): Returns endpoint/resource not found message
- **Rate limiting** (429): Returns rate limit exceeded message
- **Network errors**: Returns connection failure messages
- **Invalid JSON responses**: Returns JSON parsing error messages

## Security Considerations

- The server can access any directory that the Python process has permissions for
- Be careful when specifying paths - the server will attempt to list any valid directory path
- Consider running with appropriate user permissions to limit directory access
- Store API tokens and credentials securely in environment variables
- Never commit `.env` files with real credentials to version control
- Use GitHub App authentication for better security and rate limits
- All API requests use Bearer token or GitHub App authentication

## Development

### Project Structure
```
├── server.py                    # Main MCP server implementation
├── weather_server.py            # Standalone weather MCP server (demo)
├── github_service.py            # GitHub API service layer
├── github_client_factory.py    # GitHub App authentication
├── server_docker.py             # Docker-compatible server variant
├── requirements.txt             # Python dependencies
├── README.md                    # This documentation
├── USAGE.md                     # Additional usage examples
├── GROUPS_API.md               # Groups API documentation
├── WEATHER_API.md              # Weather API documentation
├── DOCKER.md                   # Docker setup guide
├── test_server.py              # Server tests
├── test_groups.py              # Groups API tests
├── test_weather.py             # Weather API tests
├── test_docker.py              # Docker tests
└── .env.example                # Example environment configuration
```

### Testing

Run the test suite:

```bash
python test_server.py
python test_groups.py
python test_weather.py
```

You can also test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python server.py
```

## License

This project is open source. See the LICENSE file for details.