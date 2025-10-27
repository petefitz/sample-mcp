# Weather API Integration for MCP Server

This document describes the weather API functionality added to the MCP File Listing Server.

## New Tools Added

### 1. `get_weather` - Current Weather Information

**Description**: Get current weather information for a specified city using OpenWeatherMap API.

**Parameters**:
- `city` (required): The name of the city to get weather for
- `country_code` (optional): 2-letter country code (e.g., "US", "UK", "CA")  
- `units` (optional): Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin"

**Example Usage**:
```json
{
  "name": "get_weather",
  "arguments": {
    "city": "London",
    "country_code": "UK", 
    "units": "metric"
  }
}
```

**Response Format**:
```json
{
  "location": {
    "city": "London",
    "country": "UK",
    "coordinates": {"lat": 51.5074, "lon": -0.1278}
  },
  "current": {
    "temperature": 22,
    "feels_like": 25,
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
    "speed": 3.5,
    "direction": 230,
    "gust": 5.2
  },
  "units": {
    "temperature": "°C",
    "speed": "m/s"
  },
  "timestamp": "2025-10-27T22:55:00Z",
  "source": "OpenWeatherMap API",
  "success": true
}
```

### 2. `get_weather_forecast` - Weather Forecast

**Description**: Get weather forecast for a specified city.

**Parameters**:
- `city` (required): The name of the city to get forecast for
- `country_code` (optional): 2-letter country code (e.g., "US", "UK", "CA")
- `days` (optional): Number of forecast days (1-5, default: 5)

**Example Usage**:
```json
{
  "name": "get_weather_forecast",
  "arguments": {
    "city": "New York",
    "country_code": "US",
    "days": 3
  }
}
```

**Response Format**:
```json
{
  "location": {
    "city": "New York", 
    "country": "US"
  },
  "forecast": [
    {
      "date": "2025-10-28",
      "temperature": {"high": 23, "low": 17},
      "condition": {
        "main": "Sunny",
        "description": "clear sky"
      },
      "precipitation": {"chance": 10, "amount": 0},
      "wind": {"speed": 3.0, "direction": 180}
    }
  ],
  "forecast_days": 3,
  "timestamp": "2025-10-27T22:55:00Z",
  "source": "OpenWeatherMap API",
  "success": true
}
```

## Implementation Details

### Demo Mode vs Production

**Current Implementation**: Demo mode with mock data
- No API key required for testing
- Returns realistic but static mock weather data
- Includes clear indication in response (`"source": "OpenWeatherMap API (Demo Mode)"`)

**Production Setup**: To use real weather data:

1. **Get API Key**: Sign up for free at [openweathermap.org](https://openweathermap.org/api)
2. **Set Environment Variable**:
   ```bash
   export OPENWEATHER_API_KEY=your_api_key_here
   ```
3. **Uncomment Real API Code**: The server contains commented production code ready to use

### Dependencies

Added to `requirements.txt`:
```
requests>=2.28.0
```

### Error Handling

The weather tools include comprehensive error handling:
- Invalid city names
- Network connectivity issues  
- API rate limiting
- Missing API keys (production mode)
- Malformed responses

Example error response:
```json
{
  "error": "Failed to fetch weather data: City not found",
  "city": "InvalidCity",
  "success": false
}
```

## Usage Examples

### With MCP Clients

When connected to Claude Desktop or other MCP clients, users can ask:

- "What's the weather like in Tokyo?"
- "Show me the 5-day forecast for Berlin, Germany"  
- "Get current weather for San Francisco in Fahrenheit"
- "What's the temperature in Sydney, Australia?"

### Direct JSON-RPC Testing

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "Paris", "country_code": "FR"}}}' | python server.py
```

### Docker Usage

The weather functionality is available in both native and Docker versions:

```bash
docker run --rm -i mcp-file-server python server.py
```

## API Rate Limits & Best Practices

### OpenWeatherMap Free Tier:
- 1,000 calls per day
- 60 calls per minute
- Current weather data
- 5-day forecast

### Best Practices:
1. **Caching**: Implement response caching for frequently requested locations
2. **Error Handling**: Always check `success` field in responses
3. **Rate Limiting**: Implement client-side rate limiting for production use
4. **Fallback**: Handle API unavailability gracefully

## Security Considerations

1. **API Key Protection**: Store API keys as environment variables, never in code
2. **Input Validation**: City names are validated to prevent injection attacks
3. **Network Security**: All API calls use HTTPS
4. **Error Information**: Error messages don't expose internal system details

## Testing

Run the enhanced test suite:
```bash
python test_weather.py
```

This tests:
- Server initialization
- Tool listing (including new weather tools)
- File listing functionality (existing)
- Weather data retrieval
- Weather forecast functionality

## Future Enhancements

Potential additions:
- Historical weather data
- Weather alerts and warnings
- Air quality information
- Multiple location batch requests
- Weather maps and radar data
- Astronomical data (sunrise/sunset)

## Troubleshooting

### Common Issues:

1. **"requests not found"**: Install dependencies with `pip install -r requirements.txt`
2. **Network timeouts**: Check internet connectivity
3. **Invalid responses**: Verify city names and country codes
4. **API key errors**: Ensure environment variable is set correctly (production mode)

### Debugging:

Enable debug logging to see detailed API interactions:
```python
logging.basicConfig(level=logging.DEBUG)
```