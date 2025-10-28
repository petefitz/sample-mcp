# Groups API Integration for MCP Server

This document describes the Groups API functionality that replaces the weather API in the MCP File Listing Server.

## Overview

The `get_groups` tool provides secure API access to retrieve group information with:
- **Bearer token authentication** from environment variables
- **Pagination support** for large datasets
- **Search functionality** to filter groups
- **Comprehensive error handling** for various API scenarios

## Configuration

### Environment Variables

Create a `.env` file in the project root with your API configuration:

```env
# Groups API Configuration
API_ENDPOINT=https://your-api.com
BEARER_TOKEN=your_actual_bearer_token_here
```

### Security Best Practices

- ✅ **Never commit `.env` files** to version control
- ✅ **Use `.env.example`** as a template for required variables
- ✅ **Rotate bearer tokens** regularly
- ✅ **Use HTTPS endpoints** only

## API Tool

### `get_groups` - Retrieve Groups with Authentication

**Description**: Retrieve groups from a secure API endpoint with Bearer token authentication, pagination, and search capabilities.

**Parameters**:
- `page` (optional, default: 1): Page number for pagination
- `limit` (optional, default: 10): Number of groups per page (1-100)
- `search` (optional): Search term to filter groups by name or description

**Authentication**: Uses Bearer token from `BEARER_TOKEN` environment variable

**Request Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
```

## Usage Examples

### Basic Usage
```json
{
  "name": "get_groups",
  "arguments": {
    "page": 1,
    "limit": 10
  }
}
```

### With Search
```json
{
  "name": "get_groups", 
  "arguments": {
    "page": 1,
    "limit": 20,
    "search": "admin"
  }
}
```

### Pagination
```json
{
  "name": "get_groups",
  "arguments": {
    "page": 3,
    "limit": 25
  }
}
```

## Response Format

### Data Transformation

The tool automatically transforms the API response for easier consumption:

**Input from API** (array format):
```json
{
  "groups": [
    {"id": "aaa", "name": "abc"},
    {"id": "bbb", "name": "bcd"}
  ]
}
```

**Output from MCP Tool** (dictionary format):
```json
{
  "groups": {
    "abc": "aaa",
    "bcd": "bbb"
  },
  "groups_count": 2,
  "original_groups_array": [
    {"id": "aaa", "name": "abc"},
    {"id": "bbb", "name": "bcd"}
  ]
}
```

**Key Benefits**:
- ✅ **Easy Lookup**: Find group ID by name: `groups["GroupName"]`
- ✅ **Simplified Access**: No need to iterate through arrays
- ✅ **Preserved Data**: Original array included for reference
- ✅ **Error Handling**: Invalid groups (missing name/id) are filtered out

### Successful Response

The response transforms the groups array into a dictionary where group names are keys and IDs are values:

```json
{
  "groups": {
    "Administrators": "group-123",
    "Users": "group-456",
    "Developers": "group-789"
  },
  "groups_count": 3,
  "original_groups_array": [
    {
      "id": "group-123",
      "name": "Administrators",
      "description": "System administrators group",
      "member_count": 5,
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "group-456", 
      "name": "Users",
      "description": "General users group",
      "member_count": 150,
      "created_at": "2025-01-10T08:15:00Z"
    },
    {
      "id": "group-789",
      "name": "Developers",
      "description": "Development team",
      "member_count": 12,
      "created_at": "2025-01-12T14:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  },
  "search": null,
  "timestamp": "Mon, 28 Oct 2025 12:00:00 GMT",
  "success": true
}
```

### Error Response

```json
{
  "error": "Authentication failed. Please check your bearer token.",
  "status_code": 401,
  "success": false
}
```

## Error Handling

The tool provides comprehensive error handling for various scenarios:

### Configuration Errors
- **Missing API URL**: `API_ENDPOINT not configured`
- **Missing Bearer Token**: `BEARER_TOKEN not configured`

### Network Errors  
- **Connection Failed**: `Failed to connect to API`
- **Request Timeout**: `API request timed out`

### Authentication Errors
- **401 Unauthorized**: `Authentication failed. Please check your bearer token`
- **403 Forbidden**: `Access forbidden. Check your permissions`

### API Errors
- **404 Not Found**: `API endpoint not found. Check your API URL`
- **429 Rate Limited**: `Rate limit exceeded. Please wait and try again`
- **500 Server Error**: `API request failed with status 500`

### Data Errors
- **Invalid JSON**: `Invalid JSON response from API`
- **Malformed Response**: Various parsing error messages

## Testing

### Test with Mock Configuration

```bash
# Test server functionality (will show config errors with example values)
python test_groups.py
```

### Test with Real API

1. **Configure Environment**:
   ```bash
   # Edit .env file with real values
   API_ENDPOINT=https://your-api.com
   BEARER_TOKEN=your_real_token
   ```

2. **Run Tests**:
   ```bash
   python test_groups.py
   ```

### Direct JSON-RPC Testing

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_groups", "arguments": {"page": 1, "limit": 5}}}' | python server.py
```

## Docker Usage

### Build with Configuration

```bash
# Build image (uses .env.example by default)
docker build -t mcp-groups-server .
```

### Run with Environment Variables

```bash
# Run with environment variables
docker run --rm -i \
  -e API_ENDPOINT="https://your-api.com" \
  -e BEARER_TOKEN="your_token" \
  mcp-groups-server python server.py
```

### Run with .env File Mount

```bash
# Mount local .env file
docker run --rm -i \
  -v "$(pwd)/.env:/app/.env:ro" \
  mcp-groups-server python server.py
```

## API Requirements

Your Groups API should support:

### Endpoint Structure
```
GET /groups?page=1&limit=10&search=admin
```

### Response Format Options

The tool handles multiple response formats:

**Option 1: Direct Array**
```json
{
  "groups": [...],
  "total": 100,
  "total_pages": 10
}
```

**Option 2: Data Wrapper**
```json
{
  "data": [...],
  "total": 100, 
  "total_pages": 10
}
```

### Required Headers
- Accept `Authorization: Bearer {token}`
- Return `Content-Type: application/json`
- Optional: Return `Date` header for timestamps

## Integration with MCP Clients

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "groups-api": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_ENDPOINT": "https://your-api.com",
        "BEARER_TOKEN": "your_token"
      }
    }
  }
}
```

### Natural Language Queries

Users can ask:
- "Show me all groups"
- "Find groups with 'admin' in the name"  
- "Get the second page of groups"
- "List groups with 25 items per page"

## Security Considerations

### Token Management
- **Environment Variables**: Store tokens securely in environment variables
- **Token Rotation**: Regularly rotate bearer tokens
- **Principle of Least Privilege**: Use tokens with minimal required permissions

### Network Security  
- **HTTPS Only**: Never use HTTP endpoints for production
- **Timeout Limits**: 30-second timeout prevents hanging requests
- **Rate Limiting**: Respect API rate limits

### Error Information
- **No Token Exposure**: Error messages never include actual token values
- **Limited Error Details**: Errors provide helpful info without exposing internals

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify bearer token is valid and not expired
   - Check token has necessary permissions
   - Ensure token format is correct (no extra spaces)

2. **Connection Issues**
   - Verify API URL is correct and accessible
   - Check network connectivity
   - Ensure API server is running

3. **Configuration Issues**
   - Verify `.env` file exists and is readable
   - Check environment variable names match exactly
   - Ensure no trailing spaces in values

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Exact request URLs and headers (tokens are masked)
- Response status codes and headers
- Detailed error information