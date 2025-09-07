"""
Test script to verify MCP servers are working correctly
Run this after setting up your .env file
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the mcps directory to the path
sys.path.append(str(Path(__file__).parent / "mcps"))

async def test_mcp_server(mcp_name, command):
    """Test an individual MCP server"""
    print(f"\n🧪 Testing {mcp_name} MCP...")
    
    try:
        from agno.tools.mcp import MCPTools
        
        mcp_tools = MCPTools(
            command=command,
            timeout_seconds=30,
            env={**os.environ}
        )
        
        await mcp_tools.connect()
        
        # Test ping function
        result = await mcp_tools.call_tool("ping", {})
        print(f"   ✅ {mcp_name} MCP: Connection successful")
        print(f"   📊 Response: {result}")
        
        await mcp_tools.close()
        return True
        
    except Exception as e:
        print(f"   ❌ {mcp_name} MCP: Failed - {str(e)}")
        return False

async def main():
    """Test all MCP servers"""
    print("🔍 Multi-MCP Server Test")
    print("========================")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    # Test each MCP
    tests = [
        ("JIRA", "python mcps/jira_mcp.py"),
        ("Confluence", "python mcps/confluence_mcp.py"),
        ("Bitbucket", "python mcps/bitbucket_mcp.py"),
    ]
    
    results = {}
    
    for name, command in tests:
        try:
            results[name] = await test_mcp_server(name, command)
        except Exception as e:
            print(f"   ❌ {name} MCP: Failed to test - {str(e)}")
            results[name] = False
    
    # Summary
    print(f"\n📋 Test Summary")
    print("===============")
    successful = sum(results.values())
    total = len(results)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n🎯 Result: {successful}/{total} MCPs working")
    
    if successful == total:
        print("✨ All systems ready! You can now start the application.")
    else:
        print("⚠️  Some MCPs failed. Check your .env configuration.")
        print("💡 Make sure you have valid tokens and URLs for each service.")

if __name__ == "__main__":
    asyncio.run(main())