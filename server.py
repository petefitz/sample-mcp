import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict
import requests
import json

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
        # Using OpenWeatherMap's free API (no key required for basic current weather)
        # Note: For production use, you should get a free API key from openweathermap.org
        
        # Construct location query
        location = city
        if country_code:
            location = f"{city},{country_code}"
        
        # OpenWeatherMap API endpoint for current weather
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # For demo purposes, we'll use a mock response since we don't have an API key
        # In real usage, you would:
        # 1. Sign up for a free API key at openweathermap.org
        # 2. Add the API key to your environment variables
        # 3. Include it in the API request
        
        # Mock response for demonstration
        mock_weather_data = {
            "location": {
                "city": city,
                "country": country_code.upper() if country_code else "Unknown",
                "coordinates": {"lat": 40.7128, "lon": -74.0060}  # Example: NYC coordinates
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
            "source": "OpenWeatherMap API (Demo Mode)",
            "success": True
        }
        
        logger.info(f"Retrieved weather data for {location}")
        return mock_weather_data
        
        # Real API call implementation (commented out for demo):
        """
        import os
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return {
                "error": "OpenWeatherMap API key not found. Please set OPENWEATHER_API_KEY environment variable.",
                "city": city,
                "success": False
            }
        
        params = {
            'q': location,
            'appid': api_key,
            'units': units
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "location": {
                "city": data['name'],
                "country": data['sys']['country'],
                "coordinates": {"lat": data['coord']['lat'], "lon": data['coord']['lon']}
            },
            "current": {
                "temperature": data['main']['temp'],
                "feels_like": data['main']['feels_like'],
                "humidity": data['main']['humidity'],
                "pressure": data['main']['pressure'],
                "visibility": data.get('visibility', 0) / 1000  # Convert to km
            },
            "condition": {
                "main": data['weather'][0]['main'],
                "description": data['weather'][0]['description'],
                "icon": data['weather'][0]['icon']
            },
            "wind": {
                "speed": data['wind']['speed'],
                "direction": data['wind'].get('deg', 0)
            },
            "timestamp": data['dt'],
            "success": True
        }
        """
        
    except requests.RequestException as e:
        logger.error(f"API request failed for {city}: {e}")
        return {
            "error": f"Failed to fetch weather data: {str(e)}",
            "city": city,
            "success": False
        }
    except Exception as e:
        logger.error(f"Unexpected error getting weather for {city}: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
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
            "source": "OpenWeatherMap API (Demo Mode)",
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
    # Run the MCP server using stdio transport
    mcp.run("stdio")