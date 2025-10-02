import asyncio
import json
from server import get_cached_token
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_graphql_filter(query_name, graphql_query, impersonate_user="robwol@54mv4c.onmicrosoft.com"):
    """Test a GraphQL query with filter"""
    print(f"\n=== TESTING: {query_name} ===")
    print(f"Query:\n{graphql_query['query']}")
    print("-" * 60)
    
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
                    
                    # Show first few results
                    for i, req in enumerate(access_requests[:3], 1):
                        beneficiary = req.get('beneficiary', {})
                        print(f"  {i}. Request ID: {req.get('id', 'N/A')}")
                        print(f"     Beneficiary: {beneficiary.get('displayName', 'N/A')} (ID: {beneficiary.get('identityId', 'N/A')})")
                        print(f"     Resource: {req.get('resource', {}).get('name', 'N/A')}")
                    
                    if len(access_requests) > 3:
                        print(f"     ... and {len(access_requests) - 3} more")
                        
                else:
                    print("[ERROR] No accessRequests data found in response")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
            else:
                print(f"[FAILED] Status {response.status_code}")
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        for error in error_data['errors']:
                            print(f"   Error: {error.get('message', 'Unknown error')}")
                except:
                    pass
                print(f"   Response: {response.text[:300]}...")
                
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")

async def main():
    print("=== TESTING GRAPHQL FILTERS FOR BENEFICIARY ===")
    
    # Test 1: No filter (baseline)
    no_filter_query = {
        "query": """query GetAccessRequests {
  accessRequests {
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
    
    # Test 2: Filter by beneficiary identityId (GraphQL argument style)
    filter_by_identity_id_args = {
        "query": """query GetAccessRequests($beneficiaryIdentityId: String) {
  accessRequests(beneficiaryIdentityId: $beneficiaryIdentityId) {
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
}""",
        "variables": {
            "beneficiaryIdentityId": "YANLER"
        }
    }
    
    # Test 3: Filter using where clause style
    filter_where_identity_id = {
        "query": """query GetAccessRequests {
  accessRequests(where: {beneficiary: {identityId: {eq: "YANLER"}}}) {
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
    
    # Test 4: Filter by beneficiary ID (GUID)
    filter_by_beneficiary_id = {
        "query": """query GetAccessRequests {
  accessRequests(beneficiaryId: "a708e710-e1e6-45cc-a02d-8e0f0cc4127f") {
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
    
    # Test 5: Filter using different parameter name
    filter_identity_param = {
        "query": """query GetAccessRequests {
  accessRequests(identityId: "YANLER") {
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
    
    # Test 6: Filter using filter parameter
    filter_parameter = {
        "query": """query GetAccessRequests {
  accessRequests(filter: "beneficiary/identityId eq 'YANLER'") {
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
    
    # Run all tests
    await test_graphql_filter("No Filter (Baseline)", no_filter_query)
    await test_graphql_filter("Filter by beneficiaryIdentityId (Args)", filter_by_identity_id_args)
    await test_graphql_filter("Filter with Where Clause", filter_where_identity_id)
    await test_graphql_filter("Filter by Beneficiary ID (GUID)", filter_by_beneficiary_id)
    await test_graphql_filter("Filter by identityId Parameter", filter_identity_param)
    await test_graphql_filter("Filter with OData-style Filter", filter_parameter)

if __name__ == "__main__":
    asyncio.run(main())