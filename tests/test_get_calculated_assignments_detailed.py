"""
Test script for get_calculated_assignments_detailed function
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the current directory to the path to import server module
sys.path.insert(0, os.path.dirname(__file__))

from server import get_calculated_assignments_detailed

# Load environment variables
load_dotenv()

async def test_basic():
    """Test with mandatory parameters only"""

    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email

    print("="*80)
    print("TEST 1: Basic test - mandatory parameters only")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Omada Base URL: {os.getenv('OMADA_BASE_URL')}")
    print("="*80)
    print()

    try:
        result = await get_calculated_assignments_detailed(
            identity_id=identity_id,
            impersonate_user=impersonate_user
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_with_filters():
    """Test with optional filter parameters"""

    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email

    print("\n" + "="*80)
    print("TEST 2: With all filters")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Resource Type: Active Directory - Security Group")
    print(f"Compliance Status: NOT APPROVED")
    print("="*80)
    print()

    try:
        result = await get_calculated_assignments_detailed(
            identity_id=identity_id,
            impersonate_user=impersonate_user,
            resource_type_name="Active Directory - Security Group",
            compliance_status="NOT APPROVED"
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_compliance_filter_only():
    """Test with compliance status filter only"""

    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email

    print("\n" + "="*80)
    print("TEST 3: Compliance status filter only")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Compliance Status: NOT APPROVED")
    print("="*80)
    print()

    try:
        result = await get_calculated_assignments_detailed(
            identity_id=identity_id,
            impersonate_user=impersonate_user,
            compliance_status="NOT APPROVED"
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def test_resource_type_filter_only():
    """Test with resource type filter only"""

    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email

    print("\n" + "="*80)
    print("TEST 4: Resource type filter only")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Resource Type: Active Directory")
    print("="*80)
    print()

    try:
        result = await get_calculated_assignments_detailed(
            identity_id=identity_id,
            impersonate_user=impersonate_user,
            resource_type_name="Active Directory"
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 Starting get_calculated_assignments_detailed tests\n")

    # Run all tests
    asyncio.run(test_basic())
    asyncio.run(test_with_filters())
    asyncio.run(test_compliance_filter_only())
    asyncio.run(test_resource_type_filter_only())

    print("\n✅ All tests completed!")
