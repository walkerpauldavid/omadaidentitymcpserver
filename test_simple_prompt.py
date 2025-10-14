#!/usr/bin/env python3
"""
Simple test to verify MCP prompts can be registered and retrieved.
"""

import asyncio
from mcp.server.fastmcp.server import FastMCP

# Create test MCP server
mcp = FastMCP("TestServer")

# Register a simple test prompt
@mcp.prompt()
def test_workflow():
    """Test workflow prompt"""
    return "This is a test workflow prompt!"

# Try to list prompts
async def test_prompts():
    print("Testing MCP prompt registration...\n")

    try:
        # List prompts
        prompts = await mcp.list_prompts()
        print(f"[OK] Found {len(prompts)} registered prompts:")
        for prompt in prompts:
            print(f"  - Name: {prompt.name}")
            print(f"    Description: {prompt.description}")

            # Try to get the prompt
            result = await mcp.get_prompt(prompt.name)
            print(f"    Content preview: {result.messages[0].content.text[:100]}...")
            print()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prompts())
