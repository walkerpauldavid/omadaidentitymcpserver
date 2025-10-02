import asyncio
import json
from server import get_cached_token
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_filters_parameter():
    """Test the 'filters' parameter that was suggested by the GraphQL error"""
    
    print("=== TESTING 'filters' PARAMETER (SUGGESTED BY ERROR) ===")
    
    # Test different formats for the filters parameter
    test_cases = [
        {
            "name": "Filters with OData-style string",
            "query": {
                "query": """query GetAccessRequests {
  accessRequests(filters: "beneficiary/identityId eq 'YANLER'") {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
      }
      resource {
        name
      }
    }
  }
}"""
            }
        },
        {
            "name": "Filters with JSON object",
            "query": {
                "query": """query GetAccessRequests {
  accessRequests(filters: {beneficiaryIdentityId: "YANLER"}) {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
      }
      resource {
        name
      }
    }
  }
}"""
            }
        },
        {
            "name": "Filters with array",
            "query": {
                "query": """query GetAccessRequests {
  accessRequests(filters: [{field: "beneficiary.identityId", value: "YANLER"}]) {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
      }
      resource {
        name
      }
    }
  }
}"""
            }
        }
    ]
    
    for test_case in test_cases:
        await test_single_filter(test_case["name"], test_case["query"])

async def test_single_filter(name, graphql_query, impersonate_user="robwol@54mv4c.onmicrosoft.com"):
    """Test a single GraphQL filter"""
    print(f"\n--- {name} ---")
    print(f"Query:\n{graphql_query['query']}")
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
                    
                    # Show results
                    for i, req in enumerate(access_requests[:3], 1):
                        beneficiary = req.get('beneficiary', {})
                        print(f"  {i}. Beneficiary: {beneficiary.get('displayName', 'N/A')} (ID: {beneficiary.get('identityId', 'N/A')})")
                        print(f"     Resource: {req.get('resource', {}).get('name', 'N/A')}")
                        
                else:
                    print("[ERROR] No accessRequests data found")
                    
            else:
                print(f"[FAILED] Status {response.status_code}")
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        for error in error_data['errors']:
                            print(f"   Error: {error.get('message', 'Unknown error')}")
                except:
                    pass
                print(f"   Response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_filters_parameter())