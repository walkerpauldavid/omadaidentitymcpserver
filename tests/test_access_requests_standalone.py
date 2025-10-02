#!/usr/bin/env python3
"""
Standalone test script for the get_access_requests function.
"""

import asyncio
import sys
import os
from server import get_access_requests

async def main():
    """Test the get_access_requests function directly."""

    # Default impersonate user
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"

    # Check if user provided email
    if len(sys.argv) > 1:
        impersonate_user = sys.argv[1]

    print(f"🔍 Testing get_access_requests function")
    print(f"📧 Impersonating user: {impersonate_user}")
    print("=" * 60)

    try:
        # Test 1: No filter
        print("\n🔸 Test 1: Get all access requests (no filter)")
        result1 = await get_access_requests(impersonate_user)
        print(result1)

        # Test 2: With status filter
        print("\n🔸 Test 2: Get pending access requests (status filter)")
        result2 = await get_access_requests(impersonate_user, "status", "PENDING")
        print(result2)

        # Test 3: With different filter
        print("\n🔸 Test 3: Get approved access requests")
        result3 = await get_access_requests(impersonate_user, "status", "APPROVED")
        print(result3)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("\n✅ Testing completed!")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)