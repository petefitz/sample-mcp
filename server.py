import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from github_client_factory import AppConfiguration, GitHubClientFactory
from github_service import GitHubService

# Load environment variables from .env file
load_dotenv()


# Set up logging to stderr (not stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pete-github-server")

# Initialize the FastMCP server
mcp = FastMCP("pete-github-server")

@mcp.tool()
def list_files(folder_path: str) -> Dict[str, Any]:
    """
    List all files and directories in the specified folder path.
    
    This tool provides detailed information about directory contents including
    file sizes, types, and modification times. Results are sorted alphabetically
    for consistent output.

    Args:
        folder_path: The absolute or relative path to the directory to list.
                    Examples: "/home/user/documents", "C:\\Users\\name\\Desktop", "."

    Returns:
        Dictionary containing the list of files and directories with their metadata:
        - path (str): The resolved absolute path that was listed
        - total_items (int): Number of items found in the directory
        - files (list): Array of file/directory objects, each containing:
            - name (str): File or directory name
            - path (str): Full absolute path to the item
            - type (str): Either "file" or "directory"
            - size (int|None): File size in bytes (null for directories)
            - modified (float|None): Last modification time as Unix timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        
    Examples:
        - list_files("/home/user/documents") - List files in documents folder
        - list_files(".") - List files in current directory
        - list_files("C:\\Users\\name\\Downloads") - List Windows Downloads folder
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
                logger.warning("Cannot access %s: %s", item, e)
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
    Retrieve groups from the Groups API with pagination and optional search functionality.
    
    This tool fetches groups from a secure API endpoint and returns them as a dictionary
    where group names are keys and IDs are values. Supports pagination for large datasets
    and optional search filtering.

    Args:
        page: Page number for pagination (default: 1, must be >= 1)
        page_size: Number of groups per page (default: 10, typically 1-100)
        search: Optional search term to filter groups by name or other attributes

    Returns:
        Dictionary containing:
        - groups (Dict[str, str]): Mapping of group names to their IDs
        - groups_count (int): Number of groups retrieved in this response
        - pagination (dict): Pagination metadata with:
            - page (int): Current page number
            - page_size (int): Items per page
            - total (int): Total number of groups available
            - total_pages (int): Total number of pages
            - has_next (bool): Whether there are more pages
            - has_previous (bool): Whether there are previous pages
        - original_groups_array (list): Original API response for reference
        - search (str|None): The search term used (if any)
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        
    Examples:
        - get_groups() - Get first page of groups (default 10 items)
        - get_groups(page=2, page_size=20) - Get second page with 20 items per page
        - get_groups(search="admin") - Search for groups matching "admin"
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
        total_pages = (
            max(1, (api_total + api_page_size - 1) // api_page_size)
            if api_page_size > 0
            else 1
        )
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
        logger.error("Connection error: %s", e)
        return {"error": f"Failed to connect to API: {str(e)}", "success": False}
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {"error": "API request timed out. Please try again.", "success": False}
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
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
        logger.error("Request error: %s", e)
        return {"error": f"Request failed: {str(e)}", "success": False}
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        logger.error("Unexpected error getting groups: %s", e)
        return {"error": f"Unexpected error: {str(e)}", "success": False}


@mcp.tool()
def get_usercount(group_id: str) -> Dict[str, Any]:
    """
    Get the user count for a specific group by querying the group memberships API.
    
    This tool retrieves the total number of users/members in a specific group without
    fetching the actual member details, making it efficient for counting purposes.

    Args:
        group_id: The ID of the group to get user count for (required, non-empty string)

    Returns:
        Dictionary containing:
        - user_count (int): Total number of users in the group
        - group_id (str): The group ID that was queried
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        
    Examples:
        - get_usercount("12345") - Get user count for group with ID "12345"
        - get_usercount(group_id="admin-group-id") - Get count for admin group
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

        logger.info("Fetching user count for group ID: %s", group_id)

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
        logger.error("Connection error: %s", e)
        return {
            "error": f"Failed to connect to API: {str(e)}",
            "group_id": group_id,
            "success": False,
        }
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {
            "error": "API request timed out. Please try again.",
            "group_id": group_id,
            "success": False,
        }
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
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
        logger.error("Request error: %s", e)
        return {
            "error": f"Request failed: {str(e)}",
            "group_id": group_id,
            "success": False,
        }
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {
            "error": "Invalid JSON response from API",
            "group_id": group_id,
            "success": False,
        }
    except Exception as e:
        logger.error("Unexpected error getting user count for group %s: %s", group_id, e)
        return {
            "error": f"Unexpected error: {str(e)}",
            "group_id": group_id,
            "success": False,
        }


