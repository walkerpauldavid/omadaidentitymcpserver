#!/usr/bin/env python3
"""
Test script for get_pending_approvals function.

This script tests the get_pending_approvals function with different workflow step filters.
"""

import asyncio
import json
from server import get_pending_approvals

# Default test parameters
DEFAULT_IMPERSONATE_USER = "ROBWOL@54MV4C.ONMICROSOFT.COM"
DEFAULT_WORKFLOW_STEP = "ResourceOwnerApproval"

async def test_get_pending_approvals():
    """Test get_pending_approvals with various scenarios."""

    print("=" * 80)
    print("TEST: Get Pending Approvals")
    print("=" * 80)

    # Test 1: With default workflow step filter (ResourceOwnerApproval)
    print("\n" + "=" * 80)
    print("TEST 1: Get pending approvals for ResourceOwnerApproval")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print()

    result1 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step=DEFAULT_WORKFLOW_STEP
    )

    print("Response:")
    print(result1)
    print()

    # Parse and display summary
    try:
        data1 = json.loads(result1)
        if data1.get("status") == "success":
            print(f"✅ Success! Found {data1.get('total_approvals', 0)} pending approvals")
            print(f"   Returned: {data1.get('approvals_returned', 0)} approvals")
            print(f"   Pages: {data1.get('pages', 0)}")

            # Display first approval if available
            if data1.get('approvals'):
                first_approval = data1['approvals'][0]
                print(f"\n   First Approval:")
                print(f"   - Survey ID: {first_approval.get('surveyId', 'N/A')}")
                print(f"   - Workflow Step: {first_approval.get('workflowStep', 'N/A')}")
                print(f"   - Workflow Step Title: {first_approval.get('workflowStepTitle', 'N/A')}")
                print(f"   - Reason: {first_approval.get('reason', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {data1.get('message', 'Unknown error')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    # Test 2: ManagerApproval workflow step
    print("\n" + "=" * 80)
    print("TEST 2: Get pending approvals for ManagerApproval")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: ManagerApproval")
    print()

    result2 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step="ManagerApproval"
    )

    print("Response:")
    print(result2)
    print()

    try:
        data2 = json.loads(result2)
        if data2.get("status") == "success":
            print(f"✅ Success! Found {data2.get('total_approvals', 0)} pending approvals")
        else:
            print(f"❌ Error: {data2.get('message', 'Unknown error')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    # Test 3: SystemOwnerApproval workflow step
    print("\n" + "=" * 80)
    print("TEST 3: Get pending approvals for SystemOwnerApproval")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: SystemOwnerApproval")
    print()

    result3 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step="SystemOwnerApproval"
    )

    print("Response:")
    print(result3)
    print()

    try:
        data3 = json.loads(result3)
        if data3.get("status") == "success":
            print(f"✅ Success! Found {data3.get('total_approvals', 0)} pending approvals")
        else:
            print(f"❌ Error: {data3.get('message', 'Unknown error')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    # Test 4: All pending approvals (no filter)
    print("\n" + "=" * 80)
    print("TEST 4: Get all pending approvals (no workflow step filter)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: None (all)")
    print()

    result4 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER
    )

    print("Response:")
    print(result4)
    print()

    try:
        data4 = json.loads(result4)
        if data4.get("status") == "success":
            print(f"✅ Success! Found {data4.get('total_approvals', 0)} total pending approvals")
            print(f"   Returned: {data4.get('approvals_returned', 0)} approvals")

            # Count approvals by workflow step
            if data4.get('approvals'):
                workflow_counts = {}
                for approval in data4['approvals']:
                    step = approval.get('workflowStep', 'Unknown')
                    workflow_counts[step] = workflow_counts.get(step, 0) + 1

                print(f"\n   Breakdown by Workflow Step:")
                for step, count in workflow_counts.items():
                    print(f"   - {step}: {count}")
        else:
            print(f"❌ Error: {data4.get('message', 'Unknown error')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    # Test 5: Invalid workflow step (should fail validation)
    print("\n" + "=" * 80)
    print("TEST 5: Invalid workflow step (should fail)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: InvalidStep")
    print()

    result5 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step="InvalidStep"
    )

    print("Response:")
    print(result5)
    print()

    try:
        data5 = json.loads(result5)
        if data5.get("status") == "error" and data5.get("error_type") == "ValidationError":
            print(f"✅ Validation correctly failed: {data5.get('message', 'N/A')}")
        else:
            print(f"❌ Unexpected result - should have failed validation")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    print("Starting get_pending_approvals tests...")
    print()
    asyncio.run(test_get_pending_approvals())
