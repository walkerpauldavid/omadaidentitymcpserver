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
import logging

# Load environment variables
load_dotenv()

# Configure logging system
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "omada_mcp_server.log")

# Convert to absolute path if relative path provided
if not os.path.isabs(LOG_FILE):
    # Use the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    LOG_FILE = os.path.join(script_dir, LOG_FILE)

# Create logs directory if it doesn't exist
log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging with both file and console handlers
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Writing logs to: {os.path.abspath(LOG_FILE)}")

def get_function_log_level(function_name: str) -> int:
    """
    Get the log level for a specific function, falling back to global LOG_LEVEL.

    Args:
        function_name: Name of the function to get log level for

    Returns:
        logging level constant (e.g., logging.DEBUG, logging.INFO)
    """
    # Try function-specific log level first
    func_log_level = os.getenv(f"LOG_LEVEL_{function_name}", "").upper()

    # If not set, use global LOG_LEVEL
    if not func_log_level:
        func_log_level = LOG_LEVEL

    # Convert string to logging level, default to INFO if invalid
    return getattr(logging, func_log_level, logging.INFO)

def set_function_logger_level(function_name: str) -> tuple:
    """
    Set the logger level for a specific function and return the old levels.

    Args:
        function_name: Name of the function

    Returns:
        Tuple of (old_logger_level, old_handler_levels) for restoration
    """
    old_level = logger.level
    new_level = get_function_log_level(function_name)

    # Save old handler levels before changing them
    old_handler_levels = [(handler, handler.level) for handler in logger.handlers]

    # Set logger level
    logger.setLevel(new_level)

    # IMPORTANT: Also set handler levels so they don't filter out DEBUG messages
    # Handlers have their own level filter separate from the logger level
    for handler in logger.handlers:
        handler.setLevel(new_level)

    # Log the level change if it's different (only at DEBUG level to avoid noise)
    if old_level != new_level and new_level <= logging.DEBUG:
        logger.debug(f"Function '{function_name}' using log level: {logging.getLevelName(new_level)}")

    return (old_level, old_handler_levels)

def with_function_logging(func):
    """
    Decorator to automatically set function-specific logging level.

    Usage:
        @with_function_logging
        @mcp.tool()
        async def my_function():
            pass
    """
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            old_level, old_handler_levels = set_function_logger_level(func.__name__)
            try:
                return await func(*args, **kwargs)
            finally:
                # Restore logger level
                logger.setLevel(old_level)
                # Restore handler levels
                for handler, level in old_handler_levels:
                    handler.setLevel(level)
        # Preserve the original function name and metadata
        async_wrapper.__name__ = func.__name__
        async_wrapper.__doc__ = func.__doc__
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            old_level, old_handler_levels = set_function_logger_level(func.__name__)
            try:
                return func(*args, **kwargs)
            finally:
                # Restore logger level
                logger.setLevel(old_level)
                # Restore handler levels
                for handler, level in old_handler_levels:
                    handler.setLevel(level)
        # Preserve the original function name and metadata
        sync_wrapper.__name__ = func.__name__
        sync_wrapper.__doc__ = func.__doc__
        return sync_wrapper

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

# Register MCP Prompts for workflow guidance
from prompts import register_prompts
register_prompts(mcp)

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


def _summarize_graphql_data(data: list, data_type: str) -> list:
    """
    Create a summarized version of GraphQL response data with only key fields.

    Args:
        data: List of GraphQL response objects
        data_type: Type of data being summarized (e.g., "PendingApproval", "AccessRequest")

    Returns:
        Summarized data with key fields only
    """
    if not data or not isinstance(data, list):
        return data

    # Define key fields for each GraphQL data type
    # Fields listed here are ONLY fields that will be returned
    summary_fields = {
        "PendingApproval": ["workflowStep", "workflowStepTitle", "reason"],
        "AccessRequest": ["id", "beneficiary", "resource", "status"],
        "CalculatedAssignment": ["complianceStatus", "account", "resource", "identity"],
        "Context": ["id", "displayName", "type"],
        "Resource": ["id", "name", "description", "system"]
    }

    # Define fields to explicitly exclude (technical fields users shouldn't see)
    exclude_fields = {
        "PendingApproval": ["surveyId", "surveyObjectKey", "history"],
        "AccessRequest": [],
        "CalculatedAssignment": [],
        "Context": [],
        "Resource": []
    }

    # Get relevant fields for this data type
    fields_to_keep = summary_fields.get(data_type, ["id", "name"])
    fields_to_exclude = exclude_fields.get(data_type, [])

    summarized = []
    for item in data:
        summary = {}

        # Only include explicitly allowed fields
        for field in fields_to_keep:
            if field in item:
                value = item[field]
                # Truncate long text fields
                if isinstance(value, str) and len(value) > 100:
                    summary[field] = value[:97] + "..."
                else:
                    summary[field] = value

        # Don't auto-add id field for PendingApproval type
        # For other types, include id if available and not already in summary
        if data_type != "PendingApproval":
            if "id" in item and "id" not in summary and "id" not in fields_to_exclude:
                summary["id"] = item["id"]

        summarized.append(summary)

    return summarized


# =============================================================================
# OAuth Token Functions
# =============================================================================
# NOTE: OAuth token acquisition functions have been migrated to oauth_mcp_server
# This server now focuses on Omada-specific operations.
# For token operations, use the oauth_mcp_server which provides:
#   - OAuth 2.0 Client Credentials Flow
#   - OAuth 2.0 Device Authorization Grant Flow
#   - Token caching and management
# =============================================================================

