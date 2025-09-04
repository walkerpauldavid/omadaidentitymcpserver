# server.py
import os
from typing import Any, Dict, Optional
import httpx
from mcp.server.fastmcp.server import FastMCP, Context
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import json
import urllib.parse

# Load environment variables
load_dotenv()

# Custom Exception Classes
class OmadaServerError(Exception):
    """Base exception for Omada server errors"""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class AuthenticationError(OmadaServerError):
    """Raised when authentication fails"""
    pass

class ODataQueryError(OmadaServerError):
    """Raised when OData query is malformed or fails"""
    pass

mcp = FastMCP("HelloMCP")

def _build_odata_filter(field_name: str, value: str, operator: str) -> str:
    """
    Build an OData filter expression based on the operator.
    
    Args:
        field_name: The field name (e.g., "FIRSTNAME", "LASTNAME")
        value: The value to filter by
        operator: The OData operator (eq, ne, contains, startswith, etc.)
        
    Returns:
        OData filter expression string
    """
    # Escape single quotes in value
    escaped_value = value.replace("'", "''")
    
    if operator in ["eq", "ne", "gt", "ge", "lt", "le", "like"]:
        # Standard comparison operators (including LIKE)
        return f"{field_name} {operator} '{escaped_value}'"
    elif operator == "contains":
        # Contains function
        return f"contains({field_name}, '{escaped_value}')"
    elif operator == "startswith":
        # Starts with function
        return f"startswith({field_name}, '{escaped_value}')"
    elif operator == "endswith":
        # Ends with function
        return f"endswith({field_name}, '{escaped_value}')"
    elif operator == "substringof":
        # Substring of function (reverse of contains)
        return f"substringof('{escaped_value}', {field_name})"
    else:
        # Fallback to eq if unknown operator
        return f"{field_name} eq '{escaped_value}'"


