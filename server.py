import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

# Load environment variables from .env file
load_dotenv()


# Set up logging to stderr (not stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("file-listing-server")

# Initialize the FastMCP server
mcp = FastMCP("file-listing-server")


@mcp.tool()
def list_files(folder_path: str) -> Dict[str, Any]:
    """
    List all files and directories in the specified folder path.

    Args:
        folder_path: The absolute or relative path to the directory to list

    Returns:
        Dictionary containing the list of files and directories with their metadata
    """
    try:
        # Convert to Path object and resolve
        path = Path(folder_path).resolve()

        # Check if path exists
        if not path.exists():
            return {
                "error": f"Path does not exist: {folder_path}",
                "path": str(path),
                "files": [],
            }

        # Check if it's a directory
        if not path.is_dir():
            return {
                "error": f"Path is not a directory: {folder_path}",
                "path": str(path),
                "files": [],
            }

        # List directory contents
        files_list = []

        for item in path.iterdir():
            try:
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime if item.exists() else None,
                }
                files_list.append(item_info)
            except (OSError, PermissionError) as e:
                # Skip items we can't access
                logger.warning(f"Cannot access {item}: {e}")
                continue

        # Sort by name for consistent output
        files_list.sort(key=lambda x: x["name"].lower())

        return {
            "path": str(path),
            "total_items": len(files_list),
            "files": files_list,
            "success": True,
        }

    except PermissionError:
        return {
            "error": f"Permission denied accessing: {folder_path}",
            "path": folder_path,
            "files": [],
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "path": folder_path,
            "files": [],
        }


