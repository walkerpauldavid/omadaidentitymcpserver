#!/usr/bin/env python3
"""
Fresh GraphQL test class using exact query from GraphQL-GetContextsForIdentity.txt
"""
import os
import asyncio
import httpx
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

class OmadaGraphQLTester:
    """Test class for Omada GraphQL API using exact query from file"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # OAuth2 configuration from .env
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID") 
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.omada_base_url = os.getenv("OMADA_BASE_URL")
        self.oauth2_scope = os.getenv("OAUTH2_SCOPE", "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default")
        
        # Validate required environment variables
        if not all([self.tenant_id, self.client_id, self.client_secret, self.omada_base_url]):
            raise ValueError("Missing required environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET, OMADA_BASE_URL")
        
        # Token URL
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        # GraphQL endpoint
        self.graphql_url = f"{self.omada_base_url}/api/Domain/2.6"
        
        # Cached token
        self._cached_token = None
    
    async def get_oauth_token(self):
        """Get OAuth2 access token from Azure AD"""
        print("[TOKEN] Getting OAuth2 token...")
        
        # Check if we have a valid cached token
        if (self._cached_token and 
            "expires_at" in self._cached_token and 
            datetime.now() < self._cached_token["expires_at"]):
            print("[TOKEN] Using cached token")
            return self._cached_token["access_token"]
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.oauth2_scope
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                # Add expiry timestamp for caching
                expires_in = token_data.get("expires_in", 3600)
                token_data["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                self._cached_token = token_data
                
                print(f"[TOKEN] [SUCCESS] Got new token: {token_data['access_token'][:50]}...")
                return token_data["access_token"]
                
            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
                
                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")
            except Exception as e:
                raise Exception(f"Token request failed: {str(e)}")
    
    async def test_graphql_contexts(self, impersonate_user: str = "ROBWOL@54MV4C.ONMICROSOFT.COM"):
        """Test GraphQL contexts query using exact query from GraphQL-GetContextsForIdentity.txt"""
        
        print("\n" + "="*80)
        print("TESTING OMADA GRAPHQL CONTEXTS QUERY")
        print("="*80)
        
        try:
            # Get OAuth token
            access_token = await self.get_oauth_token()
            
            # GraphQL query matching the working Postman format
            graphql_query = {
                "query": """query accessRequest {
    accessRequest {
        contexts(identityIds:["e3e869c4-369a-476e-a969-d57059d0b1e4"]){ 
            id
            name
         }
    }
}""",
                "variables": {}
            }
            
            # Headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "impersonate_user": impersonate_user
            }
            
            print(f"\n[REQUEST] Sending GraphQL request")
            print(f"URL: {self.graphql_url}")
            print(f"Headers:")
            for key, value in headers.items():
                if key == "Authorization":
                    print(f"  {key}: Bearer {value.split(' ')[1][:20]}...")
                else:
                    print(f"  {key}: {value}")
            
            print(f"\nGraphQL Query:")
            print(graphql_query["query"])
            
            # Make GraphQL request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_url,
                    json=graphql_query,
                    headers=headers,
                    timeout=30.0
                )
                
                print(f"\n[RESPONSE] Status Code: {response.status_code}")
                print(f"Response Headers:")
                for key, value in response.headers.items():
                    print(f"  {key}: {value}")
                
                print(f"\nResponse Body:")
                
                if response.status_code == 200:
                    result = response.json()
                    print(json.dumps(result, indent=2))
                    
                    # Extract contexts from the new query structure
                    if ('data' in result and 'accessRequest' in result['data']):
                        access_request_obj = result['data']['accessRequest']
                        contexts = access_request_obj.get('contexts', [])
                        
                        print(f"\n[SUCCESS] Found {len(contexts)} contexts for identity")
                        
                        print(f"[CONTEXTS] Contexts found:")
                        for i, context in enumerate(contexts, 1):
                            print(f"  {i}. {context.get('name', 'N/A')} (ID: {context.get('id', 'N/A')})")
                        
                        return {
                            "status": "success",
                            "contexts": contexts,
                            "contexts_count": len(contexts),
                            "identity_id": "e3e869c4-369a-476e-a969-d57059d0b1e4"
                        }
                    else:
                        print("[WARNING] No contexts found in response")
                        return {
                            "status": "no_contexts",
                            "response": result
                        }
                else:
                    error_body = response.text
                    print(error_body)
                    
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "error": error_body
                    }
                    
        except Exception as e:
            print(f"\n[ERROR] Exception occurred: {str(e)}")
            return {
                "status": "exception",
                "error": str(e),
                "error_type": type(e).__name__
            }

async def main():
    """Main test function"""
    
    try:
        # Create tester instance
        tester = OmadaGraphQLTester()
        
        # Run the test (will use default impersonate_user)
        result = await tester.test_graphql_contexts()
        
        print(f"\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Contexts found: {result['contexts_count']}")
            print(f"Identity ID queried: {result['identity_id']}")
        elif result['status'] == 'error':
            print(f"HTTP Status: {result['status_code']}")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())