class AzureOAuth2Client:
    def __init__(self):
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.access_token_url = os.getenv("ACCESS_TOKEN_URL")
        
        # Validate required environment variables
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing required environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET")
        
        # If ACCESS_TOKEN_URL is not provided, construct the standard Azure endpoint
        if not self.access_token_url:
            self.access_token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
    
    async def get_access_token(self, scope: str = None) -> Dict[str, Any]:
        """
        Get an OAuth2 access token using client credentials flow.
        
        Args:
            scope: The scope for the access token (default reads from OAUTH2_SCOPE env var)
            
        Returns:
            Dict containing token information
        """
        # Use environment variable scope if none provided
        if scope is None:
            scope = os.getenv("OAUTH2_SCOPE", "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": scope
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.access_token_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                token_data = response.json()
                
                # Add expiry timestamp for caching
                expires_in = token_data.get("expires_in", 3600)
                token_data["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                return token_data
                
            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
                
                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")
            except Exception as e:
                raise Exception(f"Token request failed: {str(e)}")

# Initialize OAuth2 client and cached token
_cached_token = None

try:
    oauth_client = AzureOAuth2Client()
except ValueError as e:
    print(f"Warning: OAuth2 client initialization failed: {e}")
    oauth_client = None

async def get_cached_token(scope: str = None) -> Dict[str, Any]:
    """Get a cached token or fetch a new one if expired."""
    global _cached_token
    
    if oauth_client is None:
        raise Exception("OAuth2 client not initialized. Check environment variables.")
    
    # Use environment variable scope if none provided
    if scope is None:
        scope = os.getenv("OAUTH2_SCOPE", "https://graph.microsoft.com/.default")
    
    # Check if we have a valid cached token
    if (_cached_token and 
        "expires_at" in _cached_token and 
        datetime.now() < _cached_token["expires_at"]):
        return _cached_token
    
    # Fetch new token
    _cached_token = await oauth_client.get_access_token(scope)
    return _cached_token

@mcp.tool()
async def query_omada_entity(entity_type: str = "Identity",
                            field_filters: list = None,
                            resource_type_id: int = None,
                            resource_type_name: str = None,
                            system_id: int = None,
                            identity_id: int = None,
                            omada_base_url: str = None,
                            scope: str = None,
                            filter_condition: str = None,
                            count_only: bool = False,
                            top: int = None,
                            skip: int = None,
                            select_fields: str = None,
                            order_by: str = None,
                            expand: str = None,
                            include_count: bool = False,
                            # Deprecated parameters - kept for backward compatibility
                            firstname: str = None, 
                            lastname: str = None,
                            firstname_operator: str = "eq",
                            lastname_operator: str = "eq") -> str:
    """
    Generic query function for any Omada entity type (Identity, Resource, Role, etc).
    
    Args:
        entity_type: Type of entity to query (Identity, Resource, Role, Account, etc)
        field_filters: List of field filters, each containing:
                      [{"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
                       {"field": "LASTNAME", "value": "Taylor", "operator": "startswith"}]
        resource_type_id: Numeric ID for resource type (Resource entities only, e.g., 1011066)
        resource_type_name: Name-based lookup for resource type (Resource entities only, e.g., "APPLICATION_ROLES")
        system_id: Numeric ID for system reference (Resource entities only, e.g., 1011066 for Systemref/Id eq 1011066)
        identity_id: Numeric ID for identity reference (CalculatedAssignments only, e.g., 1006500 for Identity/Id eq 1006500)
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        filter_condition: Custom OData filter condition
                         Examples: 
                         - "FIRSTNAME eq 'John' and LASTNAME eq 'Doe'" (Identity)
                         - "contains(DISPLAYNAME, 'Manager')" (Any entity)
                         - "Systemref/Id eq 1011066" (Resource)
        count_only: If True, returns only the count of matching records
        top: Maximum number of records to return (OData $top)
        skip: Number of records to skip (OData $skip)
        select_fields: Comma-separated list of fields to select (OData $select)
        order_by: Field(s) to order by (OData $orderby)
        expand: Comma-separated list of related entities to expand (OData $expand, e.g., "Identity,Resource,ResourceType")
        include_count: Include total count in response (adds $count=true)
        
    Returns:
        JSON response with entity data, count, or error message
    """
    try:
        # Validate entity type
        valid_entities = ["Identity", "Resource", "Role", "Account", "Application", "System", "CalculatedAssignments"]
        if entity_type not in valid_entities:
            return f"❌ Invalid entity type '{entity_type}'. Valid types: {', '.join(valid_entities)}"
        
        # Validate OData operators
        valid_operators = ["eq", "ne", "gt", "ge", "lt", "le", "like", "startswith", "endswith", "contains", "substringof"]
        if firstname_operator not in valid_operators:
            return f"❌ Invalid firstname_operator '{firstname_operator}'. Valid operators: {', '.join(valid_operators)}"
        if lastname_operator not in valid_operators:
            return f"❌ Invalid lastname_operator '{lastname_operator}'. Valid operators: {', '.join(valid_operators)}"
        
        # Get base URL from parameter or environment
        if not omada_base_url:
            omada_base_url = os.getenv("OMADA_BASE_URL")
            if not omada_base_url:
                return "❌ omada_base_url parameter or OMADA_BASE_URL environment variable required"
        
        # Remove trailing slash if present
        omada_base_url = omada_base_url.rstrip('/')
        
        # Build the endpoint URL based on entity type
        if entity_type == "CalculatedAssignments":
            endpoint_url = f"{omada_base_url}/OData/BuiltIn/{entity_type}"
        else:
            endpoint_url = f"{omada_base_url}/OData/DataObjects/{entity_type}"
        
        # Build query parameters
        query_params = {}
        
        # Handle entity-specific filtering logic
        auto_filters = []
        
        # For Resource entities, handle resource_type and system filtering
        if entity_type == "Resource":
            if resource_type_name and not resource_type_id:
                env_key = f"RESOURCE_TYPE_{resource_type_name.upper()}"
                resource_type_id = os.getenv(env_key)
                if not resource_type_id:
                    return f"❌ Resource type '{resource_type_name}' not found in environment variables. Check {env_key}"
                resource_type_id = int(resource_type_id)
            
            if resource_type_id:
                auto_filters.append(f"Systemref/Id eq {resource_type_id}")
            
            # Add system_id filter for querying resources by system (only if not already filtered by resource_type_id)
            if system_id and not resource_type_id:
                auto_filters.append(f"Systemref/Id eq {system_id}")
        
        # Handle generic field filtering for any entity type
        if field_filters:
            for field_filter in field_filters:
                if isinstance(field_filter, dict) and "field" in field_filter and "value" in field_filter:
                    field_name = field_filter["field"]
                    field_value = field_filter["value"]
                    field_operator = field_filter.get("operator", "eq")
                    auto_filters.append(_build_odata_filter(field_name, field_value, field_operator))
        
        # For Identity entities, handle deprecated firstname/lastname filtering (backward compatibility)
        elif entity_type == "Identity":
            if firstname:
                auto_filters.append(_build_odata_filter("FIRSTNAME", firstname, firstname_operator))
            if lastname:
                auto_filters.append(_build_odata_filter("LASTNAME", lastname, lastname_operator))
        
        # For CalculatedAssignments entities, handle identity_id filtering
        elif entity_type == "CalculatedAssignments":
            if identity_id:
                auto_filters.append(f"Identity/Id eq {identity_id}")
        
        # Combine automatic filters with custom filter condition
        all_filters = []
        if auto_filters:
            all_filters.extend(auto_filters)
        if filter_condition:
            all_filters.append(f"({filter_condition})")
        
        if all_filters:
            query_params['$filter'] = " and ".join(all_filters)
        
        # Add count parameter if requested
        if count_only:
            query_params['$count'] = 'true'
            query_params['$top'] = '0'  # Don't return actual records, just count
        else:
            # Add other OData parameters
            if top:
                query_params['$top'] = str(top)
            if skip:
                query_params['$skip'] = str(skip)
            if select_fields:
                query_params['$select'] = select_fields
            if order_by:
                query_params['$orderby'] = order_by
            if expand:
                query_params['$expand'] = expand
            if include_count:
                query_params['$count'] = 'true'
        
        # Construct final URL with query parameters
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            endpoint_url = f"{endpoint_url}?{query_string}"
        
        # Get the Azure token
        token_data = await get_cached_token(scope)
        bearer_token = f"Bearer {token_data['access_token']}"
        
        # Make API call to Omada
        headers = {
            "Authorization": bearer_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint_url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                # Parse the response
                data = response.json()
                
                if count_only:
                    # Return just the count
                    count = data.get("@odata.count", len(data.get("value", [])))
                    result = {
                        "status": "success",
                        "entity_type": entity_type,
                        "count": count,
                        "filter": query_params.get('$filter', 'none'),
                        "endpoint": endpoint_url
                    }
                else:
                    # Return full data with metadata
                    entities_found = len(data.get("value", []))
                    total_count = data.get("@odata.count")  # Available if $count=true was included
                    
                    result = {
                        "status": "success",
                        "entity_type": entity_type,
                        "entities_returned": entities_found,
                        "total_count": total_count,
                        "filter": query_params.get('$filter', 'none'),
                        "endpoint": endpoint_url,
                        "data": data
                    }
                    
                    # Add entity-specific metadata
                    if entity_type == "Resource" and resource_type_id:
                        result["resource_type_id"] = resource_type_id
                
                return json.dumps(result, indent=2)
            elif response.status_code == 400:
                raise ODataQueryError(f"Bad request - invalid OData query: {response.text[:200]}", response.status_code)
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed - token may be expired", response.status_code)
            elif response.status_code == 403:
                raise AuthenticationError("Access forbidden - insufficient permissions", response.status_code)
            elif response.status_code == 404:
                raise OmadaServerError("Omada endpoint not found - check base URL", response.status_code)
            elif response.status_code >= 500:
                raise OmadaServerError(f"Omada server error: {response.status_code}", response.status_code, response.text)
            else:
                raise OmadaServerError(f"Unexpected response: {response.status_code}", response.status_code, response.text)
                
    except AuthenticationError as e:
        return f"🔐 Authentication Error: {str(e)}"
    except ODataQueryError as e:
        return f"🔍 Query Error: {str(e)}"
    except OmadaServerError as e:
        return f"🚨 Server Error: {str(e)}"
    except httpx.RequestError as e:
        return f"🌐 Network Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool()
async def query_omada_identity(firstname: str = None, lastname: str = None,
                              firstname_operator: str = "eq",
                              lastname_operator: str = "eq", 
                              omada_base_url: str = None,
                              scope: str = None,
                              filter_condition: str = None,
                              count_only: bool = False,
                              top: int = None,
                              skip: int = None,
                              select_fields: str = None,
                              order_by: str = None,
                              include_count: bool = False) -> str:
    """
    Query Omada Identity entities (wrapper for query_omada_entity).
    
    Args:
        firstname: First name to search for
        lastname: Last name to search for
        firstname_operator: OData operator for firstname (eq, ne, contains, startswith, endswith, etc)
        lastname_operator: OData operator for lastname (eq, ne, contains, startswith, endswith, etc)
        omada_base_url: Omada instance URL
        scope: OAuth2 scope for the token
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select
        order_by: Field(s) to order by
        include_count: Include total count in response
        
    Returns:
        JSON response with identity data or error message
    """
    return await query_omada_entity(
        entity_type="Identity",
        firstname=firstname,
        lastname=lastname,
        firstname_operator=firstname_operator,
        lastname_operator=lastname_operator,
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count
    )

@mcp.tool()
async def query_omada_resources(resource_type_id: int = None,
                               resource_type_name: str = None,
                               system_id: int = None,
                               omada_base_url: str = None,
                               scope: str = None,
                               filter_condition: str = None,
                               count_only: bool = False,
                               top: int = None,
                               skip: int = None,
                               select_fields: str = None,
                               order_by: str = None,
                               include_count: bool = False) -> str:
    """
    Query Omada Resource entities (wrapper for query_omada_entity).
    
    Args:
        resource_type_id: Numeric ID for resource type (e.g., 1011066 for Application Roles)
        resource_type_name: Name-based lookup for resource type (e.g., "APPLICATION_ROLES")
        system_id: Numeric ID for system reference to filter resources by system (e.g., 1011066)
        omada_base_url: Omada instance URL
        scope: OAuth2 scope for the token
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select
        order_by: Field(s) to order by
        include_count: Include total count in response
        
    Returns:
        JSON response with resource data or error message
    """
    return await query_omada_entity(
        entity_type="Resource",
        resource_type_id=resource_type_id,
        resource_type_name=resource_type_name,
        system_id=system_id,
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count
    )

@mcp.tool()
async def query_omada_entities(entity_type: str = "Identity",
                              field_filters: list = None,
                              omada_base_url: str = None,
                              scope: str = None,
                              filter_condition: str = None,
                              count_only: bool = False,
                              top: int = None,
                              skip: int = None,
                              select_fields: str = None,
                              order_by: str = None,
                              expand: str = None,
                              include_count: bool = False) -> str:
    """
    Modern generic query function for Omada entities using field filters.
    
    Args:
        entity_type: Type of entity to query (Identity, Resource, System, etc)
        field_filters: List of field filters:
                      [{"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
                       {"field": "LASTNAME", "value": "Taylor", "operator": "startswith"}]
        omada_base_url: Omada instance URL
        scope: OAuth2 scope for the token
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select
        order_by: Field(s) to order by
        expand: Comma-separated list of related entities to expand
        include_count: Include total count in response
        
    Returns:
        JSON response with entity data or error message
    """
    return await query_omada_entity(
        entity_type=entity_type,
        field_filters=field_filters,
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        expand=expand,
        include_count=include_count
    )

@mcp.tool()
async def query_calculated_assignments(identity_id: int = None,
                                      select_fields: str = "AssignmentKey,AccountName",
                                      expand: str = "Identity,Resource,ResourceType",
                                      omada_base_url: str = None,
                                      scope: str = None,
                                      filter_condition: str = None,
                                      top: int = None,
                                      skip: int = None,
                                      order_by: str = None,
                                      include_count: bool = False) -> str:
    """
    Query Omada CalculatedAssignments entities (wrapper for query_omada_entity).
    
    Args:
        identity_id: Numeric ID for identity to get assignments for (e.g., 1006500)
        select_fields: Fields to select (default: "AssignmentKey,AccountName")
        expand: Related entities to expand (default: "Identity,Resource,ResourceType")
        omada_base_url: Omada instance URL
        scope: OAuth2 scope for the token
        filter_condition: Custom OData filter condition
        top: Maximum number of records to return
        skip: Number of records to skip
        order_by: Field(s) to order by
        include_count: Include total count in response
        
    Returns:
        JSON response with calculated assignments data or error message
    """
    return await query_omada_entity(
        entity_type="CalculatedAssignments",
        identity_id=identity_id,
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        expand=expand,
        include_count=include_count
    )

@mcp.tool()
async def get_all_omada_identities(omada_base_url: str = None,
                                  scope: str = None,
                                  top: int = 100,
                                  skip: int = None,
                                  select_fields: str = None,
                                  order_by: str = None,
                                  include_count: bool = True) -> str:
    """
    Retrieve all identities from Omada Identity system with pagination support.
    
    Args:
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        top: Maximum number of records to return (default: 100)
        skip: Number of records to skip for pagination
        select_fields: Comma-separated list of fields to select
        order_by: Field(s) to order by
        include_count: Include total count in response
        
    Returns:
        JSON response with all identity data or error message
    """
    return await query_omada_identity(
        omada_base_url=omada_base_url,
        scope=scope,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        filter_condition=None,  # No filter to get all
        include_count=include_count
    )

@mcp.tool()
async def count_omada_identities(filter_condition: str = None,
                                omada_base_url: str = None,
                                scope: str = None) -> str:
    """
    Count identities in Omada Identity system with optional filtering.
    
    Args:
        filter_condition: OData filter condition (optional)
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        
    Returns:
        JSON response with count or error message
    """
    return await query_omada_identity(
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        count_only=True
    )

@mcp.tool()
def ping() -> str:
    return "pong"

@mcp.tool()
async def get_azure_token(scope: str = None) -> str:
    """
    Get an Azure OAuth2 Bearer token for the specified scope.
    
    Args:
        scope: OAuth2 scope (default: Microsoft Graph API)
        
    Returns:
        Bearer token string
    """
    try:
        token_data = await get_cached_token(scope)
        bearer_token = f"Bearer {token_data['access_token']}"
        return bearer_token
    except Exception as e:
        return f"Error getting token: {str(e)}"

@mcp.tool()
async def get_azure_token_info(scope: str = None) -> str:
    """
    Get detailed Azure OAuth2 token information including expiry.
    
    Args:
        scope: OAuth2 scope (default: Microsoft Graph API)
        
    Returns:
        JSON string with token details
    """
    try:
        token_data = await get_cached_token(scope)
        
        # Prepare response data (excluding sensitive information)
        info = {
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
            "expires_at": token_data.get("expires_at").isoformat() if "expires_at" in token_data else None,
            "scope": token_data.get("scope"),
            "access_token_preview": f"{token_data['access_token'][:20]}..." if "access_token" in token_data else None,
            "cached": _cached_token is not None
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting token info: {str(e)}"

@mcp.tool()
async def test_azure_token(api_endpoint: str = "https://graph.microsoft.com/v1.0/me", 
                          scope: str = "https://graph.microsoft.com/.default") -> str:
    """
    Test the Azure token by making an authenticated API call.
    
    Args:
        api_endpoint: API endpoint to test (default: Microsoft Graph /me)
        scope: OAuth2 scope for the token
        
    Returns:
        API response or error message
    """
    try:
        # Get the token
        token_data = await get_cached_token(scope)
        bearer_token = f"Bearer {token_data['access_token']}"
        
        # Make test API call
        headers = {
            "Authorization": bearer_token,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(api_endpoint, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                return f"✅ Token test successful!\nStatus: {response.status_code}\nResponse: {response.text[:500]}..."
            else:
                return f"❌ Token test failed!\nStatus: {response.status_code}\nResponse: {response.text}"
                
    except Exception as e:
        return f"Error testing token: {str(e)}"

async def test_token_locally():
    """Test function to run locally and see token output"""
    global _cached_token
    print("Testing Azure OAuth2 token retrieval...")
    
    # Clear cached token to force fresh request
    _cached_token = None
    print("Cleared cached token")
    
    try:
        token = await get_azure_token()
        print(f"Token received: {token}")
        
        print("\nToken info:")
        token_info = await get_azure_token_info()
        print(token_info)
        
        print("\nTesting Omada API call:")
        result = await query_omada_identity("Emma", "Taylor")
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    # Check if we want to test locally
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_token_locally())
    else:
        mcp.run()
