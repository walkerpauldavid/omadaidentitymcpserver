#!/usr/bin/env python3
"""
Test script for MCP Completions

This script demonstrates how to test completions by directly calling the completion function.
"""

import sys
from completions import register_completions
from mcp.server.fastmcp.server import FastMCP

def test_completions():
    """Test all completion scenarios."""

    print("Testing MCP Completions")
    print("=" * 80)

    # Create a temporary FastMCP instance
    mcp = FastMCP("TestServer")

    # Register the completions
    register_completions(mcp)

    print("\nCompletions registered successfully!")
    print()

    # Test cases: (argument_name, argument_value, description)
    test_cases = [
        ("system_id", "", "System IDs"),
        ("resource_type_name", "", "Resource Type Names"),
        ("field", "", "Identity Field Names"),
        ("operator", "", "OData Operators"),
        ("compliance_status", "", "Compliance Status Values"),
        ("workflow_step", "", "Workflow Steps"),
        ("status", "", "Status Values"),
        ("unknown_field", "", "Unknown Field (should return empty)"),
    ]

    for arg_name, arg_value, description in test_cases:
        print(f"\n{description} (argument: {arg_name})")
        print("-" * 80)

        # Access the completion handler
        if hasattr(mcp, '_completions') and mcp._completions:
            # Get the completion function
            completion_func = list(mcp._completions.values())[0]

            # Call it synchronously for testing (in real use it's async)
            import asyncio
            results = asyncio.run(completion_func.fn(arg_name, arg_value))

            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i:2d}. {result}")
                print(f"\nTotal: {len(results)} suggestions")
            else:
                print("  (no suggestions)")
        else:
            print("  ERROR: Completions not found")

    print("\n" + "=" * 80)
    print("Testing complete!")

def test_specific_completion(arg_name: str):
    """Test a specific completion argument."""

    print(f"Testing completion for: {arg_name}")
    print("=" * 80)

    # Create a temporary FastMCP instance
    mcp = FastMCP("TestServer")
    register_completions(mcp)

    # Access the completion handler
    if hasattr(mcp, '_completions') and mcp._completions:
        completion_func = list(mcp._completions.values())[0]

        import asyncio
        results = asyncio.run(completion_func.fn(arg_name, ""))

        print(f"\nSuggestions for '{arg_name}':")
        print("-" * 80)

        if results:
            for i, result in enumerate(results, 1):
                print(f"{i:2d}. {result}")
            print(f"\nTotal: {len(results)} suggestions")
        else:
            print("(no suggestions)")
    else:
        print("ERROR: Completions not registered")

    print("=" * 80)

def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        # Test specific argument
        arg_name = sys.argv[1]
        test_specific_completion(arg_name)
    else:
        # Test all completions
        test_completions()

if __name__ == "__main__":
    main()
