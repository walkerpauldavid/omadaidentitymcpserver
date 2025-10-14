#!/usr/bin/env python3
"""
Test MCP completions via the actual MCP protocol

This script starts the server and sends completion requests via MCP protocol.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_completion(argument_name: str):
    """Test a specific completion via MCP protocol."""

    # Configure server connection
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    print(f"Testing completion for: {argument_name}")
    print("=" * 80)

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✓ Connected to MCP server")

                # Request completion
                print(f"\nRequesting completions for argument: '{argument_name}'")
                print("-" * 80)

                # Note: The MCP SDK might not expose completion/complete directly
                # This is a conceptual example - actual implementation may vary
                try:
                    # Try to get completions (this API might differ)
                    # In the actual MCP protocol, this would be:
                    # POST with method "completion/complete"
                    result = await session.send_request(
                        "completion/complete",
                        {
                            "argument": {
                                "name": argument_name,
                                "value": ""
                            }
                        }
                    )

                    if hasattr(result, 'values'):
                        print(f"\n✓ Received {len(result.values)} suggestions:\n")
                        for i, value in enumerate(result.values, 1):
                            print(f"  {i:2d}. {value}")
                    else:
                        print(f"\nResult: {result}")

                except Exception as e:
                    print(f"\n⚠ Completion request failed: {e}")
                    print("\nNote: Your MCP SDK version might not support completions yet.")
                    print("Use test_completions_direct.py for testing instead.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nFalling back to direct testing...")
        print("Run: python test_completions_direct.py")

    print("\n" + "=" * 80)

async def test_all_via_mcp():
    """Test all completions via MCP protocol."""

    test_args = [
        "system_id",
        "resource_type_name",
        "field",
        "operator"
    ]

    for arg_name in test_args:
        await test_completion(arg_name)
        print()

def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        arg_name = sys.argv[1]
        asyncio.run(test_completion(arg_name))
    else:
        asyncio.run(test_all_via_mcp())

if __name__ == "__main__":
    main()
