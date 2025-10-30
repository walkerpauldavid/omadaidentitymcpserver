#!/usr/bin/env python3
"""
Test script for approval workflow functions.

This script tests the complete approval workflow with selectable test scenarios:
1. Get pending approvals (summary mode - user-friendly)
2. Get approval details (full mode - with technical IDs)
3. Make an approval decision (APPROVE or REJECT)
4. Test invalid decision validation
5. Test case-insensitive decision handling

Usage:
    # Run all tests
    python test_make_approval_decision.py

    # Run specific tests (comma-separated)
    python test_make_approval_decision.py 1,2,3

    # Run single test
    python test_make_approval_decision.py 3
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import get_pending_approvals, get_approval_details, make_approval_decision

# Default test parameters
DEFAULT_IMPERSONATE_USER = "ROBWOL@54MV4C.ONMICROSOFT.COM"
DEFAULT_WORKFLOW_STEP = "ResourceOwnerApproval"
DEFAULT_DECISION = "APPROVE"  # or "REJECT"

# Test configuration - which tests to run
def parse_test_selection():
    """Parse command line arguments to determine which tests to run."""
    if len(sys.argv) > 1:
        test_arg = sys.argv[1]
        try:
            # Parse comma-separated test numbers
            selected = [int(x.strip()) for x in test_arg.split(',')]
            return selected
        except ValueError:
            print(f"Invalid test selection: {test_arg}")
            print("Usage: python test_make_approval_decision.py [1,2,3,4,5]")
            sys.exit(1)
    else:
        # Default: run only tests 1 and 2 (safe tests, no approval submission)
        return [1, 2]

async def test_step_1():
    """STEP 1: Get pending approvals (summary mode - clean view)"""
    print("=" * 80)
    print("STEP 1: Get Pending Approvals (Summary Mode)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print(f"Summary Mode: True (default)")
    print()

    result = await get_pending_approvals(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step=DEFAULT_WORKFLOW_STEP,
        summary_mode=True  # This is the default
    )

    print("Response (Summary Mode):")
    print(result)
    print()

    # Parse and display summary
    try:
        data = json.loads(result)
        if data.get("status") == "success":
            print(f"✅ Success! Found {data.get('total_approvals', 0)} pending approvals")
            print(f"   Summary Mode: {data.get('summary_mode', False)}")
            print(f"   Returned: {data.get('approvals_returned', 0)} approvals")

            if data.get('approvals'):
                print(f"\n   Summary Fields (Clean - No Technical IDs):")
                first_approval = data['approvals'][0]
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
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

async def test_step_2():
    """STEP 2: Get approval details (full mode - with technical IDs)"""
    print("=" * 80)
    print("STEP 2: Get Approval Details (Full Mode with Technical IDs)")
    print("=" * 80)
    print(f"Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print(f"Purpose: Get surveyId and surveyObjectKey for making decisions")
    print()

    result = await get_approval_details(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        workflow_step=DEFAULT_WORKFLOW_STEP
    )

    print("Response (Full Details Mode):")
    print(result)
    print()

    # Parse and extract technical IDs
    survey_id = None
    survey_object_key = None

    try:
        data = json.loads(result)
        if data.get("status") == "success":
            print(f"✅ Success! Retrieved full approval details")
            print(f"   Summary Mode: {data.get('summary_mode', False)}")

            if data.get('approvals'):
                first_approval = data['approvals'][0]
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
                    return survey_id, survey_object_key, workflow_step, approval_reason
                else:
                    print(f"\n   ❌ Missing required technical IDs")
                    return None, None, None, None
            else:
                print("   No approvals to process")
                return None, None, None, None
        else:
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
            return None, None, None, None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return None, None, None, None

async def test_step_3(survey_id=None, survey_object_key=None, workflow_step=None, approval_reason=None):
    """STEP 3: Make approval decision"""
    print("=" * 80)
    print("STEP 3: Make Approval Decision")
    print("=" * 80)

    # If IDs not provided, try to get them
    if not survey_id or not survey_object_key:
        print("⚠️  No survey IDs provided. Fetching from Step 2...")
        survey_id, survey_object_key, workflow_step, approval_reason = await test_step_2()
        print()

    if not survey_id or not survey_object_key:
        print("❌ Cannot proceed without survey IDs. Run Step 2 first or provide valid IDs.")
        return

    print(f"⚠️  WARNING: This will actually submit an approval decision!")
    print()
    print(f"Decision Details:")
    print(f"   - Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"   - Survey ID: {survey_id}")
    print(f"   - Survey Object Key: {survey_object_key}")
    print(f"   - Decision: {DEFAULT_DECISION}")
    print(f"   - Workflow Step: {workflow_step}")
    print(f"   - Reason: {approval_reason[:100] if approval_reason else 'N/A'}...")
    print()
    print(f"📋 The GraphQL mutation will be logged to the log file with DEBUG level")
    print(f"   Check: LOG_LEVEL_make_approval_decision=DEBUG in .env")
    print()

    # Confirm before submitting
    print("🚫 Submitting approval decision...")
    print()

    result = await make_approval_decision(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        survey_id=survey_id,
        survey_object_key=survey_object_key,
        decision=DEFAULT_DECISION
    )

    print("Response (Approval Decision):")
    print(result)
    print()

    try:
        data = json.loads(result)
        if data.get("status") == "success":
            print(f"✅ Approval decision submitted successfully!")
            print(f"   Decision: {data.get('decision', 'N/A')}")
            print(f"   Questions Successfully Submitted: {data.get('questions_successfully_submitted', False)}")
            print()
            print(f"💡 TIP: Check the log file for the GraphQL mutation that was sent")
        elif data.get("status") == "error":
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
            print(f"   Error Type: {data.get('error_type', 'N/A')}")
            if 'errors' in data:
                print(f"   GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
            print()
            print(f"💡 TIP: Check the log file for the GraphQL mutation and error details")
        else:
            print(f"⚠️  Unexpected status: {data.get('status', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

async def test_step_4():
    """STEP 4: Test invalid decision validation"""
    print("=" * 80)
    print("STEP 4: Test Invalid Decision Validation")
    print("=" * 80)
    print(f"Testing with invalid decision: 'INVALID_DECISION'")
    print()

    result = await make_approval_decision(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        survey_id="test-survey-id",
        survey_object_key="test-object-key",
        decision="INVALID_DECISION"  # This should fail validation
    )

    print("Response (Invalid Decision):")
    print(result)
    print()

    try:
        data = json.loads(result)
        if data.get("status") == "error" and data.get("error_type") == "ValidationError":
            print(f"✅ Validation correctly rejected invalid decision")
            print(f"   Error: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Validation did not work as expected")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

async def test_step_5():
    """STEP 5: Test REJECT decision validation"""
    print("=" * 80)
    print("STEP 5: Test REJECT Decision (case-insensitive)")
    print("=" * 80)
    print(f"Testing with decision: 'reject' (lowercase)")
    print()

    result = await make_approval_decision(
        impersonate_user=DEFAULT_IMPERSONATE_USER,
        survey_id="test-survey-id",
        survey_object_key="test-object-key",
        decision="reject"  # Should be converted to uppercase REJECT
    )

    print("Response (Reject Decision):")
    print(result)
    print()

    try:
        data = json.loads(result)
        # This will fail at GraphQL level (invalid IDs), but should pass validation
        if data.get("decision") == "REJECT" or "REJECT" in str(data):
            print(f"✅ Decision correctly converted to uppercase: REJECT")
        else:
            print(f"⚠️  Decision validation result: {data.get('status', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")

async def main():
    """Main test execution."""
    selected_tests = parse_test_selection()

    print("=" * 80)
    print("APPROVAL WORKFLOW TEST SUITE")
    print("=" * 80)
    print()
    print(f"Selected Tests: {selected_tests}")
    print(f"Default Impersonate User: {DEFAULT_IMPERSONATE_USER}")
    print(f"Default Workflow Step: {DEFAULT_WORKFLOW_STEP}")
    print(f"Default Decision: {DEFAULT_DECISION}")
    print()
    print("Available Tests:")
    print("  1 - Get pending approvals (summary mode)")
    print("  2 - Get approval details (full mode with IDs)")
    print("  3 - Make approval decision (LIVE - submits real approval!)")
    print("  4 - Test invalid decision validation")
    print("  5 - Test case-insensitive decision")
    print()
    print("💡 TIP: Make sure LOG_LEVEL_make_approval_decision=DEBUG in .env")
    print("   to see GraphQL mutations in the log file")
    print()

    # Store IDs from step 2 for step 3
    survey_id = None
    survey_object_key = None
    workflow_step = None
    approval_reason = None

    for test_num in selected_tests:
        if test_num == 1:
            await test_step_1()
        elif test_num == 2:
            survey_id, survey_object_key, workflow_step, approval_reason = await test_step_2()
        elif test_num == 3:
            await test_step_3(survey_id, survey_object_key, workflow_step, approval_reason)
        elif test_num == 4:
            await test_step_4()
        elif test_num == 5:
            await test_step_5()
        else:
            print(f"❌ Invalid test number: {test_num}")

        print()  # Add spacing between tests

    print("=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print()
    print("Tests Run:", selected_tests)
    print()
    print("Usage examples:")
    print("  python test_make_approval_decision.py        # Run tests 1,2 (default, safe)")
    print("  python test_make_approval_decision.py 1,2,3  # Run tests 1,2,3")
    print("  python test_make_approval_decision.py 3      # Run only test 3 (approval)")
    print("  python test_make_approval_decision.py 1,2,4,5 # All except live approval")

if __name__ == "__main__":
    asyncio.run(main())
