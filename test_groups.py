#!/usr/bin/env python3
"""
Test script for the MCP server with Groups API functionality
"""
import subprocess
import json
import sys
import os
from dotenv import load_dotenv

def test_groups_api():
    """Test the MCP server with Groups API"""
    
    # Load environment variables
    load_dotenv()
    
    print("Testing MCP Server with Groups API...")
    
    # Check if environment variables are configured
    api_url = os.getenv('API_ENDPOINT')
    bearer_token = os.getenv('BEARER_TOKEN')
    
    if not api_url or api_url == "https://api.example.com":
        print("⚠️  API_ENDPOINT not configured with real API endpoint")
    if not bearer_token or bearer_token == "your_bearer_token_here":
        print("⚠️  BEARER_TOKEN not configured with real token")
    
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
        # 3. Test groups tool with default parameters
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_groups",
                "arguments": {
                    "page": 1,
                    "limit": 5
                }
            }
        },
        # 4. Test groups tool with search
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_groups",
                "arguments": {
                    "page": 1,
                    "limit": 10,
                    "search": "admin"
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
            
            expected_tools = ["list_files", "get_groups", "get_weather_forecast"]
            for expected_tool in expected_tools:
                if expected_tool in tool_names:
                    print(f"✅ {expected_tool} tool available")
                else:
                    print(f"❌ {expected_tool} tool missing")
            
            # Test groups tool execution
            if len(responses) >= 3:
                groups_response = responses[2]
                groups_content = groups_response.get("result", {}).get("content", [])
                if groups_content:
                    groups_data = json.loads(groups_content[0].get("text", "{}"))
                    if groups_data.get("success"):
                        print("✅ Groups tool executed successfully")
                        groups_dict = groups_data.get('groups', {})
                        print(f"   Retrieved {groups_data.get('groups_count', 0)} groups as name->id dictionary")
                        print(f"   Page: {groups_data.get('pagination', {}).get('page', 'N/A')}")
                        if groups_dict and len(groups_dict) > 0:
                            print("   Sample mappings:")
                            for i, (name, group_id) in enumerate(groups_dict.items()):
                                if i < 3:  # Show first 3 mappings
                                    print(f"     '{name}' -> '{group_id}'")
                    else:
                        print(f"⚠️  Groups tool returned error: {groups_data.get('error', 'Unknown error')}")
                        
            # Test groups search functionality
            if len(responses) >= 4:
                search_response = responses[3]
                search_content = search_response.get("result", {}).get("content", [])
                if search_content:
                    search_data = json.loads(search_content[0].get("text", "{}"))
                    if search_data.get("success"):
                        print("✅ Groups search executed successfully")
                        print(f"   Search term: '{search_data.get('search')}'")
                        groups_dict = search_data.get('groups', {})
                        print(f"   Found {search_data.get('groups_count', 0)} matching groups as name->id dictionary")
                        if groups_dict and len(groups_dict) > 0:
                            print("   Matching groups:")
                            for name, group_id in groups_dict.items():
                                print(f"     '{name}' -> '{group_id}'")
                    else:
                        print(f"⚠️  Groups search returned error: {search_data.get('error', 'Unknown error')}")
        
        print("\n📊 Groups API MCP Server test completed!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ MCP server test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

if __name__ == "__main__":
    success = test_groups_api()
    if not success:
        print("\n💡 To configure the Groups API:")
        print("1. Edit the .env file with your actual API URL and bearer token")
        print("2. Set API_ENDPOINT to your API endpoint")
        print("3. Set BEARER_TOKEN to your authentication token")
    sys.exit(0 if success else 1)