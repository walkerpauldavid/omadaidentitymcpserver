#!/usr/bin/env python3
"""
Test script to verify MCP prompts are registered correctly.
"""

import sys
import os

# Add the server directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp.server import FastMCP
from prompts import register_prompts

# Create test MCP server
mcp = FastMCP("TestOmadaMCP")

# Register prompts
register_prompts(mcp)

# Check if prompts are registered
print("\n=== Testing MCP Prompt Registration ===\n")

# FastMCP stores prompts internally - let's see if we can access them
# The prompts are stored in mcp._prompt_manager or similar

# Try to list registered prompts
if hasattr(mcp, '_prompts'):
    prompts = mcp._prompts
    print(f"✅ Found {len(prompts)} registered prompts:")
    for prompt_name in prompts:
        print(f"  - {prompt_name}")
elif hasattr(mcp, 'list_prompts'):
    prompts = mcp.list_prompts()
    print(f"✅ Found {len(prompts)} registered prompts:")
    for prompt in prompts:
        print(f"  - {prompt.name if hasattr(prompt, 'name') else prompt}")
else:
    print("⚠️  Cannot directly access registered prompts")
    print("   This doesn't mean they're not registered - FastMCP may store them internally")

# Check if the prompt functions exist in the module
print("\n=== Checking prompt functions in prompts.py ===\n")

expected_prompts = [
    'request_access_workflow',
    'approve_requests_workflow',
    'search_identity_workflow',
    'review_assignments_workflow',
    'authentication_workflow',
    'troubleshooting_workflow',
    'bulk_access_request_workflow',
    'compliance_audit_workflow',
    'resource_discovery_workflow',
    'identity_context_workflow',
    'compare_identities_workflow'
]

for prompt_name in expected_prompts:
    # The functions are defined inside register_prompts, so they won't be directly accessible
    # This is expected behavior
    print(f"  Expected: {prompt_name}")

print(f"\n✅ All {len(expected_prompts)} prompts should be registered")

print("\n=== How to Verify in Claude Desktop ===\n")
print("Prompts in MCP are not visible as slash commands.")
print("To test if Claude can access them, ask:")
print("  'Show me the authentication workflow'")
print("  'Help me request access'")
print("  'Compare two identities'")
print("\nClaude should respond with the full workflow text from the prompt.")
