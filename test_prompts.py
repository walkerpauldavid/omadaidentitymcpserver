#!/usr/bin/env python3
"""
Test script for MCP Prompts in omada_mcp_server

This script demonstrates how to test MCP prompts programmatically.
You can also test prompts through Claude Desktop or any MCP client.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_prompts():
    """Test all prompts by listing and retrieving them."""

    # Configure server connection
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    print("🚀 Starting MCP server...")
    print("=" * 80)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            print("\n✅ Connected to MCP server")
            print("=" * 80)

            # List all available prompts
            print("\n📋 Listing all available prompts...")
            print("-" * 80)
            prompts_result = await session.list_prompts()

            if hasattr(prompts_result, 'prompts'):
                prompts = prompts_result.prompts
                print(f"\n✨ Found {len(prompts)} prompts:\n")

                for i, prompt in enumerate(prompts, 1):
                    print(f"{i}. {prompt.name}")
                    if hasattr(prompt, 'description') and prompt.description:
                        print(f"   Description: {prompt.description}")
                    print()

            # Test each prompt by retrieving its content
            print("\n🔍 Testing each prompt...")
            print("=" * 80)

            prompt_names = [
                "request_access_workflow",
                "approve_requests_workflow",
                "search_identity_workflow",
                "review_assignments_workflow",
                "authentication_workflow",
                "troubleshooting_workflow",
                "bulk_access_request_workflow",
                "compliance_audit_workflow",
                "resource_discovery_workflow",
                "identity_context_workflow"
            ]

            for prompt_name in prompt_names:
                print(f"\n📝 Testing prompt: {prompt_name}")
                print("-" * 80)

                try:
                    # Get the prompt content
                    result = await session.get_prompt(prompt_name)

                    if hasattr(result, 'messages'):
                        print(f"✅ Successfully retrieved prompt")
                        print(f"   Messages: {len(result.messages)}")

                        # Display first 200 characters of the prompt content
                        if result.messages:
                            content = result.messages[0].content
                            if hasattr(content, 'text'):
                                preview = content.text[:200] + "..." if len(content.text) > 200 else content.text
                                print(f"   Preview: {preview}")
                    else:
                        print(f"❌ Unexpected result format")

                except Exception as e:
                    print(f"❌ Error retrieving prompt: {e}")

            print("\n" + "=" * 80)
            print("✅ Prompt testing complete!")
            print("=" * 80)

async def test_specific_prompt(prompt_name: str):
    """Test a specific prompt and display its full content."""

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    print(f"🔍 Testing prompt: {prompt_name}")
    print("=" * 80)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                result = await session.get_prompt(prompt_name)

                if hasattr(result, 'messages') and result.messages:
                    content = result.messages[0].content
                    if hasattr(content, 'text'):
                        print("\n📄 Full Prompt Content:")
                        print("-" * 80)
                        print(content.text)
                        print("-" * 80)
                    else:
                        print(f"Content: {content}")
                else:
                    print("No content found in prompt")

            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        # Test a specific prompt
        prompt_name = sys.argv[1]
        asyncio.run(test_specific_prompt(prompt_name))
    else:
        # Test all prompts
        asyncio.run(test_prompts())

if __name__ == "__main__":
    main()
