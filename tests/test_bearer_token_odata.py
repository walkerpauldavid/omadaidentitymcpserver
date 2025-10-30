"""
Test bearer token from bearer.txt against Omada OData API

This script reads a bearer token from bearer.txt and tests it against
the Omada OData API to verify it's working correctly.

Usage:
    python test_bearer_token_odata.py
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add parent directory to path to import from .env
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(parent_dir / '.env')

def read_bearer_token():
    """Read bearer token from bearer.txt in utility folder"""
    token_file = Path(__file__).parent / 'bearer.txt'

    if not token_file.exists():
        print(f"❌ Token file not found: {token_file}")
        print("Please create bearer.txt in the utility folder with your bearer token")
        sys.exit(1)

    with open(token_file, 'r') as f:
        token = f.read().strip()

    # Strip "Bearer " prefix if present
    token = token.replace("Bearer ", "").replace("bearer ", "").strip()

    print(f"✅ Loaded bearer token from {token_file}")
    print(f"   Token preview: {token[:30]}...")
    return token

def test_odata_identity(base_url, token, impersonate_user=None):
    """Test OData API with a simple Identity query"""

    # Build OData URL - get top 5 identities
    endpoint_url = f"{base_url}/OData/DataObjects/Identity?$top=5&$select=Id,FIRSTNAME,LASTNAME,EMAIL"

    print(f"\n🔍 Testing OData endpoint:")
    print(f"   URL: {endpoint_url}")

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Add impersonate_user header if provided (required for user-delegated tokens)
    if impersonate_user:
        headers["impersonate_user"] = impersonate_user
        print(f"   Impersonate User: {impersonate_user}")

    print(f"   Headers: {list(headers.keys())}")

    try:
        response = requests.get(endpoint_url, headers=headers, timeout=30.0)

        print(f"\n📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            identities = data.get("value", [])
            count = len(identities)

            print(f"✅ SUCCESS! Retrieved {count} identities")
            print(f"\n📋 Sample Data:")
            for i, identity in enumerate(identities[:3], 1):
                print(f"   {i}. {identity.get('FIRSTNAME', 'N/A')} {identity.get('LASTNAME', 'N/A')} ({identity.get('EMAIL', 'N/A')})")

            return True

        elif response.status_code == 401:
            print(f"❌ UNAUTHORIZED (401)")
            print(f"   The bearer token is invalid or expired")
            print(f"\n   Response: {response.text[:500]}")
            return False

        elif response.status_code == 403:
            print(f"❌ FORBIDDEN (403)")
            print(f"   The token is valid but lacks permissions for OData API")
            print(f"\n   Response: {response.text[:500]}")
            return False

        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"\n   Response: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ REQUEST TIMEOUT")
        print(f"   The request took longer than 30 seconds")
        return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"   Exception type: {type(e).__name__}")
        return False

def test_odata_resource(base_url, token):
    """Test OData API with a Resource query"""

    # Build OData URL - get top 5 resources
    endpoint_url = f"{base_url}/OData/DataObjects/Resource?$top=5&$select=Id,Name,Description"

    print(f"\n🔍 Testing OData Resource endpoint:")
    print(f"   URL: {endpoint_url}")

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.get(endpoint_url, headers=headers, timeout=30.0)

        print(f"\n📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            resources = data.get("value", [])
            count = len(resources)

            print(f"✅ SUCCESS! Retrieved {count} resources")
            print(f"\n📋 Sample Data:")
            for i, resource in enumerate(resources[:3], 1):
                print(f"   {i}. {resource.get('Name', 'N/A')} - {resource.get('Description', 'N/A')[:50]}")

            return True

        else:
            print(f"⚠️  Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 Omada OData API Bearer Token Test")
    print("=" * 80)

    # Get Omada base URL from environment
    base_url = os.getenv("OMADA_BASE_URL")
    if not base_url:
        print("❌ OMADA_BASE_URL not found in .env file")
        sys.exit(1)

    base_url = base_url.rstrip('/')
    print(f"\n🌐 Omada Base URL: {base_url}")

    # Read bearer token
    token = read_bearer_token()

    # Ask for impersonate_user (optional but recommended for device code tokens)
    print("\n📧 Enter impersonate_user email (or press Enter to skip):")
    print("   Example: ROBWOL@54MV4C.ONMICROSOFT.COM")
    impersonate_user = input("   > ").strip()

    if impersonate_user:
        print(f"   Will use impersonate_user: {impersonate_user}")
    else:
        print(f"   No impersonate_user specified (may cause 403 for user-delegated tokens)")

    # Test Identity endpoint
    identity_success = test_odata_identity(base_url, token, impersonate_user)

    # Test Resource endpoint
    resource_success = test_odata_resource(base_url, token)

    # Summary
    print("\n" + "=" * 80)
    print("📝 Test Summary:")
    print("=" * 80)
    print(f"   Identity Query: {'✅ PASS' if identity_success else '❌ FAIL'}")
    print(f"   Resource Query: {'✅ PASS' if resource_success else '❌ FAIL'}")

    if identity_success and resource_success:
        print(f"\n🎉 All tests passed! Bearer token is valid for OData API")
        return 0
    elif identity_success:
        print(f"\n⚠️  Token works for Identity but not Resource - check permissions")
        return 1
    else:
        print(f"\n❌ Bearer token validation failed")
        print(f"\nTroubleshooting:")
        print(f"   1. Check that bearer.txt contains a valid token")
        print(f"   2. Verify the token hasn't expired (typically 1 hour)")
        print(f"   3. Ensure the token has OData API permissions")
        print(f"   4. Run device authentication again to get a fresh token")
        return 1

if __name__ == "__main__":
    sys.exit(main())
