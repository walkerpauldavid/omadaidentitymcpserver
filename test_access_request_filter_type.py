import asyncio
import json
from server import get_cached_token
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_access_request_filter_fields():
    """Test different field names in AccessRequestFilterInputType"""
    
    print("=== TESTING AccessRequestFilterInputType FIELDS ===")
    
    # Common field names to try
    filter_tests = [
        {"name": "beneficiaryId", "value": "a708e710-e1e6-45cc-a02d-8e0f0cc4127f"},
        {"name": "beneficiary", "value": {"identityId": "YANLER"}},
        {"name": "beneficiary", "value": {"id": "a708e710-e1e6-45cc-a02d-8e0f0cc4127f"}},
        {"name": "identityId", "value": "YANLER"},
        {"name": "requestId", "value": "e876aaa8-7651-4044-8757-1561b1555089"},
        {"name": "id", "value": "e876aaa8-7651-4044-8757-1561b1555089"},
        {"name": "status", "value": "Approved"}
    ]
    
    for test in filter_tests:
        await test_single_filter_field(test["name"], test["value"])

async def test_single_filter_field(field_name, field_value, impersonate_user="robwol@54mv4c.onmicrosoft.com"):
    """Test a single filter field"""
    print(f"\n--- Testing filter: {field_name} = {field_value} ---")
    
    # Build the GraphQL query
    graphql_query = {
        "query": f"""query GetAccessRequests {{
  accessRequests(filters: {{{field_name}: {json.dumps(field_value)}}}) {{
    total
    data {{
      id
      beneficiary {{
        id
        identityId
        displayName
      }}
      resource {{
        name
      }}
      status {{
        approvalStatus
      }}
    }}
  }}
}}"""
    }
    
    print(f"Query: {graphql_query['query']}")
    print("-" * 40)
    
    try:
        # Get OAuth access token
        token_info = await get_cached_token()
        token = token_info.get('access_token')
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "impersonate_user": impersonate_user
        }
        
        # Get Omada base URL
        omada_base_url = os.getenv("OMADA_BASE_URL")
        graphql_url = f"{omada_base_url}/api/Domain/2.6"
        
        # Make the GraphQL request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                graphql_url,
                json=graphql_query,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'accessRequests' in result['data']:
                    access_requests_obj = result['data']['accessRequests']
                    total = access_requests_obj.get('total', 0)
                    access_requests = access_requests_obj.get('data', [])
                    
                    print(f"[SUCCESS] Found {total} total requests, {len(access_requests)} returned")
                    
                    # Show first result if any
                    if access_requests:
                        req = access_requests[0]
                        beneficiary = req.get('beneficiary', {})
                        print(f"  First result: {beneficiary.get('displayName', 'N/A')} (ID: {beneficiary.get('identityId', 'N/A')})")
                        print(f"  Resource: {req.get('resource', {}).get('name', 'N/A')}")
                    else:
                        print("  No results (filter worked but no matches)")
                        
                else:
                    print("[ERROR] No accessRequests data found")
                    
            else:
                print(f"[FAILED] Status {response.status_code}")
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        for error in error_data['errors']:
                            message = error.get('message', 'Unknown error')
                            if len(message) > 100:
                                message = message[:100] + "..."
                            print(f"   Error: {message}")
                except:
                    pass
                
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_access_request_filter_fields())