@with_function_logging
@mcp.tool()
async def query_omada_entity(entity_type: str = "Identity",
                            filters: dict = None,
                            omada_base_url: str = None,
                            scope: str = None,
                            count_only: bool = False,
                            summary_mode: bool = True,
                            top: int = None,
                            skip: int = None,
                            select_fields: str = None,
                            order_by: str = None,
                            expand: str = None,
                            include_count: bool = False,
                            bearer_token: str = None,
                            impersonate_user: str = None) -> str:
    """
    Generic query function for any Omada entity type (Identity, Resource, Role, etc).

    IMPORTANT - Identity Field Names (use EXACTLY as shown):
        - EMAIL (not "email", "MAIL", or "EMAILADDRESS")
        - FIRSTNAME (not "firstname" or "first_name")
        - LASTNAME (not "lastname" or "last_name")
        - DISPLAYNAME (not "displayname" or "display_name")
        - EMPLOYEEID (not "employee_id")
        - DEPARTMENT (not "department")
        - STATUS (not "status")

    Args:
        entity_type: Type of entity to query (Identity, Resource, Role, Account, etc)
        filters: Dictionary containing filter criteria:
                {
                    "field_filters": [{"field": "EMAIL", "value": "user@domain.com", "operator": "eq"}],
                    "resource_type_id": 1011066,  # For Resource entities
                    "resource_type_name": "APPLICATION_ROLES",  # Alternative to resource_type_id
                    "system_id": 1011066,  # For Resource entities
                    "identity_id": 1006500,  # For CalculatedAssignments entities
                    "custom_filter": "FIRSTNAME eq 'John' and LASTNAME eq 'Doe'"  # Custom OData filter
                }
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        count_only: If True, returns only the count of matching records
        summary_mode: If True, returns only key fields as a summary instead of full objects
        top: Maximum number of records to return (OData $top)
        skip: Number of records to skip (OData $skip)
        select_fields: Comma-separated list of fields to select (OData $select)
        order_by: Field(s) to order by (OData $orderby)
        expand: Comma-separated list of related entities to expand (OData $expand)
        include_count: Include total count in response (adds $count=true)
        bearer_token: Optional bearer token to use instead of acquiring a new one
        impersonate_user: Optional email address for user impersonation (required for user-delegated tokens)

    Examples:
        # Query by email (IMPORTANT: field name is "EMAIL" not "email" or "MAIL")
        await query_omada_entity("Identity", filters={
            "field_filters": [{"field": "EMAIL", "value": "user@domain.com", "operator": "eq"}]
        })

        # Query by first name
        await query_omada_entity("Identity", filters={
            "field_filters": [{"field": "FIRSTNAME", "value": "John", "operator": "eq"}]
        })

        # Resource filtering
        await query_omada_entity("Resource", filters={
            "resource_type_id": 123,
            "system_id": 456
        })

        # Multiple filters combined
        await query_omada_entity("Identity", filters={
            "field_filters": [{"field": "DEPARTMENT", "value": "IT", "operator": "eq"}],
            "custom_filter": "STATUS eq 'ACTIVE'"
        })

        # CalculatedAssignments for specific identity
        await query_omada_entity("CalculatedAssignments", filters={
            "identity_id": 1006500
        })

        # Count only with custom filter
        await query_omada_entity("Identity",
            filters={"custom_filter": "DEPARTMENT eq 'Engineering'"},
            count_only=True
        )

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
        
        # Initialize filters dictionary if not provided
        if filters is None:
            filters = {}

        # Extract filter components from the filters dictionary
        field_filters = filters.get("field_filters", [])
        resource_type_id = filters.get("resource_type_id")
        resource_type_name = filters.get("resource_type_name")
        system_id = filters.get("system_id")
        identity_id = filters.get("identity_id")
        custom_filter = filters.get("custom_filter")

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
        if custom_filter:
            all_filters.append(f"({custom_filter})")
        
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

        # Bearer token is always required (OAuth functions migrated to oauth_mcp_server)
        if bearer_token:
            logger.debug("Using provided bearer token for OData request")
            # Strip "Bearer " prefix if already present to avoid double-prefix
            clean_token = bearer_token.replace("Bearer ", "").replace("bearer ", "").strip()
            auth_header = f"Bearer {clean_token}"
        else:
            # OAuth token functions have been migrated to oauth_mcp_server
            # bearer_token is now mandatory for all authentication methods
            raise Exception(
                "bearer_token parameter is required.\n"
                "OAuth token functions have been migrated to oauth_mcp_server.\n\n"
                "Workflow:\n"
                "1. Use oauth_mcp_server to obtain a bearer token:\n"
                "   - For Device Code flow: 'start device authentication' then 'complete device authentication'\n"
                "   - For Client Credentials: use oauth_mcp_server's token acquisition functions\n"
                "2. Pass the token to this function using bearer_token parameter\n\n"
                "Example: bearer_token='eyJ0eXAiOiJKV1QiLCJhbGc...'"
            )

        # Make API call to Omada
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Add impersonate_user header if provided (required for user-delegated tokens like device code)
        if impersonate_user:
            headers["impersonate_user"] = impersonate_user
            logger.debug(f"Using impersonate_user: {impersonate_user}")
        
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

@with_function_logging
@mcp.tool()
async def query_omada_identity(field_filters: list = None,
                              omada_base_url: str = None,
                              scope: str = None,
                              filter_condition: str = None,
                              count_only: bool = False,
                              summary_mode: bool = True,
                              top: int = None,
                              skip: int = None,
                              select_fields: str = None,
                              order_by: str = None,
                              include_count: bool = False,
                              bearer_token: str = None) -> str:
    """
    Query Omada Identity entities (wrapper for query_omada_entity).

    IMPORTANT - Identity Field Names (use EXACTLY as shown):
        - EMAIL (not "email", "MAIL", or "EMAILADDRESS")
        - FIRSTNAME (not "firstname" or "first_name")
        - LASTNAME (not "lastname" or "last_name")
        - DISPLAYNAME, EMPLOYEEID, DEPARTMENT, STATUS

    Args:
        field_filters: List of field filters:
                      [{"field": "EMAIL", "value": "user@domain.com", "operator": "eq"},
                       {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
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
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with identity data or error message
    """
    # Build filters dictionary for clean API
    filters = {}
    if field_filters:
        filters["field_filters"] = field_filters
    if filter_condition:
        filters["custom_filter"] = filter_condition

    return await query_omada_entity(
        entity_type="Identity",
        filters=filters if filters else None,
        omada_base_url=omada_base_url,
        scope=scope,
        count_only=count_only,
        summary_mode=summary_mode,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token
    )

@with_function_logging
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
                               include_count: bool = False,
                               bearer_token: str = None) -> str:
    """
    Query Omada Resource entities using OData API (for ADMINISTRATIVE queries only).

    WARNING: DO NOT USE THIS for access request workflows!
    - This function does NOT scope resources to user permissions
    - This does NOT show what a user can request
    - For access requests, use get_requestable_resources or get_resources_for_beneficiary instead

    USE THIS FUNCTION for:
    - Administrative resource queries
    - Bulk resource reports
    - System-level resource inventory
    - Resource type analysis

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
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with resource data or error message
    """
    # Build filters dictionary for clean API
    filters = {}
    if resource_type_id:
        filters["resource_type_id"] = resource_type_id
    if resource_type_name:
        filters["resource_type_name"] = resource_type_name
    if system_id:
        filters["system_id"] = system_id
    if filter_condition:
        filters["custom_filter"] = filter_condition

    return await query_omada_entity(
        entity_type="Resource",
        filters=filters if filters else None,
        omada_base_url=omada_base_url,
        scope=scope,
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token
    )

@with_function_logging
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
                              include_count: bool = False,
                              bearer_token: str = None) -> str:
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
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with entity data or error message
    """
    # Build filters dictionary for clean API
    filters = {}
    if field_filters:
        filters["field_filters"] = field_filters
    if filter_condition:
        filters["custom_filter"] = filter_condition

    return await query_omada_entity(
        entity_type=entity_type,
        filters=filters if filters else None,
        omada_base_url=omada_base_url,
        scope=scope,
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        expand=expand,
        include_count=include_count,
        bearer_token=bearer_token
    )

@with_function_logging
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
                                      include_count: bool = False,
                                      bearer_token: str = None) -> str:
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
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with calculated assignments data or error message
    """
    # Build filters dictionary for clean API
    filters = {}
    if identity_id:
        filters["identity_id"] = identity_id
    if filter_condition:
        filters["custom_filter"] = filter_condition

    return await query_omada_entity(
        entity_type="CalculatedAssignments",
        filters=filters if filters else None,
        omada_base_url=omada_base_url,
        scope=scope,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        expand=expand,
        include_count=include_count,
        bearer_token=bearer_token
    )

@with_function_logging
@mcp.tool()
async def get_all_omada_identities(omada_base_url: str = None,
                                  scope: str = None,
                                  top: int = 1000,
                                  skip: int = None,
                                  select_fields: str = None,
                                  order_by: str = None,
                                  include_count: bool = True,
                                  bearer_token: str = None) -> str:
    """
    Retrieve all identities from Omada Identity system with pagination support.

    Args:
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        top: Maximum number of records to return (default: 1000)
        skip: Number of records to skip for pagination
        select_fields: Comma-separated list of fields to select
        order_by: Field(s) to order by
        include_count: Include total count in response
        bearer_token: Optional bearer token to use instead of acquiring a new one

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
        include_count=include_count,
        bearer_token=bearer_token
    )


