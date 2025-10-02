import asyncio
import json
from server import create_access_request

async def test_create_access_request():
    """Test harness for the create_access_request function"""

    print("=== TESTING CREATE ACCESS REQUEST FUNCTION ===")
    print()

    # Test data - you may need to adjust these values based on your Omada environment
    test_cases = [
        {
            "name": "Request VPN for Berry Black (Expected Success)",
            "params": {
                "impersonate_user": "berbla@54MV4C.ONMICROSOFT.COM",
                "reason": "Test reason",
                "context": "Business context for testing access request",
                "resources": '{"id": "fa58b111-7e91-4723-b998-2df8c0758568"}'
            }
        }
    ]

    # Run each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test {i}: {test_case['name']} ---")

        try:
            # Call the function with test parameters
            result = await create_access_request(**test_case['params'])

            # Parse and display the result
            parsed_result = json.loads(result)
            status = parsed_result.get('status', 'unknown')

            print(f"Status: {status}")

            # Show full HTTP body and GraphQL details
            print("\n📋 FULL HTTP REQUEST/RESPONSE DETAILS:")
            print("=" * 50)
            if 'endpoint' in parsed_result:
                print(f"GraphQL Endpoint: {parsed_result['endpoint']}")

            # Show HTTP debug information if available
            if 'http_debug' in parsed_result:
                http_debug = parsed_result['http_debug']

                print("\n🔍 RAW HTTP REQUEST BODY:")
                if http_debug.get('raw_request_body'):
                    print(http_debug['raw_request_body'])
                else:
                    print("Not available")

                print("\n🔍 RAW HTTP RESPONSE BODY:")
                if http_debug.get('raw_response_body'):
                    print(http_debug['raw_response_body'])
                else:
                    print("Not available")

                print("\n🔍 REQUEST HEADERS:")
                if http_debug.get('request_headers'):
                    for key, value in http_debug['request_headers'].items():
                        print(f"  {key}: {value}")
                else:
                    print("Not available")

            # Show GraphQL errors if present
            if 'errors' in parsed_result:
                print("\n❌ GraphQL Errors:")
                print(json.dumps(parsed_result['errors'], indent=2))

            # Show the complete parsed result for debugging
            print("\n📄 Complete Parsed Response:")
            print(json.dumps(parsed_result, indent=2))
            print("=" * 50)

            if status == 'success':
                print(f"✅ SUCCESS")
                print(f"   Access Request ID: {parsed_result.get('access_request_id', 'N/A')}")
                print(f"   Message: {parsed_result.get('message', 'N/A')}")
                print(f"   Impersonated User: {parsed_result.get('impersonated_user', 'N/A')}")

                request_details = parsed_result.get('request_details', {})
                if request_details:
                    print(f"   Request Details:")
                    print(f"     Reason: {request_details.get('reason', 'N/A')}")
                    print(f"     Identity ID: {request_details.get('identity_id', 'N/A')}")
                    print(f"     Resources: {request_details.get('resources', 'N/A')}")
                    if request_details.get('valid_from'):
                        print(f"     Valid From: {request_details.get('valid_from')}")
                    if request_details.get('valid_to'):
                        print(f"     Valid To: {request_details.get('valid_to')}")
                    if request_details.get('context'):
                        print(f"     Context: {request_details.get('context')}")

            elif status == 'error':
                error_type = parsed_result.get('error_type', 'Unknown')
                message = parsed_result.get('message', 'No message provided')

                if error_type == 'ValidationError':
                    print(f"❌ VALIDATION ERROR (Expected)")
                else:
                    print(f"❌ ERROR")

                print(f"   Error Type: {error_type}")
                print(f"   Message: {message}")

                # Show additional error details if available
                if 'errors' in parsed_result:
                    print(f"   GraphQL Errors: {parsed_result['errors']}")
                if 'response_body' in parsed_result:
                    print(f"   Response Body: {parsed_result['response_body']}")
                if 'endpoint' in parsed_result:
                    print(f"   Endpoint: {parsed_result['endpoint']}")
            else:
                print(f"⚠️ UNEXPECTED STATUS: {status}")
                print(f"   Full Response: {json.dumps(parsed_result, indent=2)}")

        except Exception as e:
            print(f"💥 TEST EXECUTION FAILED: {str(e)}")
            print(f"   Error Type: {type(e).__name__}")

        print()

async def interactive_test():
    """Interactive test function where you can input your own parameters"""

    print("=== INTERACTIVE CREATE ACCESS REQUEST TEST ===")
    print("Enter the parameters for creating an access request:")
    print("(Press Enter for optional fields to skip them)")
    print()

    # Get user input
    impersonate_user = input("Impersonate User (email): ").strip()
    reason = input("Reason: ").strip()
    context = input("Context (business context): ").strip()
    resources = input("Resources (JSON format): ").strip()

    # Optional fields
    valid_from = input("Valid From (optional): ").strip() or None
    valid_to = input("Valid To (optional): ").strip() or None

    print("\n--- Executing Request ---")

    try:
        result = await create_access_request(
            impersonate_user=impersonate_user,
            reason=reason,
            context=context,
            resources=resources,
            valid_from=valid_from,
            valid_to=valid_to
        )

        print("Result:")
        parsed_result = json.loads(result)

        # Show full HTTP body and GraphQL details
        print("\n📋 FULL HTTP REQUEST/RESPONSE DETAILS:")
        print("=" * 50)
        if 'endpoint' in parsed_result:
            print(f"GraphQL Endpoint: {parsed_result['endpoint']}")

        # Show HTTP debug information if available
        if 'http_debug' in parsed_result:
            http_debug = parsed_result['http_debug']

            print("\n🔍 RAW HTTP REQUEST BODY:")
            if http_debug.get('raw_request_body'):
                print(http_debug['raw_request_body'])
            else:
                print("Not available")

            print("\n🔍 RAW HTTP RESPONSE BODY:")
            if http_debug.get('raw_response_body'):
                print(http_debug['raw_response_body'])
            else:
                print("Not available")

            print("\n🔍 REQUEST HEADERS:")
            if http_debug.get('request_headers'):
                for key, value in http_debug['request_headers'].items():
                    print(f"  {key}: {value}")
            else:
                print("Not available")

        # Show GraphQL errors if present
        if 'errors' in parsed_result:
            print("\n❌ GraphQL Errors:")
            print(json.dumps(parsed_result['errors'], indent=2))

        # Show the complete parsed result
        print("\n📄 Complete Parsed Response:")
        print(json.dumps(parsed_result, indent=2))
        print("=" * 50)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Run automated test cases")
    print("2. Interactive test")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "2":
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_create_access_request())