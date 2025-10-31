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
logger = logging.getLogger("weather-server")

# Initialize the FastMCP server
mcp = FastMCP("weather-server")


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
