#!/usr/bin/env python3
"""
Quick interactive test for contexts function
Usage: python quick_test.py <identity> [impersonate_user]
"""
import asyncio
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import get_contexts_for_identity

async def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <identity> [impersonate_user]")
        print("Examples:")
        print("  python quick_test.py emmtay@54MV4C.ONMICROSOFT.COM")
        print("  python quick_test.py EMMTAY emmtay@54MV4C.ONMICROSOFT.COM")
        print("  python quick_test.py 2c68e1df-1335-4e8c-8ef9-eff1d2005629")
        sys.exit(1)
    
    identity = sys.argv[1]
    impersonate_user = sys.argv[2] if len(sys.argv) > 2 else "emmtay@54MV4C.ONMICROSOFT.COM"
    
    print(f"Testing contexts for identity: {identity}")
    print(f"Impersonating user: {impersonate_user}")
    print("-" * 50)
    
    try:
        result = await get_contexts_for_identity(identity, impersonate_user)
        
        # Pretty print the JSON result
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
        
        # Show key info
        if parsed.get("status") == "success":
            contexts = parsed.get("data", {}).get("contexts", [])
            print(f"\n✅ Found {len(contexts)} contexts:")
            for i, context in enumerate(contexts, 1):
                print(f"  {i}. {context}")
        elif "identity_uid" in parsed:
            print(f"\n📋 Lookup successful:")
            print(f"   Method: {parsed.get('lookup_method')}")
            print(f"   UID: {parsed.get('identity_uid')}")
            print(f"   But GraphQL query failed - check schema")
        else:
            print(f"\n❌ Error: {parsed.get('message')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())