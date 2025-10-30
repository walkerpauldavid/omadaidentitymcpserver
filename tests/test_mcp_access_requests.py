import asyncio
import json

async def test_mcp_access_requests():
    """Test the MCP server's get_access_requests tool"""
    
    # Import the server module to access the MCP tools
    from server import get_access_requests
    
    print("=== TESTING MCP ACCESS REQUESTS TOOL ===")
    print("Email addresses to test:")
    test_emails = [
        "robwol@54mvc.onmicrosoft.com",
        "pawa@omada.net",
        "admin@example.com"  # This should fail as it's likely not a valid user
    ]
    
    for email in test_emails:
        print(f"\n--- Testing with: {email} ---")
        try:
            result = await get_access_requests(email)
            # Parse the JSON result to display nicely
            parsed = json.loads(result)
            
            status = parsed.get('status', 'unknown')
            total = parsed.get('total_requests', 0)
            
            print(f"Status: {status}")
            print(f"Total Requests: {total}")
            
            if status == 'success' and total > 0:
                print("Access Requests:")
                for i, request in enumerate(parsed['data']['access_requests'], 1):
                    beneficiary = request.get('beneficiary', {})
                    print(f"  {i}. ID: {request.get('id', 'N/A')}")
                    print(f"     Beneficiary: {beneficiary.get('firstName', '')} {beneficiary.get('lastName', '')}")
                    print(f"     Identity ID: {beneficiary.get('identityId', 'N/A')}")
            elif status == 'success':
                print("No access requests found for this user.")
            else:
                print(f"Error: {parsed.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mcp_access_requests())