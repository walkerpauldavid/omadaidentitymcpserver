#!/usr/bin/env python3
"""
Simple test script for MCP Prompts in omada_mcp_server

This script tests prompts by directly importing the prompts module.
Much simpler than using the MCP client protocol.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from prompts import register_prompts
from mcp.server.fastmcp.server import FastMCP

def test_all_prompts():
    """Test all prompts by calling them directly."""

    print(">> Testing MCP Prompts")
    print("=" * 80)

    # Create a temporary FastMCP instance
    mcp = FastMCP("TestServer")

    # Register the prompts
    register_prompts(mcp)

    print("\n>> Available prompts:\n")

    # Get all registered prompts
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

    for i, name in enumerate(prompt_names, 1):
        print(f"{i:2d}. {name}")

    print("\n" + "=" * 80)
    return mcp, prompt_names

def display_prompt(mcp, prompt_name):
    """Display the content of a specific prompt."""

    print(f"\n>> Prompt: {prompt_name}")
    print("=" * 80)

    # Access the prompt through FastMCP's internal structure
    if hasattr(mcp, '_prompts') and prompt_name in mcp._prompts:
        prompt_func = mcp._prompts[prompt_name]

        # Call the prompt function to get its content
        try:
            content = prompt_func.fn()
            print(content)
        except Exception as e:
            print(f"Error calling prompt: {e}")
    else:
        print(f"Prompt '{prompt_name}' not found")

    print("\n" + "=" * 80)

def interactive_mode():
    """Interactive mode to browse prompts."""

    mcp, prompt_names = test_all_prompts()

    while True:
        print("\n>> Options:")
        print("  1-10: View specific prompt by number")
        print("  all:  View all prompts")
        print("  list: List prompts again")
        print("  quit: Exit")
        print()

        choice = input("Enter your choice: ").strip().lower()

        if choice == 'quit' or choice == 'q':
            print("\n>> Goodbye!")
            break
        elif choice == 'list':
            test_all_prompts()
        elif choice == 'all':
            for name in prompt_names:
                display_prompt(mcp, name)
                input("\nPress Enter to continue...")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(prompt_names):
                display_prompt(mcp, prompt_names[idx])
            else:
                print(f"Invalid number. Please enter 1-{len(prompt_names)}")
        else:
            # Try to use it as a prompt name
            if choice in prompt_names:
                display_prompt(mcp, choice)
            else:
                print(f"Unknown option: {choice}")

def main():
    """Main entry point."""

    if len(sys.argv) > 1:
        # Non-interactive mode: display specific prompt
        prompt_name = sys.argv[1]
        mcp = FastMCP("TestServer")
        register_prompts(mcp)

        if prompt_name == "list":
            test_all_prompts()
        else:
            display_prompt(mcp, prompt_name)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
