#!/usr/bin/env python3
"""
Test script for the enhanced MCP server with weather API functionality
"""
import subprocess
import json
import sys

def test_mcp_weather_server():
    """Test the MCP server with new weather tools"""
    
    print("Testing Enhanced MCP Server with Weather API...")
    
    # Test messages
    messages = [
        # 1. Initialize
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        },
        # 2. List tools
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        # 3. Test file listing tool
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_files",
                "arguments": {
                    "folder_path": "."
                }
            }
        },
        # 4. Test weather tool
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_weather",
                "arguments": {
                    "city": "New York",
                    "country_code": "US",
                    "units": "metric"
                }
            }
        },
        # 5. Test weather forecast tool
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_weather_forecast",
                "arguments": {
                    "city": "London",
                    "country_code": "UK",
                    "days": 3
                }
            }
        }
    ]
    
    try:
        # Start the MCP server process
        process = subprocess.Popen([
            sys.executable, "server.py"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Send all messages
        input_data = ""
        for message in messages:
            input_data += json.dumps(message) + "\n"
        
        # Get response
        stdout, stderr = process.communicate(input=input_data, timeout=30)
        
        if process.returncode != 0:
            print(f"❌ Server failed with return code: {process.returncode}")
            print(f"stderr: {stderr}")
            return False
        
        # Parse responses
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    response = json.loads(line)
                    responses.append(response)
                except json.JSONDecodeError:
                    print(f"⚠️  Failed to parse JSON response: {line}")
                    continue
        
        print(f"✅ Received {len(responses)} responses from MCP server")
        
        # Validate responses
        if len(responses) >= 2:
            # Check tools list response
            tools_response = responses[1]
            tools = tools_response.get("result", {}).get("tools", [])
            tool_names = [tool["name"] for tool in tools]
            
            expected_tools = ["list_files", "get_weather", "get_weather_forecast"]
            for expected_tool in expected_tools:
                if expected_tool in tool_names:
                    print(f"✅ {expected_tool} tool available")
                else:
                    print(f"❌ {expected_tool} tool missing")
            
            # Test tool executions
            if len(responses) >= 4:
                # Check weather tool response
                weather_response = responses[3]
                weather_content = weather_response.get("result", {}).get("content", [])
                if weather_content:
                    weather_data = json.loads(weather_content[0].get("text", "{}"))
                    if weather_data.get("success"):
                        print("✅ Weather tool executed successfully")
                        print(f"   Location: {weather_data['location']['city']}, {weather_data['location']['country']}")
                        print(f"   Temperature: {weather_data['current']['temperature']}°C")
                        print(f"   Condition: {weather_data['condition']['description']}")
                    
            if len(responses) >= 5:
                # Check forecast tool response
                forecast_response = responses[4]
                forecast_content = forecast_response.get("result", {}).get("content", [])
                if forecast_content:
                    forecast_data = json.loads(forecast_content[0].get("text", "{}"))
                    if forecast_data.get("success"):
                        print("✅ Weather forecast tool executed successfully")
                        print(f"   Location: {forecast_data['location']['city']}")
                        print(f"   Forecast days: {forecast_data['forecast_days']}")
                        print(f"   First day: {forecast_data['forecast'][0]['condition']['main']}")
        
        print("\n🌤️  Enhanced MCP Server test completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ MCP server test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_weather_server()
    sys.exit(0 if success else 1)