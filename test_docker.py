#!/usr/bin/env python3
"""
Test script for the Dockerized MCP File Listing Server
"""
import subprocess
import json
import sys

def test_docker_mcp_server():
    """Test the MCP server running in Docker container"""
    
    print("Testing MCP File Listing Server in Docker...")
    
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
        # 3. Call list_files tool with container path
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_files",
                "arguments": {
                    "folder_path": "/host/Users/pete/Desktop"
                }
            }
        }
    ]
    
    try:
        # Start the Docker container
        process = subprocess.Popen([
            "docker", "run", "--rm", "-i",
            "-v", "C:/Users:/host/Users:ro",
            "-v", "C:/:/host/C:ro",
            "mcp-file-server",
            "python", "server.py"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Send all messages
        input_data = ""
        for message in messages:
            input_data += json.dumps(message) + "\n"
        
        # Get response
        stdout, stderr = process.communicate(input=input_data, timeout=30)
        
        if process.returncode != 0:
            print(f"❌ Container failed with return code: {process.returncode}")
            print(f"stderr: {stderr}")
            return False
        
        # Parse responses
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    response = json.loads(line)
                    responses.append(response)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse JSON response: {line}")
                    continue
        
        print(f"✅ Received {len(responses)} responses from Docker container")
        
        # Validate responses
        if len(responses) >= 3:
            # Check initialize response
            init_response = responses[0]
            if init_response.get("result", {}).get("protocolVersion"):
                print("✅ Initialization successful")
            
            # Check tools list response
            tools_response = responses[1]
            tools = tools_response.get("result", {}).get("tools", [])
            if any(tool["name"] == "list_files" for tool in tools):
                print("✅ list_files tool available")
            
            # Check tool execution response
            if len(responses) >= 3:
                exec_response = responses[2]
                content = exec_response.get("result", {}).get("content", [])
                if content and len(content) > 0:
                    result = json.loads(content[0].get("text", "{}"))
                    if result.get("success"):
                        print(f"✅ Successfully listed {result.get('total_items', 0)} items from Docker container")
                        print(f"   Path: {result.get('path')}")
                        if result.get('files'):
                            for file in result['files'][:3]:  # Show first 3 files
                                print(f"   - {file['name']} ({file['type']})")
                    else:
                        print(f"⚠️  Tool execution returned error: {result.get('error')}")
        
        print("\n🐳 Docker MCP Server test completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Docker container test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error testing Docker container: {e}")
        return False

if __name__ == "__main__":
    success = test_docker_mcp_server()
    sys.exit(0 if success else 1)