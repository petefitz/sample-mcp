import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server


# Set up logging to stderr (not stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
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
                "files": []
            }
        
        # Check if it's a directory
        if not path.is_dir():
            return {
                "error": f"Path is not a directory: {folder_path}",
                "path": str(path),
                "files": []
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
                    "modified": item.stat().st_mtime if item.exists() else None
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
            "success": True
        }
        
    except PermissionError:
        return {
            "error": f"Permission denied accessing: {folder_path}",
            "path": folder_path,
            "files": []
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "path": folder_path,
            "files": []
        }


if __name__ == "__main__":
    # Run the MCP server using stdio transport
    mcp.run("stdio")