@mcp.tool()
def get_groups(
    page: int = 1, page_size: int = 10, search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve groups from the API with pagination and optional search functionality.
    Returns groups as a dictionary where group names are keys and IDs are values.

    Args:
        page: Page number for pagination (default: 1)
        page_size: Number of groups per page (default: 10)
        search: Optional search term to filter groups

    Returns:
        Dictionary containing:
        - groups: Dict[str, str] mapping group names to IDs
        - groups_count: Number of groups retrieved
        - pagination: Pagination metadata
        - original_groups_array: Original API response for reference
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("API_ENDPOINT")
        bearer_token = os.getenv("BEARER_TOKEN")

        # Validate required configuration
        if not api_url:
            return {
                "error": "Groups API URL not configured. Please set API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Prepare query parameters
        params = {"page": page, "page_size": page_size}

        if search:
            params["search"] = search

        logger.info(
            f"Fetching groups from API: page={page}, page_size={page_size}, search={search}"
        )

        api_url = f"{api_url}/api/v2/authorizations/groups?managed=true&q={search}&pageSize={page_size}&pageIndex={page}"

        # Make the API request
        response = requests.get(api_url, headers=headers, params=params, timeout=30)

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Get the groups array from response
        groups_array = data.get("groups", data.get("data", []))

        # Transform groups array into dictionary with name as key and id as value
        groups_dict = {}
        for group in groups_array:
            if isinstance(group, dict) and "name" in group and "id" in group:
                groups_dict[group["name"]] = group["id"]

        # Extract pagination info from the 'page' object in the response
        page_info = data.get("page", {})
        api_page_index = page_info.get("pageIndex", page)
        api_page_size = page_info.get("pageSize", page_size)
        api_total = page_info.get("total", len(groups_array))
        
        # Calculate pagination metadata
        total_pages = max(1, (api_total + api_page_size - 1) // api_page_size) if api_page_size > 0 else 1
        has_next = api_page_index < total_pages
        has_previous = api_page_index > 1

        # Structure the response
        result = {
            "groups": groups_dict,
            "groups_count": len(groups_dict),
            "original_groups_array": groups_array,  # Keep original for reference
            "pagination": {
                "page": api_page_index,
                "page_size": api_page_size,
                "total": api_total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
            "search": search,
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info(
            f"Successfully retrieved {len(groups_dict)} groups and transformed to name->id dictionary"
        )
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return {"error": f"Failed to connect to API: {str(e)}", "success": False}
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {e}")
        return {"error": "API request timed out. Please try again.", "success": False}
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        status_code = e.response.status_code if e.response else "Unknown"

        # Handle common HTTP status codes
        if status_code == 401:
            error_msg = "Authentication failed. Please check your bearer token."
        elif status_code == 403:
            error_msg = "Access forbidden. Check your permissions."
        elif status_code == 404:
            error_msg = "API endpoint not found. Check your API URL."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait and try again."
        else:
            error_msg = f"API request failed with status {status_code}"

        return {"error": error_msg, "status_code": status_code, "success": False}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": f"Request failed: {str(e)}", "success": False}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        logger.error(f"Unexpected error getting groups: {e}")
        return {"error": f"Unexpected error: {str(e)}", "success": False}


@mcp.tool()
def get_usercount(group_id: str) -> Dict[str, Any]:
    """
    Get the user count for a specific group by calling the group memberships API.

    Args:
        group_id: The ID of the group to get user count for

    Returns:
        Dictionary containing:
        - user_count: Total number of users in the group
        - group_id: The group ID that was queried
        - success: Boolean indicating if the request was successful
        - error: Error message (if any occurred)
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("API_ENDPOINT")
        bearer_token = os.getenv("BEARER_TOKEN")

        # Validate required configuration
        if not api_url:
            return {
                "error": "API URL not configured. Please set API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Validate group_id parameter
        if not group_id or not group_id.strip():
            return {
                "error": "group_id parameter is required and cannot be empty",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(f"Fetching user count for group ID: {group_id}")

        # Construct the API URL for group memberships
        # Based on the sample response structure, this appears to be a memberships endpoint
        memberships_url = f"{api_url}/api/v2/authorizations/group-memberships?groupId={group_id}&pageIndex=1&pageSize=0"

        # Make the API request
        response = requests.get(memberships_url, headers=headers, timeout=30)

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract the total count from the page object
        page_info = data.get("page", {})
        total_users = page_info.get("total", 0)

        # Structure the response
        result = {
            "user_count": total_users,
            "group_id": group_id,
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info(
            f"Successfully retrieved user count for group {group_id}: {total_users} users"
        )
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return {
            "error": f"Failed to connect to API: {str(e)}",
            "group_id": group_id,
            "success": False,
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {e}")
        return {
            "error": "API request timed out. Please try again.",
            "group_id": group_id,
            "success": False,
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        status_code = e.response.status_code if e.response else "Unknown"

        # Handle common HTTP status codes
        if status_code == 401:
            error_msg = "Authentication failed. Please check your bearer token."
        elif status_code == 403:
            error_msg = "Access forbidden. Check your permissions for this group."
        elif status_code == 404:
            error_msg = f"Group not found or memberships endpoint not accessible for group ID: {group_id}"
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait and try again."
        else:
            error_msg = f"API request failed with status {status_code}"

        return {
            "error": error_msg,
            "status_code": status_code,
            "group_id": group_id,
            "success": False,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return {
            "error": f"Request failed: {str(e)}",
            "group_id": group_id,
            "success": False,
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {
            "error": "Invalid JSON response from API",
            "group_id": group_id,
            "success": False,
        }
    except Exception as e:
        logger.error(f"Unexpected error getting user count for group {group_id}: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "group_id": group_id,
            "success": False,
        }


@mcp.tool()
def get_weather_forecast(
    city: str, country_code: str = "", days: int = 5
) -> Dict[str, Any]:
    """
    Get weather forecast for a specified city.

    Args:
        city: The name of the city to get forecast for
        country_code: Optional 2-letter country code (e.g., "US", "UK", "CA")
        days: Number of forecast days (1-5)

    Returns:
        Dictionary containing weather forecast information
    """
    try:
        # Validate days parameter
        if days < 1 or days > 5:
            days = 5

        location = city
        if country_code:
            location = f"{city},{country_code}"

        # Mock forecast data for demonstration
        forecast_days = []
        base_temp = 20

        for i in range(days):
            day_data = {
                "date": f"2025-10-{28 + i}",
                "temperature": {"high": base_temp + i + 2, "low": base_temp + i - 3},
                "condition": {
                    "main": ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"][
                        i % 5
                    ],
                    "description": [
                        "clear sky",
                        "few clouds",
                        "light rain",
                        "partly cloudy",
                        "clear sky",
                    ][i % 5],
                },
                "precipitation": {
                    "chance": [10, 30, 80, 20, 5][i % 5],
                    "amount": [0, 0.2, 5.4, 1.1, 0][i % 5],
                },
                "wind": {"speed": 3.0 + (i * 0.5), "direction": 180 + (i * 30)},
            }
            forecast_days.append(day_data)

        mock_forecast = {
            "location": {
                "city": city,
                "country": country_code.upper() if country_code else "Unknown",
            },
            "forecast": forecast_days,
            "forecast_days": days,
            "timestamp": "2025-10-27T22:55:00Z",
            "source": "OpenWeatherMap API (Demo Mode)",
            "success": True,
        }

        logger.info(f"Retrieved {days}-day forecast for {location}")
        return mock_forecast

    except Exception as e:
        logger.error(f"Error getting forecast for {city}: {e}")
        return {
            "error": f"Failed to get forecast: {str(e)}",
            "city": city,
            "success": False,
        }


if __name__ == "__main__":
    # Run the MCP server using stdio transport
    mcp.run("stdio")
