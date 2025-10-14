#!/usr/bin/env python3
"""
Test actual prompts from prompts.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp.server import FastMCP
from prompts import register_prompts

# Create test MCP server
mcp = FastMCP("TestOmadaMCP")

# Register actual prompts
print("Registering prompts from prompts.py...")
register_prompts(mcp)

# Try to list prompts
async def test_prompts():
    print("\nTesting actual prompt registration...\n")

    try:
        # List prompts
        prompts = await mcp.list_prompts()
        print(f"[OK] Found {len(prompts)} registered prompts:\n")

        for i, prompt in enumerate(prompts, 1):
            print(f"{i}. Name: {prompt.name}")
            print(f"   Description: {prompt.description[:80]}..." if len(prompt.description) > 80 else f"   Description: {prompt.description}")

            # Try to get the prompt content
            try:
                result = await mcp.get_prompt(prompt.name)
                if result.messages:
                    content = result.messages[0].content.text
                    preview = content[:150].replace('\n', ' ')
                    print(f"   Content preview: {preview}...")
            except Exception as e:
                print(f"   [ERROR getting content]: {e}")

            print()

        # Specifically look for compare_identities_workflow
        print("\n" + "="*60)
        print("Looking specifically for 'compare_identities_workflow'...")
        print("="*60 + "\n")

        found = False
        for prompt in prompts:
            if 'compare' in prompt.name.lower():
                found = True
                print(f"[FOUND] {prompt.name}")
                result = await mcp.get_prompt(prompt.name)
                content = result.messages[0].content.text
                print(f"\nFirst 300 characters:")
                print(content[:300])
                print("...")
                break

        if not found:
            print("[NOT FOUND] compare_identities_workflow is not in the registered prompts!")
            print("\nAvailable prompt names:")
            for prompt in prompts:
                print(f"  - {prompt.name}")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prompts())
