# Updated server.py to handle containerized paths
import asyncio
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr for STDIO servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-file-server")

# Create FastMCP server
mcp = FastMCP("File Listing Server")

@mcp.tool()
def list_files(folder_path: str) -> dict:
    """
    List all files and directories in the specified folder path.
    
    Args:
        folder_path: The absolute or relative path to the directory to list
        
    Returns:
        Dictionary containing the list of files and directories with their metadata
    """
    try:
        # Handle containerized paths - convert /host/ prefixed paths
        if folder_path.startswith('/host/'):
            # Path is already in container format
            path = Path(folder_path)
        else:
            # Convert Windows paths to container paths if running in Docker
            if folder_path.startswith('C:') or folder_path.startswith('c:'):
                # Convert C:\path to /host/C/path
                folder_path = folder_path.replace('\\', '/')
                if folder_path.startswith('C:/') or folder_path.startswith('c:/'):
                    # Remove the C: prefix and add /host/C
                    folder_path = '/host/C' + folder_path[2:]
                else:
                    # Handle C:path format (without slash)
                    folder_path = '/host/C/' + folder_path[2:]
                path = Path(folder_path)
            else:
                path = Path(folder_path)
        
        logger.info(f"Listing files in: {path}")
        
        if not path.exists():
            return {
                "error": f"Path does not exist: {folder_path}",
                "path": str(folder_path),
                "files": []
            }
        
        if not path.is_dir():
            return {
                "error": f"Path is not a directory: {folder_path}",
                "path": str(folder_path), 
                "files": []
            }
        
        files = []
        for item in path.iterdir():
            try:
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime
                })
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not access {item}: {e}")
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "unknown",
                    "size": None,
                    "modified": None,
                    "error": str(e)
                })
        
        # Sort files by name for consistent output
        files.sort(key=lambda x: x["name"].lower())
        
        return {
            "path": str(path),
            "total_items": len(files),
            "files": files,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error listing files in {folder_path}: {e}")
        return {
            "error": f"Failed to list files: {str(e)}",
            "path": str(folder_path),
            "files": []
        }

if __name__ == "__main__":
    logger.info("Starting MCP File Listing Server...")
    mcp.run("stdio")