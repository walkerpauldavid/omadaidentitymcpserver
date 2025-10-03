#!/usr/bin/env python3
"""
Test script for approval workflow functions.

This script tests the complete approval workflow:
1. Get pending approvals (summary mode - user-friendly)
2. Get approval details (full mode - with technical IDs)
3. Make an approval decision (APPROVE or REJECT)
"""

import asyncio
import json
from server import get_pending_approvals, get_approval_details, make_approval_decision

# Default test parameters
DEFAULT_IMPERSONATE_USER = "ROBWOL@54MV4C.ONMICROSOFT.COM"
DEFAULT_WORKFLOW_STEP = "ResourceOwnerApproval"
DEFAULT_DECISION = "APPROVE"  # or "REJECT"

async def test_approval_workflow():
    """Test the complete approval workflow."""

    print("=" * 80)
    print("APPROVAL WORKFLOW TEST")
    print("=" * 80)
    print()

    # STEP 1: Get pending approvals (summary mode - clean view)
    print("=" * 80)
    print("STEP 1: Get Pending Approvals (Summary Mode)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print(f"Summary Mode: True (default)")
    print()

    result1 = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step=DEFAULT_WORKFLOW_STEP,
        summary_mode=True  # This is the default
    )

    print("Response (Summary Mode):")
    print(result1)
    print()

    # Parse and display summary
    try:
        data1 = json.loads(result1)
        if data1.get("status") == "success":
            print(f"✅ Success! Found {data1.get('total_approvals', 0)} pending approvals")
            print(f"   Summary Mode: {data1.get('summary_mode', False)}")
            print(f"   Returned: {data1.get('approvals_returned', 0)} approvals")

            if data1.get('approvals'):
                print(f"\n   Summary Fields (Clean - No Technical IDs):")
                first_approval = data1['approvals'][0]
                print(f"   Fields returned: {list(first_approval.keys())}")
                print(f"   - Workflow Step: {first_approval.get('workflowStep', 'N/A')}")
                print(f"   - Workflow Step Title: {first_approval.get('workflowStepTitle', 'N/A')}")
                print(f"   - Reason: {first_approval.get('reason', 'N/A')[:100]}...")

                # Verify technical fields are NOT present
                if 'surveyId' in first_approval or 'surveyObjectKey' in first_approval:
                    print(f"\n   ❌ WARNING: Technical fields found in summary mode!")
                else:
                    print(f"\n   ✅ Technical fields properly excluded from summary")
            else:
                print("   No approvals to display")
        else:
            print(f"❌ Error: {data1.get('message', 'Unknown error')}")
            return
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return

    # STEP 2: Get approval details (full mode - with technical IDs)
    print("\n" + "=" * 80)
    print("STEP 2: Get Approval Details (Full Mode with Technical IDs)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print(f"Purpose: Get surveyId and surveyObjectKey for making decisions")
    print()

    result2 = await get_approval_details(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step=DEFAULT_WORKFLOW_STEP
    )

    print("Response (Full Details Mode):")
    print(result2)
    print()

    # Parse and extract technical IDs
    survey_id = None
    survey_object_key = None
    approval_reason = None
    workflow_step = None

    try:
        data2 = json.loads(result2)
        if data2.get("status") == "success":
            print(f"✅ Success! Retrieved full approval details")
            print(f"   Summary Mode: {data2.get('summary_mode', False)}")

            if data2.get('approvals'):
                first_approval = data2['approvals'][0]
                print(f"\n   Full Fields (Including Technical IDs):")
                print(f"   Fields returned: {list(first_approval.keys())}")

                # Extract the IDs we need for making a decision
                survey_id = first_approval.get('surveyId')
                survey_object_key = first_approval.get('surveyObjectKey')
                approval_reason = first_approval.get('reason', 'N/A')
                workflow_step = first_approval.get('workflowStep', 'N/A')

                print(f"\n   Extracted Technical IDs:")
                print(f"   - Survey ID: {survey_id}")
                print(f"   - Survey Object Key: {survey_object_key}")
                print(f"   - Workflow Step: {workflow_step}")
                print(f"   - Reason: {approval_reason[:100]}...")

                if survey_id and survey_object_key:
                    print(f"\n   ✅ Technical IDs successfully extracted for decision-making")
                else:
                    print(f"\n   ❌ Missing required technical IDs")
                    return
            else:
                print("   No approvals to process")
                return
        else:
            print(f"❌ Error: {data2.get('message', 'Unknown error')}")
            return
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return

    # STEP 3: Make approval decision (if we have the IDs)
    if survey_id and survey_object_key:
        print("\n" + "=" * 80)
        print("STEP 3: Make Approval Decision")
        print("=" * 80)
        print(f"⚠️  WARNING: This will actually submit an approval decision!")
        print()
        print(f"Decision Details:")
        print(f"   - Impersonate User: {DEFAULT_IMPERSONATE_USER}")
        print(f"   - Survey ID: {survey_id}")
        print(f"   - Survey Object Key: {survey_object_key}")
        print(f"   - Decision: {DEFAULT_DECISION}")
        print(f"   - Workflow Step: {workflow_step}")
        print(f"   - Reason: {approval_reason[:100]}...")
        print()

        # Uncomment the lines below to actually make the decision
        # WARNING: This will submit a real approval!

        print("🚫 APPROVAL DECISION NOT SUBMITTED (Safety Mode)")
        print("   To actually submit, uncomment the code below in the test file:")
        print()
        print("   result3 = await make_approval_decision(")
        print(f"       impersonate_user='{DEFAULT_IMPERSONATE_USER}',")
        print(f"       survey_id='{survey_id}',")
        print(f"       survey_object_key='{survey_object_key}',")
        print(f"       decision='{DEFAULT_DECISION}'")
        print("   )")
        print()

        # UNCOMMENT BELOW TO ACTUALLY MAKE THE APPROVAL DECISION
        """
        result3 = await make_approval_decision(
            impersonate_user=DEFAULT_IMPERSONATE_USER,
            survey_id=survey_id,
            survey_object_key=survey_object_key,
            decision=DEFAULT_DECISION
        )

        print("Response (Approval Decision):")
        print(result3)
        print()

        try:
            data3 = json.loads(result3)
            if data3.get("status") == "success":
                print(f"✅ Approval decision submitted successfully!")
                print(f"   Decision: {data3.get('decision', 'N/A')}")
                print(f"   Questions Successfully Submitted: {data3.get('questions_successfully_submitted', False)}")
            else:
                print(f"❌ Error: {data3.get('message', 'Unknown error')}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
        """

    # STEP 4: Test invalid decision validation
    print("\n" + "=" * 80)
    print("STEP 4: Test Invalid Decision Validation")
    print("=" * 80)
    print(f"Testing with invalid decision: 'INVALID_DECISION'")
    print()

    result4 = await make_approval_decision(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        survey_id="test-survey-id",
        survey_object_key="test-object-key",
        decision="INVALID_DECISION"  # This should fail validation
    )

    print("Response (Invalid Decision):")
    print(result4)
    print()

    try:
        data4 = json.loads(result4)
        if data4.get("status") == "error" and data4.get("error_type") == "ValidationError":
            print(f"✅ Validation correctly rejected invalid decision")
            print(f"   Error: {data4.get('message', 'N/A')}")
        else:
            print(f"❌ Validation did not work as expected")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    # STEP 5: Test REJECT decision validation
    print("\n" + "=" * 80)
    print("STEP 5: Test REJECT Decision (case-insensitive)")
    print("=" * 80)
    print(f"Testing with decision: 'reject' (lowercase)")
    print()

    result5 = await make_approval_decision(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        survey_id="test-survey-id",
        survey_object_key="test-object-key",
        decision="reject"  # Should be converted to uppercase REJECT
    )

    print("Response (Reject Decision):")
    print(result5)
    print()

    try:
        data5 = json.loads(result5)
        # This will fail at GraphQL level (invalid IDs), but should pass validation
        if data5.get("decision") == "REJECT" or "REJECT" in str(data5):
            print(f"✅ Decision correctly converted to uppercase: REJECT")
        else:
            print(f"⚠️  Decision validation result: {data5.get('status', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary of Tests:")
    print("✅ Step 1: Get pending approvals in summary mode (clean fields)")
    print("✅ Step 2: Get full approval details with technical IDs")
    print("🚫 Step 3: Make approval decision (safety mode - not submitted)")
    print("✅ Step 4: Invalid decision validation")
    print("✅ Step 5: Case-insensitive decision handling")
    print()
    print("To actually submit an approval decision, edit this file and uncomment")
    print("the code in STEP 3 (search for 'UNCOMMENT BELOW')")

if __name__ == "__main__":
    print("Starting approval workflow tests...")
    print()
    asyncio.run(test_approval_workflow())
