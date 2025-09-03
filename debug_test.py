import asyncio
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def debug_token():
    """Debug the token generation and API call step by step"""
    
    # Get credentials
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID") 
    client_secret = os.getenv("CLIENT_SECRET")
    oauth2_scope = os.getenv("OAUTH2_SCOPE")
    omada_base_url = os.getenv("OMADA_BASE_URL")
    
    print(f"TENANT_ID: {tenant_id}")
    print(f"CLIENT_ID: {client_id}")
    print(f"CLIENT_SECRET: {client_secret[:10]}...")
    print(f"OAUTH2_SCOPE: {oauth2_scope}")
    print(f"OMADA_BASE_URL: {omada_base_url}")
    print()
    
    # Step 1: Get token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": oauth2_scope
    }
    
    print("Step 1: Getting token...")
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=token_data,
            timeout=30.0
        )
        
        if token_response.status_code == 200:
            token_info = token_response.json()
            bearer_token = f"Bearer {token_info['access_token']}"
            print("Token obtained successfully!")
            print(f"Token preview: {bearer_token[:50]}...")
            print()
            
            # Step 2: Test API call
            api_url = f"{omada_base_url}/OData/DataObjects/Identity?$filter=FIRSTNAME eq 'Emma' and LASTNAME eq 'Taylor'"
            headers = {
                "Authorization": bearer_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            print("Step 2: Testing API call...")
            print(f"URL: {api_url}")
            print(f"Authorization header: {bearer_token[:30]}...")
            
            api_response = await client.get(api_url, headers=headers, timeout=30.0)
            
            print(f"Status Code: {api_response.status_code}")
            if api_response.status_code == 200:
                print("SUCCESS!")
                data = api_response.json()
                print(f"Found {len(data.get('value', []))} identities")
            else:
                print("FAILED!")
                print(f"Response: {api_response.text}")
                
        else:
            print(f"Token request failed: {token_response.status_code}")
            print(f"Response: {token_response.text}")

if __name__ == "__main__":
    asyncio.run(debug_token())