@with_function_logging
@mcp.tool()
def ping() -> str:
    logger.info("Ping function called - responding with pong")
    return "pong"

@with_function_logging
@mcp.tool()
async def check_omada_config() -> str:
    """
    Check and display current Omada server configuration.

    Returns:
        JSON string with Omada configuration details
    """
    try:
        config = {
            "name": "Omada MCP Server",
            "version": "1.0.0",
            "omada_base_url": os.getenv("OMADA_BASE_URL", "NOT_SET"),
            "graphql_endpoint_version": os.getenv("GRAPHQL_ENDPOINT_VERSION", "3.0"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_file": os.getenv("LOG_FILE", "omada_mcp_server.log"),
        }

        # Validate required settings
        missing = []
        if config["omada_base_url"] == "NOT_SET":
            missing.append("OMADA_BASE_URL")

        if missing:
            config["status"] = "INVALID"
            config["error"] = f"Missing required environment variables: {', '.join(missing)}"
        else:
            config["status"] = "VALID"

        # Add note about OAuth migration
        config["note"] = "OAuth token functions have been migrated to oauth_mcp_server. All Omada functions require bearer_token parameter."
        config["usage_example"] = "get_pending_approvals(impersonate_user='user@domain.com', bearer_token='eyJ0...')"

        return json.dumps(config, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def _prepare_graphql_request(impersonate_user: str, omada_base_url: str = None, scope: str = None, graphql_version: str = None, bearer_token: str = None):
    """
    Prepare common GraphQL request components (URL, headers, token).

    NOTE: OAuth token acquisition has been migrated to oauth_mcp_server.
    This function now requires bearer_token to be passed as a parameter.

    Args:
        impersonate_user: User to impersonate in the request
        omada_base_url: Base URL for Omada instance
        scope: OAuth2 scope (deprecated - kept for backward compatibility)
        graphql_version: GraphQL API version to use
        bearer_token: Bearer token (REQUIRED) - obtain from oauth_mcp_server

    Returns:
        tuple: (graphql_url, headers, token)

    Raises:
        Exception if bearer_token is not provided
    """
    # Bearer token is now mandatory
    if not bearer_token:
        raise Exception(
            "bearer_token parameter is REQUIRED.\n"
            "OAuth token functions have been migrated to oauth_mcp_server.\n\n"
            "To obtain a token:\n"
            "1. Use oauth_mcp_server's get_azure_token() for Client Credentials flow\n"
            "2. OR use start_device_auth() + complete_device_auth() for Device Code flow\n"
            "3. Pass the token to this function using bearer_token parameter\n\n"
            "Example: bearer_token='eyJ0eXAiOiJKV1QiLCJhbGc...'"
        )

    logger.debug("Using provided bearer token")
    # Strip "Bearer " prefix if already present to avoid double-prefix
    token = bearer_token.replace("Bearer ", "").replace("bearer ", "").strip()

    # Get base URL from parameter or environment
    if not omada_base_url:
        omada_base_url = os.getenv("OMADA_BASE_URL")
        if not omada_base_url:
            raise Exception("OMADA_BASE_URL not found in environment variables")

    # Remove trailing slash if present
    omada_base_url = omada_base_url.rstrip('/')

    # Get GraphQL endpoint version from parameter, environment, or default to 3.0
    if not graphql_version:
        graphql_version = os.getenv("GRAPHQL_ENDPOINT_VERSION", "3.0")
    graphql_url = f"{omada_base_url}/api/Domain/{graphql_version}"

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "impersonate_user": impersonate_user,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    return graphql_url, headers, token

async def _execute_graphql_request(query: str, impersonate_user: str,
                                 omada_base_url: str = None, scope: str = None,
                                 variables: dict = None, graphql_version: str = None,
                                 bearer_token: str = None) -> dict:
    """
    Execute a GraphQL request with common setup and error handling.

    Args:
        query: GraphQL query string
        impersonate_user: User to impersonate in the request
        omada_base_url: Base URL for Omada instance
        scope: OAuth2 scope for token acquisition
        variables: Optional GraphQL variables
        graphql_version: GraphQL API version to use
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        dict: Parsed response or error information
    """
    try:
        # Setup
        graphql_url, headers, token = await _prepare_graphql_request(
            impersonate_user, omada_base_url, scope, graphql_version, bearer_token
        )

        # Build payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(f"GraphQL Request to {graphql_url} with impersonation of {impersonate_user}")
        # Execute request
        async with httpx.AsyncClient() as client:
            response = await client.post(graphql_url, json=payload, headers=headers, timeout=30.0)

            # Capture raw HTTP details for debugging
            raw_request_body = json.dumps(payload, indent=2)
            raw_response_body = response.text

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code,
                    "endpoint": graphql_url,
                    "raw_request_body": raw_request_body,
                    "raw_response_body": raw_response_body,
                    "request_headers": dict(headers)
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                    "endpoint": graphql_url,
                    "raw_request_body": raw_request_body,
                    "raw_response_body": raw_response_body,
                    "request_headers": dict(headers)
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

@with_function_logging
@mcp.tool()
async def get_access_requests(impersonate_user: str, filter_field: str = None, filter_value: str = None,
                              summary_mode: bool = True, bearer_token: str = None) -> str:
    """Get access requests from Omada GraphQL API using user impersonation.

    Args:
        impersonate_user: Email address of the user to impersonate (e.g., user@domain.com)
        filter_field: Optional filter field name (e.g., "beneficiaryId", "identityId", "status")
        filter_value: Optional filter value
        summary_mode: If True (default), returns only key fields (id, beneficiary, resource, status)
                     If False, returns all fields
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON string containing access requests data
    """
    try:
        logger.debug(f"Getting access requests for user: {impersonate_user}, filter: {filter_field}={filter_value if filter_field else 'none'}")

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
        result = await _execute_graphql_request(query, impersonate_user, bearer_token=bearer_token)

        if result["success"]:
            data = result["data"]
            # Extract and format the response
            if 'data' in data and 'accessRequests' in data['data']:
                access_requests_obj = data['data']['accessRequests']
                total = access_requests_obj.get('total', 0)
                access_requests = access_requests_obj.get('data', [])

                # Apply summarization if requested
                response_data = access_requests
                if summary_mode:
                    response_data = _summarize_graphql_data(access_requests, "AccessRequest")

                formatted_result = {
                    "status": "success",
                    "impersonated_user": impersonate_user,
                    "total_requests": total,
                    "requests_returned": len(response_data),
                    "filter_applied": f"{filter_field}={filter_value}" if filter_field else "none",
                    "summary_mode": summary_mode,
                    "endpoint": result["endpoint"],
                    "data": {
                        "access_requests": response_data
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

@with_function_logging
@mcp.tool()
async def create_access_request(impersonate_user: str, reason: str, context: str,
                              resources: str, valid_from: str = None, valid_to: str = None,
                              omada_base_url: str = None, scope: str = None,
                              bearer_token: str = None) -> str:
    """Create an access request using GraphQL mutation.

    IMPORTANT: This function requires 4 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.
    The identity ID is automatically fetched using the impersonate_user email.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., user@domain.com)
                         PROMPT: "Please provide the email address to impersonate"
                         NOTE: This email will be used to automatically lookup the identity ID
        reason: Reason for the access request (cannot be empty)
                PROMPT: "Please provide a reason for this access request"
        context: Business context for the access request (cannot be empty)
                PROMPT: "Please provide the business context for this access request"
        resources: Resources to request access for (JSON array format, cannot be empty)
                  PROMPT: "Please provide the resources in JSON array format"

    Optional parameters:
        valid_from: Optional valid from date/time
        valid_to: Optional valid to date/time
        omada_base_url: Optional Omada base URL (uses env var if not provided)
        scope: Optional OAuth scope (uses default if not provided)
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Logging:
        Log level controlled by LOG_LEVEL_create_access_request in .env file
        Falls back to global LOG_LEVEL if not set

    Returns:
        JSON string containing the created access request ID or error information
    """
    try:
        # Validate mandatory fields
        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        if not reason or not reason.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: reason",
                "error_type": "ValidationError"
            }, indent=2)


        if not context or not context.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: context",
                "error_type": "ValidationError"
            }, indent=2)

        if not resources or not resources.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: resources",
                "error_type": "ValidationError"
            }, indent=2)

        # Get identity ID from the impersonate_user email
        logger.debug(f"Looking up identity ID for email: {impersonate_user}")
        identity_result = await query_omada_identity(
            field_filters=[{"field": "EMAIL", "value": impersonate_user, "operator": "eq"}],
            omada_base_url=omada_base_url,
            scope=scope,
            select_fields="UId",
            top=1,
            bearer_token=bearer_token
        )

        # Parse the identity lookup result
        try:
            identity_data = json.loads(identity_result)
            if identity_data.get("status") != "success" or not identity_data.get("data", {}).get("value"):
                return json.dumps({
                    "status": "error",
                    "message": f"Could not find identity for email: {impersonate_user}",
                    "error_type": "IdentityLookupError",
                    "lookup_result": identity_data
                }, indent=2)

            identity_entity = identity_data["data"]["value"][0]
            identity_id = str(identity_entity.get("UId"))

            if not identity_id:
                return json.dumps({
                    "status": "error",
                    "message": f"Identity found but no ID available for email: {impersonate_user}",
                    "error_type": "IdentityLookupError",
                    "identity_data": identity_entity
                }, indent=2)

            logger.debug(f"Found identity ID: {identity_id} for {impersonate_user}")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to parse identity lookup result: {str(e)}",
                "error_type": "IdentityLookupParseError",
                "raw_result": identity_result
            }, indent=2)

        # Build the GraphQL mutation with template variables filled in
        valid_from_clause = f'validFrom: "{valid_from}",' if valid_from else ''
        valid_to_clause = f'validTo: "{valid_to}",' if valid_to else ''
        context_clause = f'context: "{context}",'

        mutation = f"""mutation CreateAccessRequest {{
    createAccessRequest(accessRequest: {{
        reason: "{reason}",
        {valid_from_clause}
        {valid_to_clause}
        {context_clause}
        identities: {{id: "{identity_id}"}},
        resources: {resources}
        }})
    {{
        id
        status {{
            approvalStatus
            requestAssignmentState
        }}
        resource {{
            name
            id
            system {{
                name
                id
            }}
        }}
        validFrom
        validTo
    }}
}}"""
        
        logger.debug(f"Prepared GraphQL mutation:\n{mutation}")

        # Execute the GraphQL mutation (use version 1.1 for access request creation)
        result = await _execute_graphql_request(
            query=mutation,
            impersonate_user=impersonate_user,
            omada_base_url=omada_base_url,
            scope=scope,
            graphql_version="1.1",
            bearer_token=bearer_token
        )

        if result["success"]:
            data = result["data"]

            # Debug: Print the actual response structure
            logger.debug(f"GraphQL Response Data Structure: {json.dumps(data, indent=2)}")

            # Check if mutation was successful and extract the created access request ID
            if "data" in data and "createAccessRequest" in data["data"]:
                create_request_response = data["data"]["createAccessRequest"]
                logger.debug(f"CreateAccessRequest Response: {json.dumps(create_request_response, indent=2)}")

                # Handle both single object and array responses
                if isinstance(create_request_response, list):
                    if len(create_request_response) > 0:
                        access_request_data = create_request_response[0]
                    else:
                        return json.dumps({
                            "status": "error",
                            "message": "Empty response from createAccessRequest",
                            "impersonated_user": impersonate_user,
                            "raw_response": data,
                            "http_debug": {
                                "raw_request_body": result.get("raw_request_body"),
                                "raw_response_body": result.get("raw_response_body"),
                                "request_headers": result.get("request_headers")
                            }
                        }, indent=2)
                else:
                    access_request_data = create_request_response

                access_request_id = access_request_data.get("id")

                formatted_result = {
                    "status": "success",
                    "message": "Access request created successfully",
                    "impersonated_user": impersonate_user,
                    "access_request_id": access_request_id,
                    "endpoint": result["endpoint"],
                    "access_request_details": {
                        "id": access_request_id,
                        "status": access_request_data.get("status"),
                        "resource": access_request_data.get("resource"),
                        "validFrom": access_request_data.get("validFrom"),
                        "validTo": access_request_data.get("validTo")
                    },
                    "request_details": {
                        "reason": reason,
                        "identity_id": identity_id,
                        "identity_email": impersonate_user,
                        "resources": resources,
                        "valid_from": valid_from,
                        "valid_to": valid_to,
                        "context": context
                    },
                    "http_debug": {
                        "raw_request_body": result.get("raw_request_body"),
                        "raw_response_body": result.get("raw_response_body"),
                        "request_headers": result.get("request_headers")
                    }
                }

                return json.dumps(formatted_result, indent=2)
            elif "errors" in data:
                # Handle GraphQL errors
                return json.dumps({
                    "status": "error",
                    "message": "GraphQL mutation failed",
                    "impersonated_user": impersonate_user,
                    "errors": data["errors"],
                    "endpoint": result["endpoint"],
                    "http_debug": {
                        "raw_request_body": result.get("raw_request_body"),
                        "raw_response_body": result.get("raw_response_body"),
                        "request_headers": result.get("request_headers")
                    }
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Unexpected response format",
                    "impersonated_user": impersonate_user,
                    "raw_response": data,
                    "http_debug": {
                        "raw_request_body": result.get("raw_request_body"),
                        "raw_response_body": result.get("raw_response_body"),
                        "request_headers": result.get("request_headers")
                    }
                }, indent=2)
        else:
            # Handle HTTP request failure
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

            # Add HTTP debug information
            error_result["http_debug"] = {
                "raw_request_body": result.get("raw_request_body"),
                "raw_response_body": result.get("raw_response_body"),
                "request_headers": result.get("request_headers")
            }

            return json.dumps(error_result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error creating access request: {str(e)}",
            "impersonated_user": impersonate_user,
            "error_type": type(e).__name__
        }, indent=2)

