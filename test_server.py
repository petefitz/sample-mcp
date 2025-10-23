#!/usr/bin/env python3
"""
Simple test script to verify the MCP server functionality
"""
import asyncio
import json
import subprocess
import tempfile
import os

async def test_mcp_server():
    """Test the MCP server with a complete handshake and tool call"""
    server_path = "d:\\workspace\\python\\sample-mcp\\server.py"
    
    # Test messages
    initialize_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    
    initialized_msg = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    list_tools_msg = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    call_tool_msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_files",
            "arguments": {"folder_path": "d:\\workspace\\python\\sample-mcp"}
        }
    }
    
    # Create input for the server
    input_data = (
        json.dumps(initialize_msg) + "\n" +
        json.dumps(initialized_msg) + "\n" +
        json.dumps(list_tools_msg) + "\n" +
        json.dumps(call_tool_msg) + "\n"
    )
    
    try:
        # Run the server using virtual environment python
        venv_python = "d:\\workspace\\python\\sample-mcp\\.venv\\Scripts\\python.exe"
        process = subprocess.Popen(
            [venv_python, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="d:\\workspace\\python\\sample-mcp"
        )
        
        # Send input and get output
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        
        print("=== MCP Server Test Results ===")
        print(f"Return code: {process.returncode}")
        
        if stderr:
            print(f"STDERR:\n{stderr}")
        
        if stdout:
            print("STDOUT:")
            lines = stdout.strip().split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        response = json.loads(line)
                        print(f"Response {i}: {json.dumps(response, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Non-JSON line {i}: {line}")
        
        print("\n=== Test Summary ===")
        if process.returncode == 0:
            print("✅ Server executed successfully")
        else:
            print(f"❌ Server failed with return code {process.returncode}")
            
    except subprocess.TimeoutExpired:
        print("❌ Server test timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())