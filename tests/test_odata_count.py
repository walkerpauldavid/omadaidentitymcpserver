import asyncio
import httpx
import json
import os
from dotenv import load_dotenv
from server import get_cached_token

# Load environment variables
load_dotenv()

async def test_odata_count_endpoint(entity_type: str):
    """Test if an EntityType supports the OData $count endpoint."""
    try:
        # Get base URL
        omada_base_url = os.getenv("OMADA_BASE_URL")
        if not omada_base_url:
            return f"[FAILED] {entity_type}: No OMADA_BASE_URL configured"
        
        omada_base_url = omada_base_url.rstrip('/')
        
        # Build the count endpoint URL
        if entity_type == "CalculatedAssignments":
            endpoint_url = f"{omada_base_url}/OData/BuiltIn/{entity_type}/$count"
        else:
            endpoint_url = f"{omada_base_url}/OData/DataObjects/{entity_type}/$count"
        
        # Get the Azure token
        token_data = await get_cached_token()
        bearer_token = f"Bearer {token_data['access_token']}"
        
        # Make API call to test the count endpoint
        headers = {
            "Authorization": bearer_token,
            "Content-Type": "application/json",
            "Accept": "text/plain"  # $count endpoints typically return plain text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint_url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                count_value = response.text.strip()
                try:
                    count_int = int(count_value)
                    return f"[SUCCESS] {entity_type}: Supports $count - Found {count_int} objects"
                except ValueError:
                    return f"[WARNING]  {entity_type}: $count returned non-numeric: '{count_value}'"
            elif response.status_code == 404:
                return f"[FAILED] {entity_type}: $count endpoint not found (404)"
            elif response.status_code == 400:
                return f"[FAILED] {entity_type}: Bad request (400) - {response.text[:100]}"
            elif response.status_code == 401:
                return f"[FAILED] {entity_type}: Authentication failed (401)"
            elif response.status_code == 403:
                return f"[FAILED] {entity_type}: Access forbidden (403)"
            else:
                return f"[FAILED] {entity_type}: HTTP {response.status_code} - {response.text[:100]}"
                
    except Exception as e:
        return f"[FAILED] {entity_type}: Error - {str(e)}"

async def main():
    print("=== TESTING ODATA $COUNT ENDPOINT SUPPORT ===")
    print("Testing each EntityType to see if it supports the OData $count endpoint...")
    print()
    
    entity_types = [
        "Identity", 
        "Resource", 
        "Role", 
        "Account", 
        "Application", 
        "System", 
        "CalculatedAssignments"
    ]
    
    for entity_type in entity_types:
        result = await test_odata_count_endpoint(entity_type)
        print(result)
    
    print()
    print("=== TESTING FILTERED COUNT ENDPOINTS ===")
    print("Testing if filtered $count works (e.g., with resource type filters)...")
    print()
    
    # Test filtered count for Application Roles
    try:
        omada_base_url = os.getenv("OMADA_BASE_URL", "").rstrip('/')
        resource_type_id = os.getenv("RESOURCE_TYPE_APPLICATION_ROLES")
        
        if resource_type_id:
            endpoint_url = f"{omada_base_url}/OData/DataObjects/Resource/$count?$filter=Systemref/Id eq {resource_type_id}"
            
            token_data = await get_cached_token()
            bearer_token = f"Bearer {token_data['access_token']}"
            
            headers = {
                "Authorization": bearer_token,
                "Content-Type": "application/json",
                "Accept": "text/plain"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint_url, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    count_value = response.text.strip()
                    print(f"[SUCCESS] Filtered Resource Count (Application Roles): {count_value} objects")
                else:
                    print(f"[FAILED] Filtered Resource Count: HTTP {response.status_code}")
        else:
            print("[WARNING]  Filtered Resource Count: No RESOURCE_TYPE_APPLICATION_ROLES configured")
            
    except Exception as e:
        print(f"[FAILED] Filtered Resource Count: Error - {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())