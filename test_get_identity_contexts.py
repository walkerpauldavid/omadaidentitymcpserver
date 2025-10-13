#!/usr/bin/env python3
"""
Test script for get_identity_contexts to verify logging works
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import the server module
import server

async def test_get_identity_contexts():
    """Test get_identity_contexts with a known identity."""

    print("Testing get_identity_contexts...")
    print("=" * 80)

    # You'll need to provide actual values here
    identity_id = "7ac8b482-272f-4bf0-9339-ce3742c2b4ca"  # Replace with actual UId
    impersonate_user = "hanulr@54mv4c.onmicrosoft.com"    # Replace with actual email
    bearer_token = input("Enter bearer token: ").strip()

    print(f"\nCalling get_identity_contexts with:")
    print(f"  identity_id: {identity_id}")
    print(f"  impersonate_user: {impersonate_user}")
    print(f"  bearer_token: {bearer_token[:20]}...")
    print()

    # Call the function
    result = await server.get_identity_contexts(
        identity_id=identity_id,
        impersonate_user=impersonate_user,
        bearer_token=bearer_token
    )

    print("\nResult:")
    print("=" * 80)
    print(result)
    print("=" * 80)

    print("\nCheck the log file for debug output:")
    print(f"  {os.getenv('LOG_FILE', 'omada_mcp_server.log')}")

if __name__ == "__main__":
    asyncio.run(test_get_identity_contexts())
