import asyncio
import json
import httpx
from server import get_cached_token
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_graphql_access_requests():
    """Test GraphQL access requests endpoint with OAuth token and impersonate-user header"""
    print("=== TESTING GRAPHQL ACCESS REQUESTS ENDPOINT ===")
    
    try:
        # Get OAuth access token
        print("Getting OAuth access token...")
        token_info = await get_cached_token()
        token = token_info.get('access_token')
        if not token:
            raise Exception("Failed to obtain access token")
        print("[SUCCESS] Successfully obtained access token")
        
        # First try to discover the schema structure for accessRequests
        introspection_query = {
            "query": """query IntrospectionQuery {
  __schema {
    queryType {
      fields {
        name
        type {
          name
          kind
          fields {
            name
            type {
              name
            }
          }
        }
      }
    }
  }
}"""
        }
        
        # Try 'data' field for the items within PaginationListAccessRequest  
        graphql_query = {
            "query": """query MyQuery {
  accessRequests {
    total
    data {
      id
      beneficiary {
        firstName
        id
        lastName
        identityId
      }
    }
  }
}"""
        }
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "impersonate-user": "pawa@omada.net"
        }
        
        # Get Omada base URL from environment
        omada_base_url = os.getenv("OMADA_BASE_URL")
        if not omada_base_url:
            raise Exception("OMADA_BASE_URL not found in environment variables")
        
        # GraphQL endpoint format: api/Domain/{{ApiVersion}} where ApiVersion is 2.6
        graphql_url = f"{omada_base_url}/api/Domain/2.6"
        
        print(f"Making GraphQL request to: {graphql_url}")
        print(f"Impersonating user: pawa@omada.net")
        
        # Make the GraphQL request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                graphql_url,
                json=graphql_query,
                headers=headers,
                timeout=30.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Check if response is JSON
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    result = response.json()
                    print("[SUCCESS] GraphQL request successful!")
                    print("\n=== RESPONSE DATA ===")
                    print(json.dumps(result, indent=2))
                else:
                    print(f"[INFO] Received non-JSON response (content-type: {content_type})")
                    print("Response body (first 500 chars):")
                    print(response.text[:500])
                    print("...")
                    return
                
                # Parse and display access requests
                if 'data' in result and 'accessRequests' in result['data']:
                    access_requests_obj = result['data']['accessRequests']
                    total = access_requests_obj.get('total', 0)
                    access_requests = access_requests_obj.get('data', [])
                    
                    print(f"\n=== FOUND {total} ACCESS REQUESTS ({len(access_requests)} returned) ===")
                    
                    for i, request in enumerate(access_requests, 1):
                        request_id = request.get('id', 'N/A')
                        beneficiary = request.get('beneficiary', {})
                        
                        first_name = beneficiary.get('firstName', 'N/A')
                        last_name = beneficiary.get('lastName', 'N/A')
                        identity_id = beneficiary.get('identityId', 'N/A')
                        beneficiary_id = beneficiary.get('id', 'N/A')
                        
                        print(f"{i}. Request ID: {request_id}")
                        print(f"   Beneficiary: {first_name} {last_name}")
                        print(f"   Identity ID: {identity_id}")
                        print(f"   Beneficiary ID: {beneficiary_id}")
                        print()
                        
                    if total == 0:
                        print("No access requests found for the impersonated user.")
                        
                else:
                    print("No access requests found in response")
                    
            else:
                print(f"[FAILED] GraphQL request failed with status {response.status_code}")
                print(f"Response body: {response.text}")
                
    except Exception as e:
        print(f"[ERROR] Error during GraphQL test: {str(e)}")
        print(f"Error type: {type(e).__name__}")

async def main():
    """Run the GraphQL test"""
    await test_graphql_access_requests()

if __name__ == "__main__":
    asyncio.run(main())