@mcp.tool()
def get_teams(page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """
    Retrieve teams from the GitHub organization.
    
    This tool fetches all teams in the configured GitHub organization with pagination
    support. Team names are deduplicated and sorted, and parent team names are included.

    Args:
        page: Page number for pagination (default: 1, must be >= 1)
        page_size: Number of teams per page (default: 100, max typically 100)

    Returns:
        Dictionary containing:
        - teams (list[str]): Sorted list of unique team names (includes parent teams)
        - team_count (int): Number of unique teams found
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        - status_code (int, optional): HTTP status code if error occurred
        
    Examples:
        - get_teams() - Get first 100 teams from the organization
        - get_teams(page=2, page_size=50) - Get teams 51-100 with 50 per page
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("GITHUB_API_ENDPOINT")
        bearer_token = os.getenv("GITHUB_BEARER_TOKEN")
        org = os.getenv("GITHUB_ORG_NAME")

        # Validate required configuration
        if not api_url:
            return {
                "error": "API URL not configured. Please set GITHUB_API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set GITHUB_BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("Fetching teams from API: per_page=%s&page=%s", page_size, page)

        api_url = f"{api_url}/orgs/{org}/teams?per_page={page_size}&page={page}"

        # Make the API request
        response = requests.get(api_url, headers=headers, timeout=30)

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract team names from the response array, including parent names if present
        # Use a set to ensure no duplicates
        team_names_set = set()

        if isinstance(data, list):
            for team in data:
                if isinstance(team, dict) and "name" in team:
                    # Add the team name
                    team_names_set.add(team["name"])

                    # Check if there's a parent field and it's not null
                    parent = team.get("parent")
                    if parent and isinstance(parent, dict) and "name" in parent:
                        team_names_set.add(parent["name"])

        # Convert set to sorted list for consistent output
        team_names = sorted(team_names_set)

        # Structure the response
        result = {
            "teams": team_names,
            "team_count": len(team_names),
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info("Successfully retrieved %s unique teams", len(team_names))
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        return {"error": f"Failed to connect to API: {str(e)}", "success": False}
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {"error": "API request timed out. Please try again.", "success": False}
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
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
        logger.error("Request error: %s", e)
        return {"error": f"Request failed: {str(e)}", "success": False}
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        logger.error("Unexpected error getting teams: %s", e)
        return {"error": f"Unexpected error: {str(e)}", "success": False}


@mcp.tool()
def get_repoteams(repo_slug: str = None) -> Dict[str, Any]:
    """
    Retrieve teams that have access to a specific repository from the GitHub API.
    
    This tool fetches all teams with access to the specified repository in the
    configured organization. Useful for understanding repository permissions and access.

    Args:
        repo_slug: The repository slug/name to get teams for (e.g., "my-repo", "sample-mcp")

    Returns:
        Dictionary containing:
        - repo (str): The repository slug that was queried
        - teams (list[str]): Sorted list of unique team names with access (includes parent teams)
        - team_count (int): Number of unique teams found
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        - status_code (int, optional): HTTP status code if error occurred
        
    Examples:
        - get_repoteams("my-repo") - Get teams with access to "my-repo"
        - get_repoteams(repo_slug="sample-mcp") - Get teams for sample-mcp repository
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("GITHUB_API_ENDPOINT")
        bearer_token = os.getenv("GITHUB_BEARER_TOKEN")
        org = os.getenv("GITHUB_ORG_NAME")

        # Validate required configuration
        if not api_url:
            return {
                "error": "API URL not configured. Please set GITHUB_API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set GITHUB_BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("Fetching teams from API: repo_slug=%s", repo_slug)

        api_url = f"{api_url}/repos/{org}/{repo_slug}/teams"

        # Make the API request
        response = requests.get(api_url, headers=headers, timeout=30)

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract team names from the response array, including parent names if present
        # Use a set to ensure no duplicates
        team_names_set = set()

        if isinstance(data, list):
            for team in data:
                if isinstance(team, dict) and "name" in team:
                    # Add the team name
                    team_names_set.add(team["name"])

                    # Check if there's a parent field and it's not null
                    parent = team.get("parent")
                    if parent and isinstance(parent, dict) and "name" in parent:
                        team_names_set.add(parent["name"])

        # Convert set to sorted list for consistent output
        team_names = sorted(team_names_set)

        # Structure the response
        result = {
            "repo": repo_slug,
            "teams": team_names,
            "team_count": len(team_names),
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info(
            f"Successfully retrieved {len(team_names)} unique teams for repo {repo_slug}"
        )
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        return {"error": f"Failed to connect to API: {str(e)}", "success": False}
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {"error": "API request timed out. Please try again.", "success": False}
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
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
        logger.error("Request error: %s", e)
        return {"error": f"Request failed: {str(e)}", "success": False}
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        logger.error("Unexpected error getting repository teams: %s", e)
        return {"error": f"Unexpected error: {str(e)}", "success": False}


@mcp.tool()
def get_teamrepos(team_name: str) -> Dict[str, Any]:
    """
    Retrieve repositories accessible by a specific team from the GitHub API.
    
    This tool fetches all repositories that a team has access to and categorizes them
    into archived and active repositories. Automatically handles pagination to retrieve
    all repositories regardless of count.

    Args:
        team_name: The name of the team to get repositories for (required, non-empty string)

    Returns:
        Dictionary containing:
        - team_name (str): The team name that was queried
        - archived_repos (list[str]): Sorted list of archived repository names
        - active_repos (list[str]): Sorted list of non-archived repository names
        - archived_count (int): Number of archived repositories
        - active_count (int): Number of active repositories
        - total_count (int): Total number of repositories (archived + active)
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        - status_code (int, optional): HTTP status code if error occurred
        
    Examples:
        - get_teamrepos("platform-team") - Get all repos accessible by platform-team
        - get_teamrepos(team_name="developers") - Get repos for developers team
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("GITHUB_API_ENDPOINT")
        bearer_token = os.getenv("GITHUB_BEARER_TOKEN")
        org = os.getenv("GITHUB_ORG_NAME")

        # Validate required configuration
        if not api_url:
            return {
                "error": "API URL not configured. Please set GITHUB_API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set GITHUB_BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Validate team_name parameter
        if not team_name or not team_name.strip():
            return {
                "error": "team_name parameter is required and cannot be empty",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("Fetching repositories for team: %s", team_name)

        # Initialize lists for categorizing repositories
        archived_repos = []
        active_repos = []

        # Start with the first page
        current_url = f"{api_url}/orgs/{org}/teams/{team_name}/repos"
        page_count = 0

        while current_url:
            page_count += 1
            logger.info("Fetching page %s from: %s", page_count, current_url)

            # Make the API request
            response = requests.get(current_url, headers=headers, timeout=30)

            # Check if request was successful
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Process the repository data from this page
            if isinstance(data, list):
                for repo in data:
                    if isinstance(repo, dict) and "name" in repo:
                        repo_name = repo["name"]
                        is_archived = repo.get("archived", False)

                        if is_archived:
                            archived_repos.append(repo_name)
                        else:
                            active_repos.append(repo_name)

            # Check for next page in Link header
            current_url = None
            link_header = response.headers.get("Link", "")
            if link_header:
                # Parse Link header to find "next" relation
                links = {}
                for link in link_header.split(","):
                    link = link.strip()
                    if ";" in link:
                        url_part, rel_part = link.split(";", 1)
                        url = url_part.strip().strip("<>")
                        rel = rel_part.strip()
                        if 'rel="next"' in rel:
                            links["next"] = url

                # Set next URL if it exists
                current_url = links.get("next")
                if current_url:
                    logger.info("Found next page: %s", current_url)
                else:
                    logger.info("No more pages found")

        logger.info("Completed pagination after %s pages", page_count)

        # Sort the lists for consistent output
        archived_repos.sort()
        active_repos.sort()

        # Structure the response
        result = {
            "team_name": team_name,
            "archived_repos": archived_repos,
            "active_repos": active_repos,
            "archived_count": len(archived_repos),
            "active_count": len(active_repos),
            "total_count": len(archived_repos) + len(active_repos),
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info(
            f"Successfully retrieved {result['total_count']} repositories for team {team_name} "
            f"({result['active_count']} active, {result['archived_count']} archived)"
        )
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        return {
            "error": f"Failed to connect to API: {str(e)}",
            "team_name": team_name,
            "success": False,
        }
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {
            "error": "API request timed out. Please try again.",
            "team_name": team_name,
            "success": False,
        }
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
        status_code = e.response.status_code if e.response else "Unknown"

        # Handle common HTTP status codes
        if status_code == 401:
            error_msg = "Authentication failed. Please check your bearer token."
        elif status_code == 403:
            error_msg = "Access forbidden. Check your permissions for this team."
        elif status_code == 404:
            error_msg = (
                f"Team not found or repositories not accessible for team: {team_name}"
            )
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait and try again."
        else:
            error_msg = f"API request failed with status {status_code}"

        return {
            "error": error_msg,
            "status_code": status_code,
            "team_name": team_name,
            "success": False,
        }
    except requests.exceptions.RequestException as e:
        logger.error("Request error: %s", e)
        return {
            "error": f"Request failed: {str(e)}",
            "team_name": team_name,
            "success": False,
        }
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {
            "error": "Invalid JSON response from API",
            "team_name": team_name,
            "success": False,
        }
    except Exception as e:
        logger.error("Unexpected error getting repositories for team %s: %s", team_name, e)
        return {
            "error": f"Unexpected error: {str(e)}",
            "team_name": team_name,
            "success": False,
        }


@mcp.tool()
def get_team_members(
    team_name: str, page: int = 1, page_size: int = 30
) -> Dict[str, Any]:
    """
    Retrieve members of a specific team from the GitHub API.
    
    This tool fetches the list of team members (GitHub usernames) for a specified team
    in the configured organization. Supports pagination for large teams.

    Args:
        team_name: The name of the team to get members for (required)
        page: Page number for pagination (default: 1, must be >= 1)
        page_size: Number of members per page (default: 30, typically 1-100)

    Returns:
        Dictionary containing:
        - members (list[str]): Sorted list of unique member login names
        - member_count (int): Number of unique members found
        - timestamp (str): API response timestamp
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        - status_code (int, optional): HTTP status code if error occurred
        
    Examples:
        - get_team_members("platform-team") - Get first 30 members of platform-team
        - get_team_members("developers", page=2, page_size=50) - Get members 51-100
    """
    try:
        # Get configuration from environment variables
        api_url = os.getenv("GITHUB_API_ENDPOINT")
        bearer_token = os.getenv("GITHUB_BEARER_TOKEN")
        org = os.getenv("GITHUB_ORG_NAME")

        # Validate required configuration
        if not api_url:
            return {
                "error": "API URL not configured. Please set GITHUB_API_ENDPOINT in .env file.",
                "success": False,
            }

        if not bearer_token:
            return {
                "error": "Bearer token not configured. Please set GITHUB_BEARER_TOKEN in .env file.",
                "success": False,
            }

        # Prepare request headers with Bearer token
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info("Fetching teams from API: per_page=%s&page=%s", page_size, page)

        api_url = f"{api_url}/orgs/{org}/teams/{team_name}/members?per_page={page_size}&page={page}"

        # Make the API request
        response = requests.get(api_url, headers=headers, timeout=30)

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract team names from the response array, including parent names if present
        # Use a set to ensure no duplicates
        members_set = set()

        if isinstance(data, list):
            for member in data:
                if isinstance(member, dict) and "login" in member:
                    # Add the member login
                    members_set.add(member["login"])

        # Convert set to sorted list for consistent output
        member_names = sorted(members_set)

        # Structure the response
        result = {
            "members": member_names,
            "member_count": len(member_names),
            "timestamp": response.headers.get("Date", "Unknown"),
            "success": True,
        }

        logger.info("Successfully retrieved %s unique team members", len(member_names))
        return result

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        return {"error": f"Failed to connect to API: {str(e)}", "success": False}
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout: %s", e)
        return {"error": "API request timed out. Please try again.", "success": False}
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
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
        logger.error("Request error: %s", e)
        return {"error": f"Request failed: {str(e)}", "success": False}
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e)
        return {"error": "Invalid JSON response from API", "success": False}
    except Exception as e:
        logger.error("Unexpected error getting team members: %s", e)
        return {"error": f"Unexpected error: {str(e)}", "success": False}


@mcp.tool()
def update_file(
    repo_name: str,
    branch_name: str,
    file_path: str,
    file_content: str,
    commit_message: str,
) -> Dict[str, Any]:
    """
    Update a file in a GitHub repository using the low-level Git API.
    
    This tool uses the Git plumbing API (create_git_blob, create_git_tree, create_git_commit)
    to update a file in a specific branch of a repository. The file must already exist.
    Uses GitHub App authentication from environment variables.

    Args:
        repo_name: The name of the repository (e.g., "sample-mcp", "my-project")
        branch_name: The branch to update the file in (e.g., "main", "develop")
        file_path: The path to the file within the repository (e.g., "src/main.py", "README.md")
        file_content: The new content for the file (as a string)
        commit_message: The commit message for the update (e.g., "Update configuration")

    Returns:
        Dictionary containing:
        - commit_sha (str): The SHA of the commit that was created
        - success (bool): True if operation succeeded
        - error (str, optional): Error message if operation failed
        
    Examples:
        - update_file("my-repo", "main", "README.md", "# New Content", "Update README")
        - update_file(repo_name="sample-mcp", branch_name="develop", 
                     file_path="config.json", file_content='{"key": "value"}',
                     commit_message="Update config")
    """
    try:
        # Load configuration from environment variables
        config = AppConfiguration.from_env()

        # Create the factory and service
        factory = GitHubClientFactory(config)
        github_service = GitHubService(factory)

        logger.info(
            f"Updating file {file_path} in repo {repo_name} on branch {branch_name}"
        )

        response = github_service.update_file_using_git_api(
            owner=config.github_org,
            repo_name=repo_name,
            branch_name=branch_name,
            file_path=file_path,
            file_content=file_content,
            commit_message=commit_message,
        )

        # Structure the response
        result = {
            "commit_sha": response["commit_sha"],
            "success": True,
        }

        logger.info(
            f"Successfully updated file {file_path} in repo {repo_name} on branch {branch_name}"
        )
        return result

    except Exception as e:
        logger.error("Unexpected error updating file: %s", e)
        return {"error": f"Unexpected error: {str(e)}", "success": False}


if __name__ == "__main__":
    # Run the MCP server using stdio transport
    mcp.run("stdio")
