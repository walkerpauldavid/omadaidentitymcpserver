"""
Test script for check_access_request_policy function (SoD Policy Check)
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the current directory to the path to import server module
sys.path.insert(0, os.path.dirname(__file__))

from server import check_access_request_policy

# Load environment variables
load_dotenv()

async def test_check_access_request_policy_single_resource():
    """Test the check_access_request_policy function with a single resource"""

    # Test parameters - modify these as needed
    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    resource_ids = "95d4f3dd-a2c1-4838-8830-f39a56e2f1e7"  # Single resource ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email
    bearer_token = os.getenv("BEARER_TOKEN", "")  # Get from environment

    print("="*80)
    print("Test 1: Single Resource SoD Policy Check")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Resource ID: {resource_ids}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Bearer Token: {'*' * 20 if bearer_token else 'NOT SET'}")
    print("="*80)
    print()

    try:
        # Call the function
        result = await check_access_request_policy(
            identity_id=identity_id,
            resource_ids=resource_ids,
            impersonate_user=impersonate_user,
            bearer_token=bearer_token
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_check_access_request_policy_multiple_resources():
    """Test the check_access_request_policy function with multiple resources"""

    # Test parameters - modify these as needed
    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    resource_ids = "95d4f3dd-a2c1-4838-8830-f39a56e2f1e7,29fb5413-d26b-4e7b-94ea-250b046432e8"  # Multiple resource IDs
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email
    bearer_token = os.getenv("BEARER_TOKEN", "")  # Get from environment

    print("="*80)
    print("Test 2: Multiple Resources SoD Policy Check")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Resource IDs: {resource_ids}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Bearer Token: {'*' * 20 if bearer_token else 'NOT SET'}")
    print("="*80)
    print()

    try:
        # Call the function
        result = await check_access_request_policy(
            identity_id=identity_id,
            resource_ids=resource_ids,
            impersonate_user=impersonate_user,
            bearer_token=bearer_token
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_check_access_request_policy_validation():
    """Test validation - missing identity_id"""

    identity_id = ""  # Empty identity_id
    resource_ids = "95d4f3dd-a2c1-4838-8830-f39a56e2f1e7"
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"
    bearer_token = os.getenv("BEARER_TOKEN", "")

    print("="*80)
    print("Test 3: Validation - Empty Identity ID")
    print("="*80)
    print(f"Identity ID: '{identity_id}' (empty)")
    print(f"Resource IDs: {resource_ids}")
    print("="*80)
    print()

    try:
        result = await check_access_request_policy(
            identity_id=identity_id,
            resource_ids=resource_ids,
            impersonate_user=impersonate_user,
            bearer_token=bearer_token
        )

        print("✅ Result (should show validation error):")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

async def test_check_access_request_policy_no_resources():
    """Test validation - no resources"""

    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"
    resource_ids = ""  # Empty resource_ids
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"
    bearer_token = os.getenv("BEARER_TOKEN", "")

    print("="*80)
    print("Test 4: Validation - No Resource IDs")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Resource IDs: '{resource_ids}' (empty)")
    print("="*80)
    print()

    try:
        result = await check_access_request_policy(
            identity_id=identity_id,
            resource_ids=resource_ids,
            impersonate_user=impersonate_user,
            bearer_token=bearer_token
        )

        print("✅ Result (should show validation error):")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    print("\n🚀 Starting check_access_request_policy tests\n")

    # Run all tests
    asyncio.run(test_check_access_request_policy_single_resource())
    print("\n" + "-"*80 + "\n")

    asyncio.run(test_check_access_request_policy_multiple_resources())
    print("\n" + "-"*80 + "\n")

    asyncio.run(test_check_access_request_policy_validation())
    print("\n" + "-"*80 + "\n")

    asyncio.run(test_check_access_request_policy_no_resources())

    print("\n✅ All tests completed!")
