# Updated server.py to handle containerized paths
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict
import requests
import json
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

@mcp.tool()
def get_weather(city: str, country_code: str = "", units: str = "metric") -> Dict[str, Any]:
    """
    Get current weather information for a specified city using OpenWeatherMap API.
    
    Args:
        city: The name of the city to get weather for
        country_code: Optional 2-letter country code (e.g., "US", "UK", "CA")
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin"
        
    Returns:
        Dictionary containing current weather information
    """
    try:
        location = city
        if country_code:
            location = f"{city},{country_code}"
        
        # Mock weather data for demonstration (same as regular server)
        mock_weather_data = {
            "location": {
                "city": city,
                "country": country_code.upper() if country_code else "Unknown",
                "coordinates": {"lat": 40.7128, "lon": -74.0060}
            },
            "current": {
                "temperature": 22 if units == "metric" else 72,
                "feels_like": 25 if units == "metric" else 77,
                "humidity": 65,
                "pressure": 1013,
                "visibility": 10,
                "uv_index": 5
            },
            "condition": {
                "main": "Clouds",
                "description": "scattered clouds",
                "icon": "03d"
            },
            "wind": {
                "speed": 3.5 if units == "metric" else 7.8,
                "direction": 230,
                "gust": 5.2 if units == "metric" else 11.6
            },
            "units": {
                "temperature": "°C" if units == "metric" else "°F" if units == "imperial" else "K",
                "speed": "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
            },
            "timestamp": "2025-10-27T22:55:00Z",
            "source": "OpenWeatherMap API (Demo Mode - Docker)",
            "success": True
        }
        
        logger.info(f"Retrieved weather data for {location}")
        return mock_weather_data
        
    except Exception as e:
        logger.error(f"Error getting weather for {city}: {e}")
        return {
            "error": f"Failed to get weather: {str(e)}",
            "city": city,
            "success": False
        }

@mcp.tool()
def get_weather_forecast(city: str, country_code: str = "", days: int = 5) -> Dict[str, Any]:
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
                "temperature": {
                    "high": base_temp + i + 2,
                    "low": base_temp + i - 3
                },
                "condition": {
                    "main": ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"][i % 5],
                    "description": ["clear sky", "few clouds", "light rain", "partly cloudy", "clear sky"][i % 5]
                },
                "precipitation": {
                    "chance": [10, 30, 80, 20, 5][i % 5],
                    "amount": [0, 0.2, 5.4, 1.1, 0][i % 5]
                },
                "wind": {
                    "speed": 3.0 + (i * 0.5),
                    "direction": 180 + (i * 30)
                }
            }
            forecast_days.append(day_data)
        
        mock_forecast = {
            "location": {
                "city": city,
                "country": country_code.upper() if country_code else "Unknown"
            },
            "forecast": forecast_days,
            "forecast_days": days,
            "timestamp": "2025-10-27T22:55:00Z",
            "source": "OpenWeatherMap API (Demo Mode - Docker)",
            "success": True
        }
        
        logger.info(f"Retrieved {days}-day forecast for {location}")
        return mock_forecast
        
    except Exception as e:
        logger.error(f"Error getting forecast for {city}: {e}")
        return {
            "error": f"Failed to get forecast: {str(e)}",
            "city": city,
            "success": False
        }

if __name__ == "__main__":
    logger.info("Starting MCP File Listing Server...")
    mcp.run("stdio")