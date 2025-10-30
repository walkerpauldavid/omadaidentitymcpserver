"""
Test bearer token from bearer.txt against Omada GraphQL API

This script reads a bearer token from bearer.txt and tests it against
the Omada GraphQL API to verify it's working correctly.

Usage:
    python test_bearer_token_graphql.py
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
    """Read bearer token from bearer.txt in tests folder"""
    token_file = Path(__file__).parent / 'bearer.txt'

    if not token_file.exists():
        print(f"❌ Token file not found: {token_file}")
        print("Please create bearer.txt in the tests folder with your bearer token")
        sys.exit(1)

    with open(token_file, 'r') as f:
        token = f.read().strip()

    # Strip "Bearer " prefix if present
    token = token.replace("Bearer ", "").replace("bearer ", "").strip()

    print(f"✅ Loaded bearer token from {token_file}")
    print(f"   Token preview: {token[:30]}...")
    return token

def test_graphql_pending_approvals(base_url, token, impersonate_user, graphql_version="3.0"):
    """Test GraphQL API with a pending approvals query"""

    # Build GraphQL URL
    graphql_url = f"{base_url}/api/Domain/{graphql_version}"

    print(f"\n🔍 Testing GraphQL endpoint:")
    print(f"   URL: {graphql_url}")
    print(f"   Query: accessRequestApprovalSurveyQuestions")

    # GraphQL query for pending approvals (matches server.py)
    query = """query myAccessRequestApprovalSurveyQuestions {
  accessRequestApprovalSurveyQuestions {
    pages
    total
    data {
      reason
      surveyId
      surveyObjectKey
      workflowStep
      history
      workflowStepTitle
    }
  }
}"""

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "impersonate_user": impersonate_user
    }

    print(f"   Impersonate User: {impersonate_user}")
    print(f"   Headers: {list(headers.keys())}")

    # Prepare payload
    payload = {
        "query": query
    }

    try:
        response = requests.post(graphql_url, headers=headers, json=payload, timeout=30.0)

        print(f"\n📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                print(f"❌ GraphQL ERRORS:")
                for error in data["errors"]:
                    print(f"   - {error.get('message', 'Unknown error')}")
                    if "extensions" in error:
                        print(f"     Extensions: {json.dumps(error['extensions'], indent=6)}")
                return False

            # Success - print data
            approval_data = data.get("data", {}).get("accessRequestApprovalSurveyQuestions", {})
            approvals = approval_data.get("data", [])
            total = approval_data.get("total", 0)
            pages = approval_data.get("pages", 0)

            print(f"✅ SUCCESS! Retrieved {len(approvals)} pending approvals (total: {total}, pages: {pages})")
            print(f"\n📋 Sample Data:")
            for i, approval in enumerate(approvals[:3], 1):
                print(f"   {i}. {approval.get('workflowStepTitle', 'N/A')}")
                print(f"      Step: {approval.get('workflowStep', 'N/A')}")
                print(f"      Reason: {approval.get('reason', 'N/A')[:50]}")

            return True

        elif response.status_code == 401:
            print(f"❌ UNAUTHORIZED (401)")
            print(f"   The bearer token is invalid or expired")
            print(f"\n   Response: {response.text[:500]}")
            return False

        elif response.status_code == 403:
            print(f"❌ FORBIDDEN (403)")
            print(f"   The token is valid but lacks permissions for GraphQL API")
            print(f"\n   Response: {response.text[:500]}")
            return False

        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"\n   Response: {response.text[:1000]}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ REQUEST TIMEOUT")
        print(f"   The request took longer than 30 seconds")
        return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"   Exception type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 Omada GraphQL API Bearer Token Test")
    print("=" * 80)

    # Get Omada base URL from environment
    base_url = os.getenv("OMADA_BASE_URL")
    if not base_url:
        print("❌ OMADA_BASE_URL not found in .env file")
        sys.exit(1)

    base_url = base_url.rstrip('/')
    print(f"\n🌐 Omada Base URL: {base_url}")

    # Get GraphQL version from environment
    graphql_version = os.getenv("GRAPHQL_ENDPOINT_VERSION", "3.0")
    print(f"📊 GraphQL Version: {graphql_version}")

    # Read bearer token
    token = read_bearer_token()

    # Ask for impersonate_user (REQUIRED for GraphQL)
    print("\n📧 Enter impersonate_user email (REQUIRED for GraphQL):")
    print("   Example: ROBWOL@54MV4C.ONMICROSOFT.COM")
    impersonate_user = input("   > ").strip()

    if not impersonate_user:
        print("❌ impersonate_user is required for GraphQL API")
        sys.exit(1)

    print(f"   Will use impersonate_user: {impersonate_user}")

    # Test pending approvals endpoint
    pending_approvals_success = test_graphql_pending_approvals(base_url, token, impersonate_user, graphql_version)

    # Summary
    print("\n" + "=" * 80)
    print("📝 Test Summary:")
    print("=" * 80)
    print(f"   Pending Approvals: {'✅ PASS' if pending_approvals_success else '❌ FAIL'}")

    if pending_approvals_success:
        print(f"\n🎉 Test passed! Bearer token is valid for GraphQL API")
        return 0
    else:
        print(f"\n❌ Bearer token validation failed for GraphQL API")
        print(f"\nTroubleshooting:")
        print(f"   1. Check that bearer.txt contains a valid token")
        print(f"   2. Verify the token hasn't expired (typically 1 hour)")
        print(f"   3. Ensure impersonate_user email is correct")
        print(f"   4. GraphQL may require client credentials token instead of device code")
        print(f"   5. Check token signature key - GraphQL may use different validation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
