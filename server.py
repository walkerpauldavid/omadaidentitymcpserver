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

mcp = FastMCP("OmadaIdentityMCP")

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


def _summarize_entities(data: dict, entity_type: str) -> dict:
    """
    Create a summarized version of entity data with only key fields.

    Args:
        data: The full OData response
        entity_type: Type of entity being summarized

    Returns:
        Summarized data with key fields only
    """
    if not data or "value" not in data:
        return data

    # Define key fields for each entity type
    summary_fields = {
        "Identity": ["Id", "DISPLAYNAME", "FIRSTNAME", "LASTNAME", "EMAIL", "EMPLOYEEID", "DEPARTMENT", "STATUS"],
        "Resource": ["Id", "DISPLAYNAME", "DESCRIPTION", "RESOURCEKEY", "STATUS", "Systemref"],
        "Role": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "Account": ["Id", "ACCOUNTNAME", "DISPLAYNAME", "STATUS", "SYSTEM"],
        "Application": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "System": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "CalculatedAssignments": ["Id", "AssignmentKey", "AccountName", "Identity", "Resource"],
        "AssignmentPolicy": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"]
    }

    # Get relevant fields for this entity type
    fields_to_keep = summary_fields.get(entity_type, ["Id", "DISPLAYNAME", "DESCRIPTION"])

    summarized_entities = []
    for entity in data.get("value", []):
        summary = {}
        for field in fields_to_keep:
            if field in entity:
                value = entity[field]
                # Truncate long text fields
                if isinstance(value, str) and len(value) > 100:
                    summary[field] = value[:97] + "..."
                else:
                    summary[field] = value

        # Always include Id if available
        if "Id" in entity and "Id" not in summary:
            summary["Id"] = entity["Id"]

        summarized_entities.append(summary)

    # Return summarized data with same structure
    result = data.copy()
    result["value"] = summarized_entities
    return result


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
                            summary_mode: bool = False,
                            top: int = None,
                            skip: int = None,
                            select_fields: str = None,
                            order_by: str = None,
                            expand: str = None,
                            include_count: bool = False) -> str:
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
        summary_mode: If True, returns only key fields as a summary instead of full objects
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
        valid_entities = ["Identity", "Resource", "Role", "Account", "Application", "System", "CalculatedAssignments", "AssignmentPolicy"]
        if entity_type not in valid_entities:
            return f"❌ Invalid entity type '{entity_type}'. Valid types: {', '.join(valid_entities)}"
        
        
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
        
        # For CalculatedAssignments entities, handle identity_id filtering
        if entity_type == "CalculatedAssignments":
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

                    # Apply summarization if requested
                    response_data = data
                    if summary_mode:
                        response_data = _summarize_entities(data, entity_type)

                    result = {
                        "status": "success",
                        "entity_type": entity_type,
                        "entities_returned": entities_found,
                        "total_count": total_count,
                        "filter": query_params.get('$filter', 'none'),
                        "endpoint": endpoint_url,
                        "summary_mode": summary_mode,
                        "data": response_data
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
async def query_omada_identity(field_filters: list = None,
                              omada_base_url: str = None,
                              scope: str = None,
                              filter_condition: str = None,
                              count_only: bool = False,
                              summary_mode: bool = False,
                              top: int = None,
                              skip: int = None,
                              select_fields: str = None,
                              order_by: str = None,
                              include_count: bool = False) -> str:
    """
    Query Omada Identity entities (wrapper for query_omada_entity).
    
    Args:
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
        include_count: Include total count in response
        
    Returns:
        JSON response with identity data or error message
    """
    return await query_omada_entity(
        entity_type="Identity",
        field_filters=field_filters,
        omada_base_url=omada_base_url,
        scope=scope,
        filter_condition=filter_condition,
        count_only=count_only,
        summary_mode=summary_mode,
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

async def _prepare_graphql_request(impersonate_user: str, omada_base_url: str = None, scope: str = None):
    """
    Prepare common GraphQL request components (URL, headers, token).

    Returns:
        tuple: (graphql_url, headers, token)
    """
    # Get OAuth access token
    token_info = await get_cached_token(scope)
    token = token_info.get('access_token')
    if not token:
        raise Exception("Failed to obtain access token")

    # Get base URL from parameter or environment
    if not omada_base_url:
        omada_base_url = os.getenv("OMADA_BASE_URL")
        if not omada_base_url:
            raise Exception("OMADA_BASE_URL not found in environment variables")

    # Remove trailing slash if present
    omada_base_url = omada_base_url.rstrip('/')

    # Get GraphQL endpoint version from environment (default to 3.0)
    graphql_version = os.getenv("GRAPHQL_ENDPOINT_VERSION", "3.0")
    graphql_url = f"{omada_base_url}/api/Domain/{graphql_version}"

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "impersonate_user": impersonate_user
    }

    return graphql_url, headers, token

async def _execute_graphql_request(query: str, impersonate_user: str,
                                 omada_base_url: str = None, scope: str = None,
                                 variables: dict = None) -> dict:
    """
    Execute a GraphQL request with common setup and error handling.

    Returns:
        dict: Parsed response or error information
    """
    try:
        # Setup
        graphql_url, headers, token = await _prepare_graphql_request(
            impersonate_user, omada_base_url, scope
        )

        # Build payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        # Execute request
        async with httpx.AsyncClient() as client:
            response = await client.post(graphql_url, json=payload, headers=headers, timeout=30.0)

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code,
                    "endpoint": graphql_url
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "endpoint": graphql_url
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@mcp.tool()
async def get_access_requests(impersonate_user: str, filter_field: str = None, filter_value: str = None) -> str:
    """Get access requests from Omada GraphQL API using user impersonation.

    Args:
        impersonate_user: Email address of the user to impersonate (e.g., user@domain.com)
        filter_field: Optional filter field name (e.g., "beneficiaryId", "identityId", "status")
        filter_value: Optional filter value

    Returns:
        JSON string containing access requests data
    """
    try:
        # Build GraphQL query
        if filter_field and filter_value:
            # With filter
            query = f"""query GetAccessRequests {{
  accessRequests(filters: {{{filter_field}: {json.dumps(filter_value)}}}) {{
    total
    data {{
      id
      beneficiary {{
        id
        identityId
        displayName
        contexts {{
          id
        }}
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
        else:
            # Without filter
            query = """query GetAccessRequests {
  accessRequests {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
        contexts {
          id
        }
      }
      resource {
        name
      }
      status {
        approvalStatus
      }
    }
  }
}"""

        # Execute GraphQL request
        result = await _execute_graphql_request(query, impersonate_user)

        if result["success"]:
            data = result["data"]
            # Extract and format the response
            if 'data' in data and 'accessRequests' in data['data']:
                access_requests_obj = data['data']['accessRequests']
                total = access_requests_obj.get('total', 0)
                access_requests = access_requests_obj.get('data', [])

                formatted_result = {
                    "status": "success",
                    "impersonated_user": impersonate_user,
                    "total_requests": total,
                    "requests_returned": len(access_requests),
                    "filter_applied": f"{filter_field}={filter_value}" if filter_field else "none",
                    "endpoint": result["endpoint"],
                    "data": {
                        "access_requests": access_requests
                    }
                }

                return json.dumps(formatted_result, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "No access requests data found in response",
                    "impersonated_user": impersonate_user,
                    "raw_response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
                "message": f"GraphQL request failed with status {result.get('status_code', 'unknown')}",
                "impersonated_user": impersonate_user,
                "error_type": result.get("error_type", "GraphQLError")
            }

            if "error" in result:
                error_result["response_body"] = result["error"]
            if "endpoint" in result:
                error_result["endpoint"] = result["endpoint"]

            return json.dumps(error_result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error getting access requests: {str(e)}",
            "impersonated_user": impersonate_user,
            "error_type": type(e).__name__
        }, indent=2)

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

@mcp.tool()
async def get_identity_contexts(identity_id: str, impersonate_user: str,
                               omada_base_url: str = None, scope: str = None) -> str:
    """
    Get contexts for a specific identity using Omada GraphQL API.

    Args:
        identity_id: The identity ID to get contexts for (e.g., "e3e869c4-369a-476e-a969-d57059d0b1e4")
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token

    Returns:
        JSON response with contexts data or error message
    """
    try:
        # Build GraphQL query with the provided identity_id
        query = f'query accessRequest {{\\r\\n    accessRequest {{\\r\\n        contexts(identityIds:["{identity_id}"]) {{ \\r\\n            id\\r\\n            name\\r\\n         }}\\r\\n    }}\\r\\n}}'

        # Execute GraphQL request
        result = await _execute_graphql_request(query, impersonate_user, omada_base_url, scope)

        if result["success"]:
            data = result["data"]
            # Extract contexts from the GraphQL response
            if ('data' in data and 'accessRequest' in data['data']):
                access_request_obj = data['data']['accessRequest']
                contexts = access_request_obj.get('contexts', [])

                return json.dumps({
                    "status": "success",
                    "identity_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "contexts_count": len(contexts),
                    "contexts": contexts,
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_contexts",
                    "identity_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "message": "No contexts found in response",
                    "response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
                "identity_id": identity_id,
                "impersonated_user": impersonate_user,
                "error_type": result.get("error_type", "GraphQLError")
            }

            if "status_code" in result:
                error_result["status_code"] = result["status_code"]
            if "error" in result:
                error_result["error"] = result["error"]
            if "endpoint" in result:
                error_result["endpoint"] = result["endpoint"]

            return json.dumps(error_result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "exception",
            "identity_id": identity_id,
            "impersonated_user": impersonate_user,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)


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
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
            {"field": "LASTNAME", "value": "Taylor", "operator": "eq"}
        ])
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys

    # Check if we want to test locally
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_token_locally())
    elif len(sys.argv) > 1 and sys.argv[1] == "test-access-request":
        # Test access requests function
        async def test_access_requests():
            # Default impersonate user - you may need to change this
            impersonate_user = "test@domain.com"

            if len(sys.argv) > 2:
                impersonate_user = sys.argv[2]

            print(f"🔍 Testing get_access_requests with impersonate_user: {impersonate_user}")

            try:
                # Get OAuth access token first
                token_info = await get_cached_token()
                token = token_info.get('access_token')

                # Get Omada base URL from environment
                omada_base_url = os.getenv("OMADA_BASE_URL")
                # Get GraphQL endpoint version from environment (default to 2.6)
                graphql_version = os.getenv("GRAPHQL_ENDPOINT_VERSION", "2.6")
                graphql_url = f"{omada_base_url}/api/Domain/{graphql_version}"

                # Test 1: Without filter
                print("\n" + "="*80)
                print("🚀 TEST 1: ACCESS REQUESTS WITHOUT FILTER")
                print("="*80)

                graphql_query_no_filter = {
                    "query": """query GetAccessRequests {
  accessRequests {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
        contexts {
          id
        }
      }
      resource {
        name
      }
      status {
        approvalStatus
      }
    }
  }
}"""
                }

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "impersonate_user": impersonate_user
                }

                print(f"📡 URL: {graphql_url}")
                print(f"📋 Method: POST")

                print(f"\n📤 Request Headers:")
                for key, value in headers.items():
                    if key == "Authorization":
                        print(f"  ├── {key}: Bearer {value.split(' ')[1][:20]}...")
                    else:
                        print(f"  ├── {key}: {value}")

                print(f"\n📝 Request Body:")
                print(json.dumps(graphql_query_no_filter, indent=2))

                # Execute request
                print(f"\n⏳ Executing POST request...")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        graphql_url,
                        json=graphql_query_no_filter,
                        headers=headers,
                        timeout=30.0
                    )

                    print(f"\n📥 Response Status: {response.status_code}")
                    print(f"📥 Response Headers:")
                    for key, value in response.headers.items():
                        print(f"  ├── {key}: {value}")

                    print(f"\n📄 Response Body:")
                    if response.status_code == 200:
                        result = response.json()
                        print(json.dumps(result, indent=2))
                    else:
                        print(response.text)

                # Test 2: With filter
                print("\n" + "="*80)
                print("🚀 TEST 2: ACCESS REQUESTS WITH FILTER (status=PENDING)")
                print("="*80)

                graphql_query_filtered = {
                    "query": f"""query GetAccessRequests {{
  accessRequests(filters: {{status: {json.dumps("PENDING")}}}) {{
    total
    data {{
      id
      beneficiary {{
        id
        identityId
        displayName
        contexts {{
          id
        }}
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

                print(f"📡 URL: {graphql_url}")
                print(f"📋 Method: POST")

                print(f"\n📤 Request Headers:")
                for key, value in headers.items():
                    if key == "Authorization":
                        print(f"  ├── {key}: Bearer {value.split(' ')[1][:20]}...")
                    else:
                        print(f"  ├── {key}: {value}")

                print(f"\n📝 Request Body:")
                print(json.dumps(graphql_query_filtered, indent=2))

                # Execute filtered request
                print(f"\n⏳ Executing POST request...")
                async with httpx.AsyncClient() as client:
                    response_filtered = await client.post(
                        graphql_url,
                        json=graphql_query_filtered,
                        headers=headers,
                        timeout=30.0
                    )

                    print(f"\n📥 Response Status: {response_filtered.status_code}")
                    print(f"📥 Response Headers:")
                    for key, value in response_filtered.headers.items():
                        print(f"  ├── {key}: {value}")

                    print(f"\n📄 Response Body:")
                    if response_filtered.status_code == 200:
                        result_filtered = response_filtered.json()
                        print(json.dumps(result_filtered, indent=2))
                    else:
                        print(response_filtered.text)

                print(f"\n✅ Testing completed!")

            except Exception as e:
                print(f"❌ Error testing access requests: {e}")

        asyncio.run(test_access_requests())
    else:
        mcp.run()