@with_function_logging
@mcp.tool()
async def get_resources_for_beneficiary(identity_id: str, impersonate_user: str,
                                       system_id: str = None, context_id: str = None,
                                       resource_name: str = None,
                                       omada_base_url: str = None, scope: str = None,
                                       bearer_token: str = None) -> str:
    """
    Get resources available for an ACCESS REQUEST for a specific user/identity using Omada GraphQL API.

    USE THIS FUNCTION when user asks to:
    - "list resources for access request"
    - "what resources can I request"
    - "show requestable resources"
    - "resources I can request access to"
    - "resources available for access request"

    This is the CORRECT function for access request workflows.
    DO NOT use query_omada_resources for access requests - it does not scope to user permissions.

    CRITICAL - Identity ID Field Name:
        WRONG: Do NOT use the "Id" field (e.g., 1006715) - this is the integer database ID
        CORRECT: Use the "UId" field (e.g., "e3e869c4-369a-476e-a969-d57059d0b1e4") - this is the 32-character UUID

        When querying for identity data, you MUST:
        1. Query the Identity entity to get the user record
        2. Extract the "UId" field (NOT "Id") from the result
        3. Use that UId value as the identity_id parameter

        Example workflow:
        - Query: query_omada_identity with EMAIL filter returns {"UId": "e3e869c4-...", "Id": 1006715}
        - Use UId: "e3e869c4-..." as identity_id parameter (32 character UUID)
        - DO NOT use Id: 1006715 (this will fail!)

    IMPORTANT: This function requires 2 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        identity_id: The identity UId (32-character UUID, NOT the integer Id field!)
                    Example: "e3e869c4-369a-476e-a969-d57059d0b1e4" (CORRECT)
                    NOT: 1006715 (WRONG - this is the Id field, not UId)
                    PROMPT: "Please provide the identity UId (32-character UUID from the UId field, not the Id field)"
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"

    Optional parameters:
        system_id: System ID to filter resources by (e.g., "1c2768e9-86fd-43fd-9e0d-5c8fee21b59b")
        context_id: Context ID to filter resources by (e.g., "6dd03400-ddb5-4cc4-bfff-490d94b195a9")
        resource_name: Resource name to filter by (string, partial match supported)
                      Example: "Sales" will match "Sales Team Access", "Sales Reports", etc.
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with resources data or error message
    """
    try:
        # Validate mandatory fields
        if not identity_id or not identity_id.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: identity_id",
                "error_type": "ValidationError"
            }, indent=2)

        # Validate that identity_id is a UUID (32 characters), not an integer Id
        if identity_id.strip().isdigit():
            return json.dumps({
                "status": "error",
                "message": f"Invalid identity_id: '{identity_id}' appears to be an integer Id field, but this function requires the UId field (32-character UUID). "
                           f"When you query an Identity, you get both 'Id' (integer like 1006715) and 'UId' (UUID like 'e3e869c4-369a-476e-a969-d57059d0b1e4'). "
                           f"You MUST use the UId field, not the Id field.",
                "error_type": "ValidationError",
                "hint": "Query the identity first, then extract the 'UId' field (not 'Id') from the response"
            }, indent=2)

        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        # Build the filters object dynamically based on provided parameters
        filters = f'beneficiaryIds: "{identity_id}"'

        if system_id and system_id.strip():
            filters += f', systemId: "{system_id}"'

        if context_id and context_id.strip():
            filters += f', contextId: "{context_id}"'

        # Add resource_name filter if provided (validates and adds to GraphQL filter)
        if resource_name and resource_name.strip():
            # Escape any quotes in the resource name to prevent GraphQL injection
            escaped_resource_name = resource_name.strip().replace('"', '\\"')
            filters += f', name: "{escaped_resource_name}"'
            logger.debug(f"Added resource_name filter: {escaped_resource_name}")

        # Build GraphQL query with the filters
        query = f"""query GetResourcesForBeneficiary {{
  accessRequestComponents {{
    resources(
      filters: {{{filters}}}
    ) {{
      data {{
        name
        id
        description
        system {{
          name
          id
        }}
        resourceType {{
          name
          id
        }}
      }}
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request
        result = await _execute_graphql_request(query, impersonate_user, omada_base_url, scope, bearer_token=bearer_token)

        if result["success"]:
            data = result["data"]
            # Extract resources from the GraphQL response
            if ('data' in data and 'accessRequestComponents' in data['data']):
                access_request_components = data['data']['accessRequestComponents']
                resources = access_request_components.get('resources', {}).get('data', [])

                return json.dumps({
                    "status": "success",
                    "beneficiary_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "system_id": system_id,
                    "context_id": context_id,
                    "resources_count": len(resources),
                    "resources": resources,
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_resources",
                    "beneficiary_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "message": "No resources found in response",
                    "response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
                "beneficiary_id": identity_id,
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
            "beneficiary_id": identity_id,
            "impersonated_user": impersonate_user,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)


@with_function_logging
@mcp.tool()
async def get_requestable_resources(identity_id: str, impersonate_user: str,
                                   system_id: str = None, context_id: str = None,
                                   resource_name: str = None,
                                   omada_base_url: str = None, scope: str = None,
                                   bearer_token: str = None) -> str:
    """
    Get resources that a user can request access to (alias for get_resources_for_beneficiary).

    EASY-TO-USE function for ACCESS REQUEST workflows - no need to spell "beneficiary"!

    USE THIS when user wants to:
    - List resources they can request
    - Find what resources are available for access request
    - See requestable resources for a user

    CRITICAL - Identity ID Field Name:
        WRONG: Do NOT use the "Id" field (e.g., 1006715) - this is the integer database ID
        CORRECT: Use the "UId" field (e.g., "2c68e1df-1335-4e8c-8ef9-eff1d2005629") - this is the 32-character UUID

        When you query an Identity record, it returns BOTH fields:
        - "Id": 1006715          <- WRONG - Do not use this!
        - "UId": "2c68e1df-..."  <- CORRECT - Use this as identity_id!

        YOU MUST extract the "UId" field (32-character UUID), NOT the "Id" field (integer).

    REQUIRED:
        identity_id: The user's identity UId (32-character UUID from the "UId" field, NOT the "Id" field!)
                    CORRECT example: "2c68e1df-1335-4e8c-8ef9-eff1d2005629" (UId field)
                    WRONG example: 1006715 (Id field - this will fail!)
        impersonate_user: Email address to impersonate (e.g., "ROBWOL@54MV4C.ONMICROSOFT.COM")

    OPTIONAL:
        system_id: Filter by specific system
        context_id: Filter by specific context
        resource_name: Resource name to filter by (string, partial match supported)
                      Example: "Sales" will match "Sales Team Access", "Sales Reports", etc.
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with list of requestable resources
    """
    # This is just an alias that calls the main function
    return await get_resources_for_beneficiary(
        identity_id=identity_id,
        impersonate_user=impersonate_user,
        system_id=system_id,
        context_id=context_id,
        resource_name=resource_name,
        omada_base_url=omada_base_url,
        scope=scope,
        bearer_token=bearer_token
    )


@with_function_logging
@mcp.tool()
async def get_identities_for_beneficiary(impersonate_user: str,
                                         page: int = None, rows: int = None,
                                         omada_base_url: str = None, scope: str = None,
                                         bearer_token: str = None) -> str:
    """
    Get a list of identities available for access requests using Omada GraphQL API.

    USE THIS FUNCTION when user asks to:
    - "list identities for access request"
    - "show identities I can request for"
    - "get beneficiary identities"
    - "list identities available for access requests"

    This function queries the accessRequestComponents.identities endpoint to get identities
    that can be used as beneficiaries in access requests.

    IMPORTANT: This function requires 1 mandatory parameter.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"

    Optional parameters:
        page: Page number for pagination (e.g., 1, 2, 3...)
        rows: Number of rows per page (e.g., 10, 20, 50...)
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with identities data including pagination metadata or error message
    """
    try:
        # Validate mandatory fields
        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        # Build pagination clause if provided
        pagination_clause = ""
        if page is not None and rows is not None:
            pagination_clause = f"pagination: {{page: {page}, rows: {rows}}}, "

        # Build GraphQL query with pagination
        query = f"""query GetIdentitiesForBeneficiary {{
  accessRequestComponents {{
    identities(
      {pagination_clause}filters: {{}}
    ) {{
      pages
      total
      data {{
        firstName
        displayName
        identityId
        id
        lastName
        contexts {{
          id
          displayName
        }}
      }}
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request
        result = await _execute_graphql_request(query, impersonate_user, omada_base_url, scope, bearer_token=bearer_token)

        if result["success"]:
            data = result["data"]
            # Extract identities from the GraphQL response
            if ('data' in data and 'accessRequestComponents' in data['data']):
                access_request_components = data['data']['accessRequestComponents']
                identities_obj = access_request_components.get('identities', {})
                identities = identities_obj.get('data', [])
                total = identities_obj.get('total', len(identities))
                pages = identities_obj.get('pages', 1)

                return json.dumps({
                    "status": "success",
                    "impersonated_user": impersonate_user,
                    "pagination": {
                        "current_page": page,
                        "rows_per_page": rows,
                        "total_identities": total,
                        "total_pages": pages
                    },
                    "identities_count": len(identities),
                    "identities": identities,
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_identities",
                    "impersonated_user": impersonate_user,
                    "message": "No identities found in response",
                    "response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
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
            "impersonated_user": impersonate_user,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)


@with_function_logging
@mcp.tool()
async def get_calculated_assignments_detailed(identity_id: str, impersonate_user: str,
                                             resource_type_name: str = None,
                                             compliance_status: str = None,
                                             omada_base_url: str = None,
                                             scope: str = None,
                                             bearer_token: str = None) -> str:
    """
    Get detailed calculated assignments with compliance and violation status using Omada GraphQL API.

    IMPORTANT: This function requires 2 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    CRITICAL - Identity ID Field Name:
        WRONG: Do NOT use the "IdentityID" field (e.g., "ROBWOL") - this is a user-readable identifier
        WRONG: Do NOT use the "Id" field (e.g., 1006715) - this is the integer database ID
        CORRECT: Use the "UId" field (e.g., "2c68e1df-1335-4e8c-8ef9-eff1d2005629") - this is the 32-character GUID

        When querying Identity data, you MUST:
        1. Query the Identity entity to get the user record
        2. Extract the "UId" field (NOT "Id" or "IdentityID") from the result
        3. Use that UId value as the identity_id parameter

        Example workflow:
        - Query: query_omada_identity with EMAIL filter returns {"UId": "2c68e1df-...", "Id": 1006715, "IdentityID": "ROBWOL"}
        - Use UId: "2c68e1df-..." as identity_id parameter (32 character GUID)
        - DO NOT use Id: 1006715 (this will fail!)
        - DO NOT use IdentityID: "ROBWOL" (this will fail!)

    REQUIRED PARAMETERS (prompt user if missing):
        identity_id: The identity UId (32-character GUID from the "UId" field, NOT the "Id" or "IdentityID" fields!)
                    Example: "2c68e1df-1335-4e8c-8ef9-eff1d2005629" (CORRECT - from UId field)
                    NOT: 1006715 (WRONG - this is the Id field)
                    NOT: "ROBWOL" (WRONG - this is the IdentityID field)
                    PROMPT: "Please provide the identity UId (32-character GUID from the UId field)"
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"

    Optional parameters:
        resource_type_name: Filter by resource type name (e.g., "Active Directory - Security Group")
                           Uses CONTAINS operator if provided
        compliance_status: Filter by compliance status (e.g., "NOT APPROVED", "APPROVED")
                          Uses CONTAINS operator if provided
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with detailed assignments including compliance status, violations, accounts, and resources
    """
    try:
        # Validate mandatory fields
        if not identity_id or not identity_id.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: identity_id",
                "error_type": "ValidationError"
            }, indent=2)

        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        # Build the filters object dynamically based on provided parameters
        filters = []

        # identityIds is always required
        filters.append(f'identityIds: "{identity_id}"')

        # Add optional filters only if provided
        if resource_type_name and resource_type_name.strip():
            filters.append(f'resourceTypeName: {{filterValue: "{resource_type_name}", operator: CONTAINS}}')

        if compliance_status and compliance_status.strip():
            filters.append(f'complianceStatus: {{filterValue: "{compliance_status}", operator: CONTAINS}}')

        # Join filters
        filters_string = ', '.join(filters)

        # Build GraphQL query with the filters
        query = f"""query GetCalculatedAssignmentsDetailed {{
  calculatedAssignments(
    filters: {{{filters_string}}}
  ) {{
    pages
    total
    data {{
      id
      complianceStatus
      disabled
      validFrom
      validTo
      violations {{
        description
        violationStatus
      }}
      account {{
        accountName
        accountType {{
          name
          id
        }}
        system {{
          name
          id
        }}
      }}
      identity {{
        identityId
        lastName
        firstName
        id
        accounts {{
          accountName
          system {{
            name
            id
          }}
        }}
      }}
      resource {{
        name
        id
        description
        system {{
          id
          name
        }}
        resourceType {{
          id
          name
        }}
      }}
      reason {{
        description
        reasonType
        causeObjectKey
      }}
    }}
  }}
}}"""

        #print(f"GraphQL query: {query}")
        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 2.19
        result = await _execute_graphql_request(
            query,
            impersonate_user,
            omada_base_url,
            scope,
            graphql_version="2.19",
            bearer_token=bearer_token
        )

        if result["success"]:
            data = result["data"]
            # Extract calculated assignments from the GraphQL response
            if ('data' in data and 'calculatedAssignments' in data['data']):
                calculated_assignments = data['data']['calculatedAssignments']
                assignments_data = calculated_assignments.get('data', [])
                total = calculated_assignments.get('total', 0)
                pages = calculated_assignments.get('pages', 0)

                return json.dumps({
                    "status": "success",
                    "identity_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "resource_type_name": resource_type_name,
                    "compliance_status": compliance_status,
                    "total_assignments": total,
                    "pages": pages,
                    "assignments_returned": len(assignments_data),
                    "assignments": assignments_data,
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_assignments",
                    "identity_id": identity_id,
                    "impersonated_user": impersonate_user,
                    "message": "No calculated assignments found in response",
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


@with_function_logging
@mcp.tool()
async def get_identity_contexts(identity_id: str, impersonate_user: str,
                               omada_base_url: str = None, scope: str = None,
                               bearer_token: str = None) -> str:
    """
    Get contexts for a specific identity using Omada GraphQL API.

    IMPORTANT: This function requires 2 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        identity_id: The identity ID to get contexts for (e.g., "e3e869c4-369a-476e-a969-d57059d0b1e4")
                    PROMPT: "Please provide the identity ID"
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"

    Optional parameters:
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with contexts data or error message
    """
    try:
        logger.debug(f"get_identity_contexts called with identity_id={identity_id}, impersonate_user={impersonate_user}")

        # Validate mandatory fields
        if not identity_id or not identity_id.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: identity_id",
                "error_type": "ValidationError"
            }, indent=2)

        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        logger.debug(f"Validation passed, building GraphQL query for identity_id: {identity_id}")

        # Build GraphQL query with the provided identity_id
        query = f"""query GetContextsForIdentity {{
  accessRequestComponents {{
    contexts(identityIds: "{identity_id}") {{
      id
      displayName
      type
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request
        result = await _execute_graphql_request(query, impersonate_user, omada_base_url, scope, bearer_token=bearer_token)

        if result["success"]:
            data = result["data"]
            # Extract contexts from the GraphQL response
            if ('data' in data and 'accessRequestComponents' in data['data']):
                access_request_components = data['data']['accessRequestComponents']
                contexts = access_request_components.get('contexts', [])

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


@with_function_logging
@mcp.tool()
async def get_pending_approvals(impersonate_user: str, workflow_step: str = None,
                                summary_mode: bool = True,
                                omada_base_url: str = None, scope: str = None,
                                bearer_token: str = None) -> str:
    """
    Get pending approval survey questions from Omada GraphQL API.

    IMPORTANT: This function requires 1 mandatory parameter. If missing,
    you MUST prompt the user to provide it before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"

    Optional parameters:
        workflow_step: Filter by workflow step (one of: "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")
                      If not provided, returns all pending approvals
        summary_mode: If True (default), returns only key fields (workflowStep, workflowStepTitle, reason)
                     If False, returns all fields including surveyId and surveyObjectKey
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with pending approval survey questions or error message
    """
    try:
        # Validate mandatory fields
        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        # Validate workflow_step if provided
        valid_workflow_steps = ["ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval"]
        if workflow_step and workflow_step not in valid_workflow_steps:
            return json.dumps({
                "status": "error",
                "message": f"Invalid workflow_step '{workflow_step}'. Must be one of: {', '.join(valid_workflow_steps)}",
                "error_type": "ValidationError"
            }, indent=2)

        # Build GraphQL query
        if workflow_step:
            # With filter
            query = f"""query myAccessRequestApprovalSurveyQuestions {{
  accessRequestApprovalSurveyQuestions(
    filters: {{workflowStep: {{filterValue: "{workflow_step}", operator: EQUALS}}}}
  ) {{
    pages
    total
    data {{
      reason
      surveyId
      surveyObjectKey
      workflowStep
      history
      workflowStepTitle
    }}
  }}
}}"""
        else:
            # Without filter - get all pending approvals
            query = """query myAccessRequestApprovalSurveyQuestions {
  accessRequestApprovalSurveyQuestions {
    pages
    total
    data {
      reason
      surveyId
      surveyObjectKey
      workflowStep
      history
      workflowStepTitle
    }
  }
}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.0
        result = await _execute_graphql_request(
            query,
            impersonate_user,
            omada_base_url,
            scope,
            graphql_version="3.0",
            bearer_token=bearer_token
        )

        if result["success"]:
            data = result["data"]
            # Extract approval questions from the GraphQL response
            if ('data' in data and 'accessRequestApprovalSurveyQuestions' in data['data']):
                approval_questions = data['data']['accessRequestApprovalSurveyQuestions']
                questions_data = approval_questions.get('data', [])
                total = approval_questions.get('total', 0)
                pages = approval_questions.get('pages', 0)

                # Apply summarization if requested
                response_data = questions_data
                if summary_mode:
                    logger.debug(f"Applying summarization to {len(questions_data)} pending approvals")
                    logger.debug(f"Original data fields: {list(questions_data[0].keys()) if questions_data else []}")
                    response_data = _summarize_graphql_data(questions_data, "PendingApproval")
                    logger.debug(f"Summarized data fields: {list(response_data[0].keys()) if response_data else []}")

                return json.dumps({
                    "status": "success",
                    "impersonated_user": impersonate_user,
                    "workflow_step_filter": workflow_step if workflow_step else "none",
                    "total_approvals": total,
                    "pages": pages,
                    "approvals_returned": len(response_data),
                    "summary_mode": summary_mode,
                    "approvals": response_data,
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_approvals",
                    "impersonated_user": impersonate_user,
                    "workflow_step_filter": workflow_step if workflow_step else "none",
                    "message": "No pending approvals found in response",
                    "response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
                "impersonated_user": impersonate_user,
                "workflow_step_filter": workflow_step if workflow_step else "none",
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
            "impersonated_user": impersonate_user,
            "workflow_step_filter": workflow_step if workflow_step else "none",
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)


@with_function_logging
@mcp.tool()
async def get_approval_details(impersonate_user: str, workflow_step: str = None,
                               omada_base_url: str = None, scope: str = None,
                               bearer_token: str = None) -> str:
    """
    Get FULL approval details including technical IDs (surveyId, surveyObjectKey) needed for making decisions.

    Use this function when you need to make an approval decision and need the technical IDs.
    This returns all fields including surveyId and surveyObjectKey which are required for make_approval_decision.

    IMPORTANT: This function requires 1 mandatory parameter.

    REQUIRED PARAMETERS:
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")

    Optional parameters:
        workflow_step: Filter by workflow step (one of: "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")
        omada_base_url: Omada instance URL
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with FULL approval details including surveyId and surveyObjectKey
    """
    # Call get_pending_approvals with summary_mode=False to get all fields
    return await get_pending_approvals(
        impersonate_user=impersonate_user,
        workflow_step=workflow_step,
        summary_mode=False,  # Get full details including technical IDs
        omada_base_url=omada_base_url,
        scope=scope,
        bearer_token=bearer_token
    )


@with_function_logging
@mcp.tool()
async def make_approval_decision(impersonate_user: str, survey_id: str,
                                 survey_object_key: str, decision: str,
                                 omada_base_url: str = None, scope: str = None,
                                 bearer_token: str = None) -> str:
    """
    Make an approval decision (APPROVE or REJECT) for an access request using Omada GraphQL API.

    IMPORTANT: This function requires 4 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        survey_id: The survey ID for the approval (e.g., "d67d8182-5d9e-466d-b9c2-d499a095e06a")
                  PROMPT: "Please provide the survey ID"
        survey_object_key: The survey object key for the approval (e.g., "40501018-04D0-4C67-A4BD-E698C109B60C")
                          PROMPT: "Please provide the survey object key"
        decision: The approval decision - must be either "APPROVE" or "REJECT"
                 PROMPT: "Please provide the decision (APPROVE or REJECT)"

    Optional parameters:
        omada_base_url: Omada instance URL (if not provided, uses OMADA_BASE_URL env var)
        scope: OAuth2 scope for the token
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with approval submission result or error message
    """
    try:
        # Validate mandatory fields
        if not impersonate_user or not impersonate_user.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: impersonate_user",
                "error_type": "ValidationError"
            }, indent=2)

        if not survey_id or not survey_id.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: survey_id",
                "error_type": "ValidationError"
            }, indent=2)

        if not survey_object_key or not survey_object_key.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: survey_object_key",
                "error_type": "ValidationError"
            }, indent=2)

        if not decision or not decision.strip():
            return json.dumps({
                "status": "error",
                "message": "Missing required field: decision",
                "error_type": "ValidationError"
            }, indent=2)

        # Validate decision value
        valid_decisions = ["APPROVE", "REJECT"]
        decision_upper = decision.strip().upper()
        if decision_upper not in valid_decisions:
            return json.dumps({
                "status": "error",
                "message": f"Invalid decision '{decision}'. Must be one of: {', '.join(valid_decisions)}",
                "error_type": "ValidationError"
            }, indent=2)

        # Build GraphQL mutation
        mutation = f"""mutation makeApprovalDecision {{
  submitRequestQuestions(
    submitRequestQuestionsInput: {{
      accessApprovals: {{
        questions: {{
          decision: {decision_upper},
          surveyObjectKey: "{survey_object_key}"}},
          surveyId: "{survey_id}"}}
        }}
  ) {{
    questionsSuccessfullySubmitted
  }}
}}"""

        logger.debug(f"GraphQL mutation: {mutation}")

        # Execute GraphQL request with version 3.0
        result = await _execute_graphql_request(
            query=mutation,
            impersonate_user=impersonate_user,
            omada_base_url=omada_base_url,
            scope=scope,
            graphql_version="3.0",
            bearer_token=bearer_token
        )

        if result["success"]:
            data = result["data"]
            # Extract submission result from the GraphQL response
            if ('data' in data and 'submitRequestQuestions' in data['data']):
                submission_result = data['data']['submitRequestQuestions']
                questions_submitted = submission_result.get('questionsSuccessfullySubmitted', False)

                return json.dumps({
                    "status": "success",
                    "impersonated_user": impersonate_user,
                    "survey_id": survey_id,
                    "survey_object_key": survey_object_key,
                    "decision": decision_upper,
                    "questions_successfully_submitted": questions_submitted,
                    "endpoint": result["endpoint"]
                }, indent=2)
            elif "errors" in data:
                # Handle GraphQL errors
                return json.dumps({
                    "status": "error",
                    "message": "GraphQL mutation failed",
                    "impersonated_user": impersonate_user,
                    "survey_id": survey_id,
                    "survey_object_key": survey_object_key,
                    "decision": decision_upper,
                    "errors": data["errors"],
                    "endpoint": result["endpoint"]
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Unexpected response format from submitRequestQuestions",
                    "impersonated_user": impersonate_user,
                    "survey_id": survey_id,
                    "survey_object_key": survey_object_key,
                    "decision": decision_upper,
                    "response": data
                }, indent=2)
        else:
            # Handle GraphQL request failure
            error_result = {
                "status": "error",
                "impersonated_user": impersonate_user,
                "survey_id": survey_id,
                "survey_object_key": survey_object_key,
                "decision": decision_upper,
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
            "impersonated_user": impersonate_user,
            "survey_id": survey_id if 'survey_id' in locals() else "N/A",
            "survey_object_key": survey_object_key if 'survey_object_key' in locals() else "N/A",
            "decision": decision if 'decision' in locals() else "N/A",
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

if __name__ == "__main__":
    mcp.run()
