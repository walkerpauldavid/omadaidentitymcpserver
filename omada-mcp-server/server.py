# server.py
import asyncio
import base64
import hashlib
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp.server import Context, FastMCP

# Load environment variables FIRST
load_dotenv()

# Configure logging system BEFORE importing any other modules
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configure cache logger - it will use root logger's handlers via propagation
cache_logger = logging.getLogger("cache")
cache_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
# Don't add handlers, let it propagate to root logger
cache_logger.propagate = True

logger.info(f"Logging initialized. Writing logs to: {os.path.abspath(LOG_FILE)}")
logger.info(f"Cache logger will use root logger handlers (level: {LOG_LEVEL})")

# NOW import modules that create loggers - logging is already configured
from helpers import (
    build_error_response,
    build_pagination_clause,
    build_success_response,
    json_to_graphql_syntax,
    validate_required_fields,
)

# from cache import OmadaCache
# from cache_config import get_ttl_for_operation, should_cache, DEFAULT_TTL

logger.info("All modules imported successfully")


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
        logger.debug(
            f"Function '{function_name}' using log level: {logging.getLevelName(new_level)}"
        )

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
            # Log function entrance at INFO level
            logger.info(f"ENTERING function: {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                # Log function exit at INFO level
                logger.info(f"EXITING function: {func.__name__}")
                return result
            except Exception as e:
                # Log function exit with error at INFO level
                logger.info(
                    f"EXITING function: {func.__name__} with error: {type(e).__name__}"
                )
                raise
            finally:
                # Restore logger level
                logger.setLevel(old_level)
                # Restore handler levels
                for handler, level in old_handler_levels:
                    handler.setLevel(level)

        # Manually preserve metadata without setting __wrapped__ (which causes FastMCP to bypass decorator)
        async_wrapper.__name__ = func.__name__
        async_wrapper.__doc__ = func.__doc__
        async_wrapper.__module__ = func.__module__
        async_wrapper.__qualname__ = func.__qualname__
        async_wrapper.__annotations__ = func.__annotations__
        # Also update __dict__ as functools.wraps does
        async_wrapper.__dict__.update(func.__dict__)
        return async_wrapper
    else:

        def sync_wrapper(*args, **kwargs):
            old_level, old_handler_levels = set_function_logger_level(func.__name__)
            # Log function entrance at INFO level
            logger.info(f"ENTERING function: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                # Log function exit at INFO level
                logger.info(f"EXITING function: {func.__name__}")
                return result
            except Exception as e:
                # Log function exit with error at INFO level
                logger.info(
                    f"EXITING function: {func.__name__} with error: {type(e).__name__}"
                )
                raise
            finally:
                # Restore logger level
                logger.setLevel(old_level)
                # Restore handler levels
                for handler, level in old_handler_levels:
                    handler.setLevel(level)

        # Manually preserve metadata without setting __wrapped__ (which causes FastMCP to bypass decorator)
        sync_wrapper.__name__ = func.__name__
        sync_wrapper.__doc__ = func.__doc__
        sync_wrapper.__module__ = func.__module__
        sync_wrapper.__qualname__ = func.__qualname__
        sync_wrapper.__annotations__ = func.__annotations__
        # Also update __dict__ as functools.wraps does
        sync_wrapper.__dict__.update(func.__dict__)
        return sync_wrapper


# Custom Exception Classes
class OmadaServerError(Exception):
    """Base exception for Omada server errors"""

    def __init__(
        self, message: str, status_code: int = None, response_body: str = None
    ):
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

# Initialize caching system
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # Default 1 hour
CACHE_AUTO_CLEANUP = os.getenv("CACHE_AUTO_CLEANUP", "true").lower() == "true"

if CACHE_ENABLED:
    # cache = OmadaCache(default_ttl=CACHE_TTL_SECONDS, auto_cleanup=CACHE_AUTO_CLEANUP)
    logger.info(f"✅ Cache system DISABLED (cache module not available)")
    CACHE_ENABLED = False
else:
    cache = None
    logger.info("⚠️ Cache system DISABLED")

# Register MCP Prompts for workflow guidance
from prompts import register_prompts

register_prompts(mcp)

# Register MCP Completions for autocomplete suggestions
from completions import register_completions

register_completions(mcp)

# Register MCP Resources for entity schema definitions
from schemas import register_schemas

register_schemas(mcp)


def _get_omada_base_url(omada_base_url: str = None) -> str:
    """
    Get Omada base URL from parameter or environment variable.

    Args:
        omada_base_url: Optional base URL parameter

    Returns:
        Base URL with trailing slash removed

    Raises:
        Exception if base URL not found in parameter or environment
    """
    if not omada_base_url:
        omada_base_url = os.getenv("OMADA_BASE_URL")
        if not omada_base_url:
            raise Exception(
                "OMADA_BASE_URL not found in environment variables or parameters"
            )
    return omada_base_url.rstrip("/")


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
        "Identity": [
            "Id",
            "UId",
            "DISPLAYNAME",
            "FIRSTNAME",
            "LASTNAME",
            "EMAIL",
            "EMPLOYEEID",
            "DEPARTMENT",
            "STATUS",
        ],
        "Resource": [
            "Id",
            "DISPLAYNAME",
            "DESCRIPTION",
            "RESOURCEKEY",
            "STATUS",
            "Systemref",
        ],
        "Role": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "Account": ["Id", "ACCOUNTNAME", "DISPLAYNAME", "STATUS", "SYSTEM"],
        "Application": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "System": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "CalculatedAssignments": [
            "Id",
            "AssignmentKey",
            "AccountName",
            "Identity",
            "Resource",
        ],
        "AssignmentPolicy": ["Id", "DISPLAYNAME", "DESCRIPTION", "STATUS"],
        "Orgunit": [
            "Id",
            "UId",
            "DisplayName",
            "NAME",
            "OUID",
            "OUTYPE",
            "PARENTOU",
            "MANAGER",
            "EXPLICITOWNER",
            "C_ADOU",
        ],
    }

    # Get relevant fields for this entity type
    fields_to_keep = summary_fields.get(
        entity_type, ["Id", "DISPLAYNAME", "DESCRIPTION"]
    )

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
        "PendingApproval": [
            "workflowStep",
            "workflowStepTitle",
            "reason",
            "resourceAssignment",
        ],
        "AccessRequest": ["id", "beneficiary", "resource", "status", "requestedBy", "reason", "validFrom", "validTo"],
        "CalculatedAssignment": ["complianceStatus", "account", "resource", "identity"],
        "Context": ["id", "displayName", "type"],
        "Resource": ["id", "name", "description", "system"],
    }

    # Define fields to explicitly exclude (technical fields users shouldn't see)
    exclude_fields = {
        "PendingApproval": ["surveyId", "surveyObjectKey", "history"],
        "AccessRequest": [],
        "CalculatedAssignment": [],
        "Context": [],
        "Resource": [],
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


@with_function_logging
@mcp.tool()
async def query_omada_entity(
    entity_type: str = "Identity",
    filters: dict = None,
    count_only: bool = False,
    summary_mode: bool = True,
    top: int = None,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    expand: str = None,
    include_count: bool = False,
    bearer_token: str = None,
    impersonate_user: str = None,
) -> str:
    """
    Generic query function for any Omada entity type (Identity, Resource, Role, etc).

    IMPORTANT - $expand LIMITATION:
        Omada OData does NOT support $expand on DataObjects endpoints (Identity, Resource,
        Orgunit, Role, Account, Application, System, AssignmentPolicy).
        $expand ONLY works on BuiltIn/CalculatedAssignments with: Identity, Resource, ResourceType.
        Reference fields (e.g., MANAGER, OUTYPE, SYSTEMREF) are returned as inline nested objects
        automatically — no $expand needed. The expand parameter will be IGNORED for DataObjects
        entities to prevent 400 Bad Request errors.

    IMPORTANT - any() LAMBDA FILTER NOT SUPPORTED:
        Omada OData does NOT support the any() lambda operator on collection-type reference fields.
        Filters like OWNERREF/any(o: o/Id eq 123), MANAGER/any(), CHILDROLES/any(),
        EXPLICITOWNER/any(), MANUALOWNER/any(o: o/Id eq 123) will return 500 Internal Server Error.
        This is a limitation of Omada's OData implementation (subset of OData spec).
        DO NOT use any() or all() lambda expressions in $filter.
        Workaround: Retrieve all records and filter client-side, or use GraphQL API instead.

    IMPORTANT - Key Identity Field Names (use EXACTLY as shown - all UPPERCASE):

        Core Fields:
        - EMAIL (not "email", "MAIL", or "EMAILADDRESS")
        - FIRSTNAME (not "firstname" or "first_name")
        - LASTNAME (not "lastname" or "last_name")
        - DISPLAYNAME (not "displayname" or "display_name")
        - IDENTITYID (the user's login ID, not "identity_id")
        - EMPLOYEEID (not "employee_id" or "EmployeeId")
        - JOBTITLE (not "job_title" or "JobTitle")
        - DEPARTMENT (not "department")
        - COMPANY (not "company")
        - STATUS (not "status")

        Reference Fields (returned as inline nested objects - DO NOT use $expand):
        - JOBTITLE_REF (returns inline job title object with Id, DisplayName, etc.)
        - COMPANY_REF (returns inline company/organization object)
        - MANAGER_REF (returns inline manager identity details)
        - DEPARTMENT_REF (returns inline department object)

        Other Important Fields:
        - UId (32-character GUID - use for identity_id in GraphQL functions)
        - Id (integer database ID - rarely used)
        - LOCATION (physical location/office)
        - COSTCENTER (cost center code)
        - TITLE (may be different from JOBTITLE in some configurations)

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
        count_only: If True, returns only the count of matching records
        summary_mode: If True, returns only key fields as a summary instead of full objects
        top: Maximum number of records to return (OData $top)
        skip: Number of records to skip (OData $skip)
        select_fields: Comma-separated list of fields to select (OData $select).
                WARNING: Only use with scalar fields (e.g., NAME, EMAIL, FIRSTNAME).
                Using $select with reference/collection fields (e.g., MANAGER, SYSTEMREF,
                OUTYPE, JOBTITLE_REF) returns EMPTY objects. Omit $select to get reference data.
        order_by: Field(s) to order by (OData $orderby)
        expand: Comma-separated list of related entities to expand (OData $expand).
                ONLY supported for CalculatedAssignments (valid values: Identity, Resource, ResourceType).
                Ignored for all other entity types (DataObjects endpoints do not support $expand).
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

        # CalculatedAssignments for specific identity (expand IS supported here)
        await query_omada_entity("CalculatedAssignments", filters={
            "identity_id": 1006500
        }, expand="Identity,Resource,ResourceType")

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
        valid_entities = [
            "Identity",
            "Resource",
            "Role",
            "Account",
            "Application",
            "System",
            "CalculatedAssignments",
            "AssignmentPolicy",
            "Orgunit",
        ]
        if entity_type not in valid_entities:
            return f"❌ Invalid entity type '{entity_type}'. Valid types: {', '.join(valid_entities)}"

        # Get base URL using helper function (reads from environment)
        try:
            omada_base_url = _get_omada_base_url()
        except Exception as e:
            return f"❌ {str(e)}"

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
                if (
                    isinstance(field_filter, dict)
                    and "field" in field_filter
                    and "value" in field_filter
                ):
                    field_name = field_filter["field"]
                    field_value = field_filter["value"]
                    field_operator = field_filter.get("operator", "eq")
                    auto_filters.append(
                        _build_odata_filter(field_name, field_value, field_operator)
                    )

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
            query_params["$filter"] = " and ".join(all_filters)

        # Add count parameter if requested
        if count_only:
            query_params["$count"] = "true"
            query_params["$top"] = "0"  # Don't return actual records, just count
        else:
            # Add other OData parameters
            if top:
                query_params["$top"] = str(top)
            if skip:
                query_params["$skip"] = str(skip)
            if select_fields:
                query_params["$select"] = select_fields
            if order_by:
                query_params["$orderby"] = order_by
            # IMPORTANT: $expand is ONLY supported on BuiltIn endpoints (e.g., CalculatedAssignments).
            # DataObjects endpoints (Identity, Resource, Orgunit, Role, etc.) return reference
            # fields as inline nested objects automatically and do NOT support $expand (returns 400).
            if expand:
                if entity_type == "CalculatedAssignments":
                    query_params["$expand"] = expand
                else:
                    logger.warning(
                        f"$expand is not supported for DataObjects/{entity_type} endpoint "
                        f"(requested: {expand}). Ignoring $expand parameter. "
                        f"Reference fields are returned as inline nested objects automatically."
                    )
            if include_count:
                query_params["$count"] = "true"

        # Construct final URL with query parameters
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            endpoint_url = f"{endpoint_url}?{query_string}"

        # Bearer token is always required (OAuth functions migrated to oauth_mcp_server)
        if bearer_token:
            logger.debug("Using provided bearer token for OData request")
            # Strip "Bearer " prefix if already present to avoid double-prefix
            clean_token = (
                bearer_token.replace("Bearer ", "").replace("bearer ", "").strip()
            )
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
                    return build_success_response(
                        data=None,
                        endpoint=endpoint_url,
                        entity_type=entity_type,
                        count=count,
                        filter=query_params.get("$filter", "none"),
                    )
                else:
                    # Return full data with metadata
                    entities_found = len(data.get("value", []))
                    total_count = data.get(
                        "@odata.count"
                    )  # Available if $count=true was included

                    # Apply summarization if requested
                    response_data = data
                    if summary_mode:
                        response_data = _summarize_entities(data, entity_type)

                    # Build response with entity-specific metadata
                    extra_fields = {
                        "entity_type": entity_type,
                        "entities_returned": entities_found,
                        "total_count": total_count,
                        "filter": query_params.get("$filter", "none"),
                        "summary_mode": summary_mode,
                    }

                    # Add entity-specific metadata
                    if entity_type == "Resource" and resource_type_id:
                        extra_fields["resource_type_id"] = resource_type_id

                    return build_success_response(
                        data=response_data, endpoint=endpoint_url, **extra_fields
                    )
            elif response.status_code == 400:
                raise ODataQueryError(
                    f"Bad request - invalid OData query: {response.text[:200]}",
                    response.status_code,
                )
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed - token may be expired", response.status_code
                )
            elif response.status_code == 403:
                raise AuthenticationError(
                    "Access forbidden - insufficient permissions", response.status_code
                )
            elif response.status_code == 404:
                raise OmadaServerError(
                    "Omada endpoint not found - check base URL", response.status_code
                )
            elif response.status_code >= 500:
                raise OmadaServerError(
                    f"Omada server error: {response.status_code}",
                    response.status_code,
                    response.text,
                )
            else:
                raise OmadaServerError(
                    f"Unexpected response: {response.status_code}",
                    response.status_code,
                    response.text,
                )

    except AuthenticationError as e:
        return build_error_response(error_type="AuthenticationError", message=str(e))
    except ODataQueryError as e:
        return build_error_response(error_type="ODataQueryError", message=str(e))
    except OmadaServerError as e:
        return build_error_response(error_type="OmadaServerError", message=str(e))
    except httpx.RequestError as e:
        return build_error_response(error_type="NetworkError", message=str(e))
    except Exception as e:
        return build_error_response(error_type=type(e).__name__, message=str(e))


@with_function_logging
@mcp.tool()
async def query_omada_identity(
    field_filters: list = None,
    filter_condition: str = None,
    count_only: bool = False,
    summary_mode: bool = True,
    top: int = None,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    include_count: bool = False,
    bearer_token: str = None,
) -> str:
    """
    Query Omada Identity entities (wrapper for query_omada_entity).

    IMPORTANT LLM INSTRUCTIONS - UId Field Handling:
        When summary_mode=True (default), the response includes the UId field:
        1. DO NOT display the "UId" field to the user in your responses
        2. ONLY show user-friendly fields: DISPLAYNAME, FIRSTNAME, LASTNAME, EMAIL, EMPLOYEEID, DEPARTMENT, STATUS
        3. INTERNALLY store/remember the "UId" value for each identity
        4. When the user selects an identity by name/email, USE the corresponding "UId" value
           for any subsequent API calls that require an identity_id or identity_ids parameter
        5. The "UId" is a 32-character GUID (e.g., "2c68e1df-1335-4e8c-8ef9-eff1d2005629") required
           by GraphQL functions but not useful for end users to see

        Example user presentation:
        "Found identity: Robert Wolf (ROBWOL@domain.com)
        Department: Finance, Employee ID: EMP12345"

        But internally remember:
        - Robert Wolf: UId="2c68e1df-1335-4e8c-8ef9-eff1d2005629"

        When user says "Get assignments for Robert Wolf", use UId="2c68e1df-1335-4e8c-8ef9-eff1d2005629"
        in the identity_ids parameter.

    IMPORTANT - Identity Field Names (use EXACTLY as shown):
        - EMAIL (not "email", "MAIL", or "EMAILADDRESS")
        - FIRSTNAME (not "firstname" or "first_name")
        - LASTNAME (not "lastname" or "last_name")
        - DISPLAYNAME, EMPLOYEEID, DEPARTMENT, STATUS

    IMPORTANT - OData Limitations:
        1. $expand is NOT supported. Reference fields (JOBTITLE_REF, MANAGER_REF, etc.)
           are returned as inline nested objects automatically.
        2. $select with reference fields (JOBTITLE_REF, MANAGER_REF, COMPANY_REF,
           DEPARTMENT_REF) returns EMPTY objects. Only use $select with scalar fields
           (EMAIL, FIRSTNAME, LASTNAME, etc.). To get reference data, omit $select.
        3. any()/all() lambda filters are NOT supported on collection fields.
           Filters like MANAGER/any(m: m eq 'xxx') return 500 Internal Server Error.
           Retrieve all records and filter client-side instead.

    Args:
        field_filters: List of field filters:
                      [{"field": "EMAIL", "value": "user@domain.com", "operator": "eq"},
                       {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
                       {"field": "LASTNAME", "value": "Taylor", "operator": "startswith"}]
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select. WARNING: Only use with
                      scalar fields (EMAIL, FIRSTNAME, etc.). Reference fields in $select
                      return empty objects. Omit to get all fields including references.
        order_by: Field(s) to order by
        include_count: Include total count in response
        bearer_token: Optional bearer token to use instead of acquiring a new one
        summary_mode: If True (default), returns only key fields including UId (use UId internally, don't display to user)

    Returns:
        JSON response with identity data including:
        - UId: 32-character GUID (for internal use in subsequent API calls - don't display to user)
        - DISPLAYNAME, FIRSTNAME, LASTNAME, EMAIL: User-friendly display fields
        - EMPLOYEEID, DEPARTMENT, STATUS: Additional identity attributes

    Schema Reference:
        For complete field definitions, types, and examples, query: schema://omada/identity
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
        count_only=count_only,
        summary_mode=summary_mode,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def query_omada_resources(
    resource_type_id: int = None,
    resource_type_name: str = None,
    system_id: int = None,
    filter_condition: str = None,
    count_only: bool = False,
    top: int = None,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    include_count: bool = False,
    bearer_token: str = None,
) -> str:
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

    IMPORTANT - OData Limitations:
        1. $expand is NOT supported. Reference fields (SYSTEMREF, ROLETYPEREF, etc.)
           are returned as inline nested objects automatically.
        2. $select with reference fields (SYSTEMREF, ROLETYPEREF, ROLECATEGORY,
           ROLEFOLDER, OWNERREF, CHILDROLES, etc.) returns EMPTY objects.
           Only use $select with scalar fields (NAME, DESCRIPTION, ROLEID, etc.).
           To get reference data, omit $select.
        3. any()/all() lambda filters are NOT supported on collection fields.
           Filters like OWNERREF/any(o: o/Id eq 123), CHILDROLES/any(),
           MANUALOWNER/any(o: o/Id eq 123) return 500 Internal Server Error.
           Retrieve all records and filter client-side instead.

    Query Omada Resource entities (wrapper for query_omada_entity).

    Args:
        resource_type_id: Numeric ID for resource type (e.g., 1011066 for Application Roles)
        resource_type_name: Name-based lookup for resource type (e.g., "APPLICATION_ROLES")
        system_id: Numeric ID for system reference to filter resources by system (e.g., 1011066)
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select. WARNING: Only use with
                      scalar fields (NAME, DESCRIPTION, ROLEID, etc.). Reference fields
                      in $select return empty objects. Omit to get all fields.
        order_by: Field(s) to order by
        include_count: Include total count in response
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with resource data or error message

    Schema Reference:
        For complete Resource field definitions: schema://omada/resource
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
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def query_omada_orgunits(
    field_filters: list = None,
    filter_condition: str = None,
    count_only: bool = False,
    summary_mode: bool = True,
    top: int = None,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    include_count: bool = False,
    bearer_token: str = None,
) -> str:
    """
    Query Omada OrgUnit (Organizational Unit) entities using OData API.

    Use this to look up organizational units such as departments, divisions, teams,
    or any hierarchical organizational structure defined in Omada.

    IMPORTANT - OData Limitations for OrgUnit:
        1. $expand is NOT supported. Reference fields (OUTYPE, PARENTOU, MANAGER, etc.)
           are returned as inline nested objects automatically — no $expand needed.
        2. $select with reference fields (MANAGER, EXPLICITOWNER, OUTYPE, PARENTOU, etc.)
           returns EMPTY objects. Do NOT use $select with reference/collection fields.
           Only use $select with scalar fields like: NAME, OUID, C_ADOU, ODWBUSIKEY.
           To get reference field data, omit $select entirely (or use summary_mode=True
           which returns key fields without using $select).
        3. any()/all() lambda filters are NOT supported on collection fields.
           Filters like MANAGER/any(), EXPLICITOWNER/any(o: o/Id eq 123) return
           500 Internal Server Error. Retrieve all records and filter client-side instead.

    IMPORTANT - Key OrgUnit Field Names (use EXACTLY as shown - all UPPERCASE):
        Scalar Fields (safe to use with $select):
        - OUID (the OrgUnit's unique business identifier, e.g., "ORGANIZATION")
        - NAME (display name of the OrgUnit, e.g., "Organization")
        - ODWBUSIKEY (data warehouse business key)
        - C_ADOU (Active Directory OU path)

        Reference Fields (returned inline - do NOT use with $select):
        - OUTYPE (OrgUnit type - e.g., "Organization", "Department", "Team")
        - PARENTOU (parent OrgUnit in the hierarchy)
        - MANAGER (manager(s) of this OrgUnit)
        - EXPLICITOWNER (explicit owner(s) of this OrgUnit)
        - ROLESREF (roles associated with this OrgUnit)
        - CONTEXTSTATUS (context status of the OrgUnit)

        Other Fields:
        - UId (32-character GUID)
        - Id (integer database ID)
        - DisplayName (formatted display name, e.g., "Organization [ORGANIZATION]")
        - Deleted (boolean indicating if the OrgUnit has been deleted)
        - CLT_TAGS (tags associated with the OrgUnit)
        - SERVICEDESKAGENTS (service desk agents for the OrgUnit)
        - EXPLICITSERVICEDESKAGENTS (explicit service desk agents)

    Example: Query an OrgUnit by name (returns all fields including references):
        field_filters=[{"field": "NAME", "value": "Organization", "operator": "eq"}]

    Example: Get all OrgUnits with summary (includes OUTYPE, PARENTOU, MANAGER inline):
        query_omada_orgunits(top=100, summary_mode=True)

    Example: Get full OrgUnit records with all fields:
        query_omada_orgunits(top=100, summary_mode=False)

    Args:
        field_filters: List of field filters:
                      [{"field": "NAME", "value": "Finance", "operator": "eq"},
                       {"field": "OUID", "value": "FIN", "operator": "eq"}]
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count of matching records
        summary_mode: If True (default), returns key fields: NAME, OUID, OUTYPE, PARENTOU,
                     MANAGER, EXPLICITOWNER, C_ADOU. If False, returns all fields.
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select. WARNING: Only use with
                      scalar fields (NAME, OUID, C_ADOU). Using $select with reference
                      fields (MANAGER, OUTYPE, PARENTOU, etc.) returns empty objects.
                      Omit this to get reference field data.
        order_by: Field(s) to order by
        include_count: Include total count in response
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with OrgUnit data or error message

    Schema Reference:
        For complete OrgUnit field definitions: schema://omada/orgunit
    """
    # Build filters dictionary for clean API
    filters = {}
    if field_filters:
        filters["field_filters"] = field_filters
    if filter_condition:
        filters["custom_filter"] = filter_condition

    return await query_omada_entity(
        entity_type="Orgunit",
        filters=filters if filters else None,
        count_only=count_only,
        summary_mode=summary_mode,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def query_omada_entities(
    entity_type: str = "Identity",
    field_filters: list = None,
    filter_condition: str = None,
    count_only: bool = False,
    top: int = None,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    include_count: bool = False,
    bearer_token: str = None,
) -> str:
    """
    Modern generic query function for Omada entities using field filters.

    IMPORTANT - OData Limitations:
        1. $expand is NOT supported on DataObjects endpoints (Identity, Resource, Orgunit, etc.).
           Reference fields are returned as inline nested objects automatically — no $expand needed.
           $expand only works on BuiltIn/CalculatedAssignments (use query_calculated_assignments instead).
        2. $select with reference/collection fields returns EMPTY objects. Only use $select with
           scalar fields. Omit $select entirely to get reference field data.
        3. any()/all() lambda filters are NOT supported on collection fields (returns 500 error).
           Retrieve all records and filter client-side instead.

    Args:
        entity_type: Type of entity to query (Identity, Resource, Orgunit, System, etc)
        field_filters: List of field filters:
                      [{"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
                       {"field": "LASTNAME", "value": "Taylor", "operator": "startswith"}]
        filter_condition: Custom OData filter condition
        count_only: If True, returns only the count
        top: Maximum number of records to return
        skip: Number of records to skip
        select_fields: Comma-separated list of fields to select. WARNING: Only use with
                      scalar fields. Reference fields in $select return empty objects.
        order_by: Field(s) to order by
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
        count_only=count_only,
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        include_count=include_count,
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def query_calculated_assignments(
    identity_id: int = None,
    select_fields: str = "AssignmentKey,AccountName",
    expand: str = "Identity,Resource,ResourceType",
    filter_condition: str = None,
    top: int = None,
    skip: int = None,
    order_by: str = None,
    include_count: bool = False,
    bearer_token: str = None,
) -> str:
    """
    Query Omada CalculatedAssignments entities (wrapper for query_omada_entity).

    NOTE: This is the ONLY Omada OData endpoint that supports $expand.
    Valid $expand values: Identity, Resource, ResourceType (can be combined with commas).
    Do NOT use $expand with $select that includes fields not on the base entity (e.g.,
    ComplianceStatus, AssignmentReasons) as this causes 400 errors.

    Args:
        identity_id: Numeric ID for identity to get assignments for (e.g., 1006500)
        select_fields: Fields to select (default: "AssignmentKey,AccountName")
        expand: Related entities to expand (default: "Identity,Resource,ResourceType").
                ONLY valid values: Identity, Resource, ResourceType.
        filter_condition: Custom OData filter condition
        top: Maximum number of records to return
        skip: Number of records to skip
        order_by: Field(s) to order by
        include_count: Include total count in response
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        JSON response with calculated assignments data or error message

    Schema Reference:
        For Identity field definitions: schema://omada/identity
        For Resource field definitions: schema://omada/resource
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
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        expand=expand,
        include_count=include_count,
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def get_all_omada_identities(
    top: int = 1000,
    skip: int = None,
    select_fields: str = None,
    order_by: str = None,
    include_count: bool = True,
    bearer_token: str = None,
) -> str:
    """
    Retrieve all identities from Omada Identity system with pagination support.

    Args:
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
        top=top,
        skip=skip,
        select_fields=select_fields,
        order_by=order_by,
        filter_condition=None,  # No filter to get all
        include_count=include_count,
        bearer_token=bearer_token,
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
            config["error"] = (
                f"Missing required environment variables: {', '.join(missing)}"
            )
        else:
            config["status"] = "VALID"

        # Add note about OAuth migration
        config["note"] = (
            "OAuth token functions have been migrated to oauth_mcp_server. All Omada functions require bearer_token parameter."
        )
        config["usage_example"] = (
            "get_pending_approvals(impersonate_user='user@domain.com', bearer_token='eyJ0...')"
        )

        return build_success_response(data=config)

    except Exception as e:
        return build_error_response(error_type=type(e).__name__, message=str(e))


@with_function_logging
@mcp.tool()
async def get_cache_stats() -> str:
    """
    Get cache statistics and performance metrics.

    Shows:
    - Number of cached entries (total, valid, expired)
    - Cache hit counts
    - Most frequently accessed endpoints
    - Cache configuration (enabled/disabled, TTL)

    Returns:
        JSON string with cache statistics
    """
    try:
        if not CACHE_ENABLED or cache is None:
            return json.dumps(
                {
                    "cache_enabled": False,
                    "message": "Cache is disabled. Set CACHE_ENABLED=true in .env to enable caching.",
                },
                indent=2,
            )

        # Get stats from cache
        stats = cache.get_stats()

        # Clean up expired entries
        expired_count = cache.cleanup_expired()

        result = {
            "cache_enabled": True,
            "cache_statistics": stats,
            "expired_entries_cleaned": expired_count,
            "configuration": {
                "default_ttl_seconds": CACHE_TTL_SECONDS,
                "cache_file": stats.get("cache_file", "omada_cache.db"),
            },
        }

        logger.info(
            f"📊 Cache stats requested - Valid entries: {stats['api_cache']['valid_entries']}, Hits: {stats['api_cache']['total_hits']}"
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__, message=f"Error getting cache stats: {str(e)}"
        )


@with_function_logging
@mcp.tool()
async def clear_cache(endpoint: str = None) -> str:
    """
    Clear cache entries.

    IMPORTANT: Use this tool when you need fresh data from the Omada API.

    Common scenarios:
    - After making changes in Omada (new assignments, approvals, etc.)
    - When cache might be stale
    - To force a fresh API call

    Args:
        endpoint: Optional specific endpoint to clear (e.g., "graphql", "identity")
                 If not provided, clears ALL cache entries

    Examples:
        clear_cache()                    # Clear entire cache
        clear_cache(endpoint="graphql")  # Clear only GraphQL cache

    Returns:
        Success message with count of cleared entries
    """
    try:
        if not CACHE_ENABLED or cache is None:
            return json.dumps(
                {
                    "cache_enabled": False,
                    "message": "Cache is disabled. No cache entries to clear.",
                },
                indent=2,
            )

        # Clear cache
        deleted_count = cache.invalidate(endpoint=endpoint)

        if endpoint:
            message = f"✅ Cache cleared for endpoint: {endpoint}"
            logger.info(
                f"🗑️ Cache cleared for endpoint '{endpoint}' - {deleted_count} entries deleted"
            )
        else:
            message = f"✅ Entire cache cleared"
            logger.info(f"🗑️ ENTIRE cache cleared - {deleted_count} entries deleted")

        return json.dumps(
            {
                "success": True,
                "message": message,
                "entries_deleted": deleted_count,
                "endpoint": endpoint or "all",
            },
            indent=2,
        )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__, message=f"Error clearing cache: {str(e)}"
        )


@with_function_logging
@mcp.tool()
async def view_cache_contents_detailed(
    limit: int = 10, include_expired: bool = False
) -> str:
    """
    View detailed cache contents including FULL parameters for debugging.

    Shows complete query parameters to help identify why duplicate entries exist.
    Useful for debugging cache key generation issues.

    Args:
        limit: Maximum number of entries to show (default: 10, lower for readability)
        include_expired: Whether to include expired entries (default: False)

    Returns:
        JSON with detailed cache entries including full query parameters
    """
    try:
        if not CACHE_ENABLED or cache is None:
            return json.dumps(
                {
                    "cache_enabled": False,
                    "message": "Cache is disabled. No cache contents to view.",
                },
                indent=2,
            )

        # Get raw cache data from database
        import sqlite3

        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        now = datetime.now()

        where_clause = "" if include_expired else "WHERE expires_at > ?"
        params = [] if include_expired else [now]

        cursor.execute(
            f"""
            SELECT
                cache_key,
                endpoint,
                query_params,
                created_at,
                expires_at,
                hit_count,
                last_accessed
            FROM api_cache
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """,
            params + [limit],
        )

        entries = []
        for row in cursor.fetchall():
            (
                cache_key,
                endpoint,
                query_params,
                created_at,
                expires_at,
                hit_count,
                last_accessed,
            ) = row
            created_dt = datetime.fromisoformat(created_at)
            expires_dt = datetime.fromisoformat(expires_at)
            age_seconds = (now - created_dt).total_seconds()
            ttl_remaining = (expires_dt - now).total_seconds()

            # Parse full query params
            try:
                params_dict = json.loads(query_params)
            except:
                params_dict = {"error": "Could not parse params", "raw": query_params}

            entries.append(
                {
                    "cache_key": cache_key,
                    "cache_key_short": cache_key[:16] + "...",
                    "endpoint": endpoint,
                    "full_params": params_dict,  # FULL PARAMETERS
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "age_seconds": round(age_seconds, 1),
                    "ttl_remaining_seconds": round(ttl_remaining, 1),
                    "hit_count": hit_count,
                    "last_accessed": last_accessed,
                    "status": "valid" if expires_dt > now else "expired",
                }
            )

        conn.close()

        result = {
            "detailed_entries": entries,
            "total_shown": len(entries),
            "limit": limit,
            "include_expired": include_expired,
            "note": "This shows FULL parameters to debug duplicate entries",
        }

        logger.info(
            f"📋 Detailed cache contents viewed - {len(entries)} entries with full params"
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=f"Error viewing detailed cache contents: {str(e)}",
        )


@with_function_logging
@mcp.tool()
async def view_cache_contents(limit: int = 50, include_expired: bool = False) -> str:
    """
    View the actual contents of the cache.

    Shows what data is currently cached, including:
    - Endpoint names and parameters
    - Cache status (valid/expired)
    - Age and time remaining until expiration
    - Hit counts (how many times each entry was accessed)
    - Identity cache entries (cached users)

    This is useful for:
    - Understanding what data is cached
    - Debugging cache behavior
    - Identifying frequently accessed data
    - Checking cache freshness

    Args:
        limit: Maximum number of entries to show per cache type (default: 50)
        include_expired: Whether to include expired entries (default: False)

    Examples:
        view_cache_contents()                          # Show 50 most recent valid entries
        view_cache_contents(limit=100)                 # Show 100 entries
        view_cache_contents(include_expired=True)      # Include expired entries

    Returns:
        JSON with cache contents and details
    """
    try:
        if not CACHE_ENABLED or cache is None:
            return json.dumps(
                {
                    "cache_enabled": False,
                    "message": "Cache is disabled. No cache contents to view.",
                },
                indent=2,
            )

        # Get cache contents
        contents = cache.view_cache_contents(
            limit=limit, include_expired=include_expired
        )

        logger.info(
            f"📋 Cache contents viewed - {contents['total_shown']['api_cache']} API + {contents['total_shown']['identity_cache']} identity entries"
        )

        return json.dumps(contents, indent=2)

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=f"Error viewing cache contents: {str(e)}",
        )


@with_function_logging
@mcp.tool()
async def get_cache_efficiency() -> str:
    """
    Get detailed cache efficiency metrics and performance analysis.

    Provides comprehensive cache performance data including:
    - Hit rate percentage (how often cache is used vs API calls)
    - Cache utilization (percentage of cached entries being reused)
    - Most and least accessed endpoints
    - Storage usage (database size)
    - Performance recommendations

    Metrics explained:
    - Hit Rate: Percentage of requests served from cache (higher is better)
      - >80% = Excellent
      - 50-80% = Good
      - <50% = May need optimization
    - Utilization: Percentage of cache entries that are being accessed
      - High utilization = Cache is effective
      - Low utilization = Caching data that isn't needed

    Use this to:
    - Evaluate cache performance
    - Identify optimization opportunities
    - Understand access patterns
    - Tune cache TTL settings

    Returns:
        JSON with detailed efficiency metrics and recommendations
    """
    try:
        if not CACHE_ENABLED or cache is None:
            return json.dumps(
                {
                    "cache_enabled": False,
                    "message": "Cache is disabled. No efficiency metrics available.",
                },
                indent=2,
            )

        # Get efficiency metrics
        efficiency = cache.get_cache_efficiency()

        logger.info(
            f"📊 Cache efficiency: {efficiency['overall_efficiency']['combined_hit_rate_percent']:.1f}% hit rate"
        )

        return json.dumps(efficiency, indent=2)

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=f"Error calculating cache efficiency: {str(e)}",
        )


async def _prepare_graphql_request(
    impersonate_user: str, graphql_version: str = None, bearer_token: str = None
):
    """
    Prepare common GraphQL request components (URL, headers, token).

    NOTE: OAuth token acquisition has been migrated to oauth_mcp_server.
    This function now requires bearer_token to be passed as a parameter.

    Args:
        impersonate_user: User to impersonate in the request
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

    # Get base URL using helper function (no parameter needed, will read from env)
    omada_base_url = _get_omada_base_url()

    # Get GraphQL endpoint version from parameter, environment, or default to 3.0
    if not graphql_version:
        graphql_version = os.getenv("GRAPHQL_ENDPOINT_VERSION", "3.0")
    graphql_url = f"{omada_base_url}/api/Domain/{graphql_version}"

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "impersonate_user": impersonate_user,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    return graphql_url, headers, token


def _extract_user_identity_from_token(bearer_token: str) -> str:
    """
    Extract user identity from JWT bearer token for cache keying.

    This ensures cache entries are user-specific, preventing users from
    accessing each other's cached data.

    Args:
        bearer_token: JWT bearer token

    Returns:
        User identity string (email, sub claim, or token hash as fallback)
    """
    try:
        # Strip "Bearer " prefix if present
        token = bearer_token.replace("Bearer ", "").replace("bearer ", "").strip()

        # Decode JWT without verification (we only need the payload for cache keying)
        # Format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            # Not a valid JWT, fallback to token hash
            logger.warning(
                "Bearer token is not a valid JWT format, using token hash for cache key"
            )
            return hashlib.sha256(token.encode()).hexdigest()[:16]

        # Decode payload (base64url)
        payload_encoded = parts[1]
        # Add padding if needed
        padding = 4 - (len(payload_encoded) % 4)
        if padding != 4:
            payload_encoded += "=" * padding

        payload_decoded = json.loads(
            base64.b64decode(payload_encoded.replace("-", "+").replace("_", "/"))
        )

        # Try to extract user identity from common JWT claims
        # Priority: email > upn > unique_name > preferred_username > sub > oid
        user_identity = (
            payload_decoded.get("email")
            or payload_decoded.get("upn")
            or payload_decoded.get("unique_name")
            or payload_decoded.get("preferred_username")
            or payload_decoded.get("sub")
            or payload_decoded.get("oid")
        )

        if user_identity:
            logger.debug(
                f"Extracted user identity from token for cache key: {user_identity}"
            )
            return str(user_identity)
        else:
            # No recognizable user claim, use token hash
            logger.warning(
                "Could not extract user identity from JWT claims, using token hash for cache key"
            )
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
            return token_hash

    except Exception as e:
        # If anything goes wrong, fallback to token hash
        logger.warning(
            f"Error extracting user identity from token: {e}, using token hash for cache key"
        )
        token = bearer_token.replace("Bearer ", "").replace("bearer ", "").strip()
        return hashlib.sha256(token.encode()).hexdigest()[:16]


async def _execute_graphql_request_cached(
    query: str,
    impersonate_user: str,
    variables: dict = None,
    graphql_version: str = None,
    bearer_token: str = None,
    use_cache: bool = True,
) -> dict:
    """
    Execute a GraphQL request with caching support.

    This is a wrapper around _execute_graphql_request that adds intelligent caching.

    Args:
        query: GraphQL query string
        impersonate_user: User to impersonate in the request
        variables: Optional GraphQL variables
        graphql_version: GraphQL API version to use
        bearer_token: Bearer token for authentication
        use_cache: Whether to use cache (default: True)

    Returns:
        dict: Parsed response with cache metadata
    """
    # Check if this is a mutation (write operation)
    is_mutation = "mutation" in query.lower()

    # Determine if we should use cache
    should_use_cache = (
        CACHE_ENABLED and cache is not None and use_cache and not is_mutation
    )

    # Extract user identity from bearer token for user-specific caching
    # This prevents users from accessing each other's cached data
    user_identity = (
        _extract_user_identity_from_token(bearer_token) if bearer_token else "anonymous"
    )

    # Create cache key parameters - INCLUDES USER IDENTITY for security
    cache_params = {
        "query": query,
        "impersonate_user": impersonate_user,
        "variables": variables or {},
        "version": graphql_version or "3.0",
        "user_identity": user_identity,  # CRITICAL: Ensures cache is user-specific
    }

    endpoint = "graphql"

    # Try to get from cache first
    if should_use_cache:
        cached_result = cache.get(endpoint, cache_params)
        if cached_result:
            # Cache HIT - return cached data (logging happens in cache.get())
            return cached_result

    # Cache MISS or caching disabled - execute the actual request
    result = await _execute_graphql_request(
        query, impersonate_user, variables, graphql_version, bearer_token
    )

    # Store successful results in cache
    if should_use_cache and result.get("success"):
        # Cache disabled - get_ttl_for_operation not available
        # ttl = get_ttl_for_operation(query, is_mutation)
        # if ttl > 0:
        #     cache.set(endpoint, cache_params, result, ttl)
        pass

    # Add cache metadata to result
    result["_cache_metadata"] = {
        "cached": False,
        "cache_enabled": CACHE_ENABLED,
        "cache_used": should_use_cache,
    }

    return result


@with_function_logging
async def _execute_graphql_request(
    query: str,
    impersonate_user: str,
    variables: dict = None,
    graphql_version: str = None,
    bearer_token: str = None,
) -> dict:
    """
    Execute a GraphQL request with common setup and error handling.

    Args:
        query: GraphQL query string
        impersonate_user: User to impersonate in the request
        variables: Optional GraphQL variables
        graphql_version: GraphQL API version to use
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Returns:
        dict: Parsed response or error information
    """
    try:
        # Setup
        graphql_url, headers, token = await _prepare_graphql_request(
            impersonate_user, graphql_version, bearer_token
        )

        # Build payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(
            f"GraphQL Request to {graphql_url} with impersonation of {impersonate_user}"
        )

        # Log the payload in a readable format without escaped newlines
        logger.debug("Request JSON Payload (BEFORE web service POST):")
        logger.debug(f"Query:\n{query}")
        if variables:
            logger.debug(f"Variables: {json.dumps(variables, indent=2)}")

        # Execute request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                graphql_url, json=payload, headers=headers, timeout=30.0
            )

            # Capture raw HTTP details for debugging
            raw_request_body = json.dumps(payload, indent=2)
            raw_response_body = response.text
            response_json = json.dumps(
                (
                    response.json()
                    if response.status_code == 200
                    else {"error": raw_response_body}
                ),
                indent=2,
            )
            logger.debug(
                f"GraphQL Response (status {response.status_code}): {response_json}"
            )

            # Build common response fields
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "endpoint": graphql_url,
                "raw_request_body": raw_request_body,
                "raw_response_body": raw_response_body,
                "request_headers": dict(headers),
            }

            # Add status-specific fields
            if response.status_code == 200:
                result["data"] = response.json()
            else:
                result["error"] = response.text

            return result

    except Exception as e:
        return {"success": False, "error": str(e), "error_type": type(e).__name__}


@with_function_logging
@mcp.tool()
async def get_access_requests(
    impersonate_user: str,
    bearer_token: str,
    access_reference_key: str = None,
    access_reference_key_operator: str = "CONTAINS",
    beneficiary: str = None,
    beneficiary_operator: str = "CONTAINS",
    resource: str = None,
    resource_operator: str = "CONTAINS",
    requested_by: str = None,
    requested_by_operator: str = "CONTAINS",
    reason: str = None,
    reason_operator: str = "CONTAINS",
    search_string: str = None,
    search_string_operator: str = "CONTAINS",
    system: str = None,
    system_operator: str = "CONTAINS",
    valid_from: str = None,
    valid_from_operator: str = "LESS_THAN",
    valid_to: str = None,
    valid_to_operator: str = "LESS_THAN",
    requested_time: str = None,
    requested_time_operator: str = "LESS_THAN",
    summary_mode: bool = True,
    use_cache: bool = True,
) -> str:
    """Get access requests from Omada GraphQL API using user impersonation (requires Graph API v3.2+).

    All filters are optional and can be combined. Text filters support CONTAINS or EQUALS operators.
    Date filters support LESS_THAN or GREATER_THAN operators.

    Args:
        impersonate_user: Email address of the user to impersonate (e.g., user@domain.com)
        bearer_token: Bearer token for authentication
        access_reference_key: Filter by access reference key (not required for IS_EMPTY/IS_NOT_EMPTY)
        access_reference_key_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        beneficiary: Filter by beneficiary name (not required for IS_EMPTY/IS_NOT_EMPTY)
        beneficiary_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        resource: Filter by resource name (not required for IS_EMPTY/IS_NOT_EMPTY)
        resource_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        requested_by: Filter by who requested (not required for IS_EMPTY/IS_NOT_EMPTY)
        requested_by_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        reason: Filter by reason text (not required for IS_EMPTY/IS_NOT_EMPTY)
        reason_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        search_string: General search string across access requests (not required for IS_EMPTY/IS_NOT_EMPTY)
        search_string_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        system: Filter by system name (not required for IS_EMPTY/IS_NOT_EMPTY)
        system_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        valid_from: Filter by valid from date (ISO format, e.g. "2024-01-01")
        valid_from_operator: Operator for valid_from filter (LESS_THAN or GREATER_THAN, default: LESS_THAN)
        valid_to: Filter by valid to date (ISO format, e.g. "2024-12-31")
        valid_to_operator: Operator for valid_to filter (LESS_THAN or GREATER_THAN, default: LESS_THAN)
        requested_time: Filter by requested time (ISO format)
        requested_time_operator: Operator for requested_time filter (LESS_THAN or GREATER_THAN, default: LESS_THAN)
        summary_mode: If True (default), returns only key fields. If False, returns all fields.
        use_cache: Whether to use cache for this request (default: True)

    Returns:
        JSON string containing access requests data
    """
    try:
        # Build individual filter entries
        filter_parts = []
        active_filters = {}

        # Text filters (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY)
        text_filters = {
            "accessReferenceKey": (access_reference_key, access_reference_key_operator),
            "beneficiary": (beneficiary, beneficiary_operator),
            "resource": (resource, resource_operator),
            "requestedBy": (requested_by, requested_by_operator),
            "system": (system, system_operator),
            "searchString": (search_string, search_string_operator),
            "reason": (reason, reason_operator),
        }
        for field_name, (value, operator) in text_filters.items():
            if operator in ("IS_EMPTY", "IS_NOT_EMPTY"):
                filter_parts.append(
                    f'{field_name}: {{operator: {operator}}}'
                )
                active_filters[field_name] = operator
            elif value is not None:
                filter_parts.append(
                    f'{field_name}: {{filterValue: {json.dumps(value)}, operator: {operator}}}'
                )
                active_filters[field_name] = f"{operator} {value}"

        # Date-based filters (LESS_THAN or GREATER_THAN)
        date_filters = {
            "validFrom": (valid_from, valid_from_operator),
            "validTo": (valid_to, valid_to_operator),
            "requestedTime": (requested_time, requested_time_operator),
        }
        for field_name, (value, operator) in date_filters.items():
            if value is not None:
                filter_parts.append(
                    f'{field_name}: {{filterValue: {json.dumps(value)}, operator: {operator}}}'
                )
                active_filters[field_name] = f"{operator} {value}"

        # Build the full filter clause
        filter_clause = ""
        if filter_parts:
            filter_clause = f"(filters: {{{', '.join(filter_parts)}}})"

        logger.debug(
            f"Getting access requests for user: {impersonate_user}, filters: {active_filters if active_filters else 'none'}"
        )

        # Build GraphQL query with optional filter
        query = f"""query GetAccessRequests {{
  accessRequests{filter_clause} {{
    pages
    total
    data {{
      id
      validFrom
      validTo
      effectiveValidFrom
      effectiveValidTo
      reason
      accessReferenceKey
      resourceAssignmentId
      status {{
        accessApprovalStatusEnum
        approvalStatus
        provisioningStatus
        provisioningStatusText
        requestAssignmentState
        violationStatus
        violationStatusText
      }}
      resource {{
        name
        id
        description
        resourceType {{
          name
          id
        }}
        childResourceIds
      }}
      requestedBy {{
        lastName
        id
        firstName
        displayName
        userName
      }}
      beneficiary {{
        id
        identityId
        firstName
        lastName
        displayName
      }}
      childAssignments {{
        id
      }}
    }}
  }}
}}"""

        # Execute GraphQL request WITH CACHING (requires Graph API v3.2+)
        result = await _execute_graphql_request_cached(
            query, impersonate_user, bearer_token=bearer_token, use_cache=use_cache,
            graphql_version="3.2",
        )

        if result["success"]:
            data = result["data"]
            # Extract and format the response
            if "data" in data and "accessRequests" in data["data"]:
                access_requests_obj = data["data"]["accessRequests"]
                total = access_requests_obj.get("total", 0)
                pages = access_requests_obj.get("pages", 0)
                access_requests = access_requests_obj.get("data", [])

                # Apply summarization if requested
                response_data = access_requests
                if summary_mode:
                    response_data = _summarize_graphql_data(
                        access_requests, "AccessRequest"
                    )

                return build_success_response(
                    data={"access_requests": response_data},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    total_requests=total,
                    total_pages=pages,
                    requests_returned=len(response_data),
                    filters_applied=active_filters if active_filters else "none",
                    summary_mode=summary_mode,
                )
            else:
                return build_error_response(
                    error_type="DataError",
                    message="No access requests data found in response",
                    impersonated_user=impersonate_user,
                    raw_response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                message=f"GraphQL request failed with status {result.get('status_code', 'unknown')}",
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=f"Error getting access requests: {str(e)}",
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_access_requests_by_ids(
    impersonate_user: str,
    bearer_token: str,
    ids: str,
    use_cache: bool = True,
) -> str:
    """
    Look up one or more access requests by their ID(s) from Omada GraphQL API (requires Graph API v3.2+).

    Returns the full detail of specific access request(s) including status, resource, beneficiary,
    requester, child assignments, and violation information. Use this when you already have an
    access request ID and need the complete picture for that request.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"
        ids: The access request ID (GUID) to look up. This is the "id" field from get_access_requests results.
             Example: "c13713f1-cc1a-46fd-9195-93953c248696"
             PROMPT: "Please provide the access request ID (GUID)"

    Optional parameters:
        use_cache: Whether to use cache for this request (default: True)

    LLM INSTRUCTIONS - RESPONSE FIELD GUIDE:
        Top-level fields:
        - id: The access request GUID (matches the input)
        - validFrom / validTo: Requested validity period. validTo of "9999-12-31T00:00:00" means permanent/no expiry
        - effectiveValidFrom / effectiveValidTo: Actual effective dates (may differ due to timezone adjustments)
        - resourceAssignmentId: GUID linking to the underlying resource assignment
        - requestedTime: ISO 8601 timestamp of when the request was submitted
        - reason: The justification text provided by the requester
        - accessReferenceKey: Short reference code (e.g., "8UI9B4"). May be empty string.

        status object:
        - approvalStatus: Human-readable status (e.g., "Pending approval by Robert Scott")
        - accessApprovalStatusEnum: Enum status (e.g., "pending", "approved", "rejected")
        - requestAssignmentState: State of the assignment (e.g., "pending", "active")
        - provisioningStatus / provisioningStatusText: Provisioning state (e.g., "notSet" when not yet provisioned)
        - violationStatus / violationStatusText: Violation state (e.g., "NO_VIOLATION")

        resource object:
        - name: Resource name (e.g., "Archive Documents")
        - description: What the resource provides (e.g., "Provides the user with the ability to Archive documents")
        - system.name: Target system (e.g., "Document Management")
        - riskLevel.name: Risk classification (e.g., "Low")
        - resourceType.name: Type of resource (e.g., "Application Role")
        - resourceCategory.name: Category (e.g., "Role")
        - resourceFolder.name: Organizational folder grouping
        - maxValidity: Maximum validity in days (0 means unlimited)
        - accountTypes[].name: Account types (e.g., "Personal")
        - childResourceIds: GUIDs of child resources that are part of this resource

        requestedBy object:
        - displayName: Full name of who submitted the request (e.g., "Hanna Ulrich")
        - userName: Login username (e.g., "HANULR@54MV4C.ONMICROSOFT.COM")

        beneficiary object:
        - displayName: Full name of who the access is for
        - identityId: Short identity ID (e.g., "HANULR")
        - accounts[]: List of the beneficiary's accounts across systems, each with accountName and system.name

        childAssignments array:
        - These are child resource assignments created as a result of the parent request
        - Each has its own resource, identity, validity period, and compliance/violation info
        - violations[]: Array of violation objects with violationStatus and description
          (e.g., "DECISION_PENDING_NOT_ALLOWED" / "Copied from parent because it has been disabled")
        - reason[]: Array explaining why the child was created (reasonType "ChildResource" means
          it was auto-created from a parent resource's childResourceIds)
        - complianceStatus: Compliance state (e.g., "None")
        - disabled: Whether the child assignment is disabled (true/false)

    LLM INSTRUCTIONS - DISPLAY TO USER:
        When presenting access request details to the user, show:
        1. Resource Name (resource.name) and Description (resource.description)
        2. System Name (resource.system.name)
        3. Approval Status (status.approvalStatus) - the human-readable status
        4. Beneficiary (beneficiary.displayName)
        5. Requested By (requestedBy.displayName) and When (requestedTime)
        6. Reason (reason)
        7. Valid From/To (validFrom / validTo)
        8. Risk Level (resource.riskLevel.name)
        9. Child Assignments - if any exist, summarize their resource names, violation status, and disabled state

    LLM INSTRUCTIONS - TECHNICAL IDs (DO NOT DISPLAY, STORE INTERNALLY):
        Do NOT display these to the user, but store them for downstream operations:
        - id, resourceAssignmentId
        - All nested .id fields (resource.id, system.id, requestedBy.id, beneficiary.id, etc.)
        - childAssignments[].id, childAssignments[].reason[].causeObjectKey

    Returns:
        JSON response with full access request details, or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_access_requests_by_ids(impersonate_user={impersonate_user}, ids={ids})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            ids=ids,
        )
        if error:
            return error

        # Build GraphQL query
        query = f"""query accessRequestsByIds {{
  accessRequestsByIds(ids: {json.dumps(ids)}) {{
    id
    validTo
    validFrom
    resourceAssignmentId
    status {{
      violationStatusText
      violationStatus
      requestAssignmentState
      provisioningStatusText
      provisioningStatus
      approvalStatus
      accessApprovalStatusEnum
    }}
    resource {{
      system {{
        name
        id
      }}
      riskLevel {{
        name
      }}
      resourceFolder {{
        name
        id
      }}
      resourceType {{
        name
        id
      }}
      resourceCategory {{
        name
        id
      }}
      name
      maxValidity
      id
      description
      childResourceIds
      accountTypes {{
        id
        name
      }}
    }}
    requestedTime
    requestedBy {{
      displayName
      firstName
      id
      lastName
      userName
    }}
    reason
    effectiveValidTo
    effectiveValidFrom
    childAssignments {{
      violations {{
        violationStatus
        description
      }}
      validTo
      validFrom
      resource {{
        id
        name
        system {{
          name
          id
        }}
      }}
      reason {{
        causeObjectKey
        description
        reasonType
      }}
      id
      identity {{
        createTime
        id
        identityId
        lastName
        displayName
        firstName
      }}
      complianceStatus
      disabled
    }}
    beneficiary {{
      lastName
      identityId
      id
      firstName
      displayName
      accounts {{
        id
        system {{
          id
          name
        }}
        accountName
      }}
    }}
    accessReferenceKey
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract access requests from the GraphQL response
            if "data" in data and "accessRequestsByIds" in data["data"]:
                access_requests = data["data"]["accessRequestsByIds"]

                return build_success_response(
                    data={"access_requests": access_requests},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    ids=ids,
                    requests_returned=len(access_requests) if isinstance(access_requests, list) else 1,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No access request found for the provided ID(s)",
                    impersonated_user=impersonate_user,
                    ids=ids,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                ids=ids,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
            ids=ids if "ids" in locals() else "N/A",
        )


@with_function_logging
@mcp.tool()
async def create_access_request(
    impersonate_user: str,
    bearer_token: str,
    reason: str,
    context: str,
    resources: str,
    valid_from: str = None,
    valid_to: str = None,
) -> str:
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

        context: Business context ID for the access request (cannot be empty)
                IMPORTANT WORKFLOW: When the user needs to provide a context:
                1. First, lookup the user's identity ID using their email with query_omada_identity
                2. Then call get_identity_contexts(identity_id, impersonate_user, bearer_token)
                   to retrieve available contexts for this user
                3. Display the available contexts to the user with their displayName and type
                   (e.g., "Personal", "Finance Department")
                4. Ask the user to select a context from the displayed list
                5. Use the corresponding context "id" (GUID) value as the context parameter

                EXAMPLE:
                "I found these contexts for you:
                 1. Personal (PERSONAL)
                 2. Finance Department (ORGANIZATIONAL)

                 Which context would you like to use for this access request?"

                NOTE: The context parameter expects the internal GUID id, not the displayName.
                      You must call get_identity_contexts first to get valid context IDs.

        resources: Resources to request access for (JSON object format, cannot be empty)
                  WORKFLOW: When the user needs to provide resources:
                  1. Call get_resources_for_beneficiary(identity_id, impersonate_user, bearer_token)
                     to get available resources the user can request
                  2. Display the resources with their names and systems
                  3. Ask the user to select a resource
                  4. Use the resource "id" (GUID) in JSON format: {"id": "resource-guid"}

                  PROMPT: "Please provide the resource in JSON object format like: {\"id\": \"resource-id\"}"

    Optional parameters:
        valid_from: Optional valid from date/time (ISO format)
        valid_to: Optional valid to date/time (ISO format)
        bearer_token: Optional bearer token to use instead of acquiring a new one

    Logging:
        Log level controlled by LOG_LEVEL_create_access_request in .env file
        Falls back to global LOG_LEVEL if not set

    Returns:
        JSON string containing the created access request ID or error information
    """
    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            reason=reason,
            context=context,
            resources=resources,
        )
        if error:
            return error

        # Get identity ID from the impersonate_user email
        logger.debug(f"Looking up identity ID for email: {impersonate_user}")
        identity_result = await query_omada_identity(
            field_filters=[
                {"field": "EMAIL", "value": impersonate_user, "operator": "eq"}
            ],
            select_fields="UId",
            top=1,
            bearer_token=bearer_token,
        )

        # Parse the identity lookup result
        try:
            identity_data = json.loads(identity_result)
            if identity_data.get("status") != "success" or not identity_data.get(
                "data", {}
            ).get("value"):
                return build_error_response(
                    error_type="IdentityLookupError",
                    message=f"Could not find identity for email: {impersonate_user}",
                    lookup_result=identity_data,
                )

            identity_entity = identity_data["data"]["value"][0]
            identity_id = str(identity_entity.get("UId"))

            if not identity_id:
                return build_error_response(
                    error_type="IdentityLookupError",
                    message=f"Identity found but no ID available for email: {impersonate_user}",
                    identity_data=identity_entity,
                )

            logger.debug(f"Found identity ID: {identity_id} for {impersonate_user}")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return build_error_response(
                error_type="IdentityLookupParseError",
                message=f"Failed to parse identity lookup result: {str(e)}",
                raw_result=identity_result,
            )

        # Build the GraphQL mutation with template variables filled in
        valid_from_clause = f'validFrom: "{valid_from}",' if valid_from else ""
        valid_to_clause = f'validTo: "{valid_to}",' if valid_to else ""
        context_clause = f'context: "{context}",'

        # Convert resources from JSON format to GraphQL syntax
        # JSON: {"id": "123"} -> GraphQL: {id: "123"}
        try:
            resources_graphql = json_to_graphql_syntax(resources)
            logger.debug(
                f"Converted resources from JSON to GraphQL syntax: {resources} -> {resources_graphql}"
            )
        except ValueError as e:
            return build_error_response(
                error_type="ResourcesFormatError",
                message=f"Invalid resources format: {str(e)}. Expected JSON object format like: {{'id': 'resource-id'}}",
                provided_resources=resources,
            )

        mutation = f"""mutation CreateAccessRequest {{
    createAccessRequest(accessRequest: {{
        reason: "{reason}",
        {valid_from_clause}
        {valid_to_clause}
        {context_clause}
        identities: {{id: "{identity_id}"}},
        resources: {resources_graphql}
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
            graphql_version="1.1",
            bearer_token=bearer_token,
        )

        if result["success"]:
            data = result["data"]

            # Debug: Print the actual response structure
            logger.debug(
                f"GraphQL Response Data Structure: {json.dumps(data, indent=2)}"
            )

            # Check if mutation was successful and extract the created access request ID
            if "data" in data and "createAccessRequest" in data["data"]:
                create_request_response = data["data"]["createAccessRequest"]
                logger.debug(
                    f"CreateAccessRequest Response: {json.dumps(create_request_response, indent=2)}"
                )

                # Handle both single object and array responses
                if isinstance(create_request_response, list):
                    if len(create_request_response) > 0:
                        access_request_data = create_request_response[0]
                    else:
                        return build_error_response(
                            error_type="EmptyResponse",
                            message="Empty response from createAccessRequest",
                            impersonated_user=impersonate_user,
                            raw_response=data,
                            http_debug={
                                "raw_request_body": result.get("raw_request_body"),
                                "raw_response_body": result.get("raw_response_body"),
                                "request_headers": result.get("request_headers"),
                            },
                        )
                else:
                    access_request_data = create_request_response

                access_request_id = access_request_data.get("id")

                return build_success_response(
                    data={
                        "access_request_details": {
                            "id": access_request_id,
                            "status": access_request_data.get("status"),
                            "resource": access_request_data.get("resource"),
                            "validFrom": access_request_data.get("validFrom"),
                            "validTo": access_request_data.get("validTo"),
                        },
                        "request_details": {
                            "reason": reason,
                            "identity_id": identity_id,
                            "identity_email": impersonate_user,
                            "resources": resources,
                            "valid_from": valid_from,
                            "valid_to": valid_to,
                            "context": context,
                        },
                        "http_debug": {
                            "raw_request_body": result.get("raw_request_body"),
                            "raw_response_body": result.get("raw_response_body"),
                            "request_headers": result.get("request_headers"),
                        },
                    },
                    endpoint=result["endpoint"],
                    message="Access request created successfully",
                    impersonated_user=impersonate_user,
                    access_request_id=access_request_id,
                )
            elif "errors" in data:
                # Handle GraphQL errors
                # Log the error details for debugging
                logger.error(
                    f"GraphQL mutation returned errors: {json.dumps(data['errors'], indent=2)}"
                )
                logger.error(
                    f"Raw Request Body:\n{result.get('raw_request_body', 'N/A')}"
                )
                logger.error(
                    f"Raw Response Body:\n{result.get('raw_response_body', 'N/A')}"
                )

                return build_error_response(
                    error_type="GraphQLError",
                    message="GraphQL mutation failed",
                    impersonated_user=impersonate_user,
                    errors=data["errors"],
                    endpoint=result["endpoint"],
                    http_debug={
                        "raw_request_body": result.get("raw_request_body"),
                        "raw_response_body": result.get("raw_response_body"),
                        "request_headers": result.get("request_headers"),
                    },
                )
            else:
                # Log the unexpected response for debugging
                logger.error(f"Unexpected response format from access request mutation")
                logger.error(
                    f"Raw Request Body:\n{result.get('raw_request_body', 'N/A')}"
                )
                logger.error(
                    f"Raw Response Body:\n{result.get('raw_response_body', 'N/A')}"
                )

                return build_error_response(
                    error_type="UnexpectedResponse",
                    message="Unexpected response format",
                    impersonated_user=impersonate_user,
                    raw_response=data,
                    http_debug={
                        "raw_request_body": result.get("raw_request_body"),
                        "raw_response_body": result.get("raw_response_body"),
                        "request_headers": result.get("request_headers"),
                    },
                )
        else:
            # Handle HTTP request failure using helper
            # Log the error details for debugging
            logger.error(
                f"Access request creation failed with status {result.get('status_code', 'unknown')}"
            )
            logger.error(f"Raw Request Body:\n{result.get('raw_request_body', 'N/A')}")
            logger.error(
                f"Raw Response Body:\n{result.get('raw_response_body', 'N/A')}"
            )

            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                message=f"GraphQL request failed with status {result.get('status_code', 'unknown')}",
                impersonated_user=impersonate_user,
                http_debug={
                    "raw_request_body": result.get("raw_request_body"),
                    "raw_response_body": result.get("raw_response_body"),
                    "request_headers": result.get("request_headers"),
                },
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=f"Error creating access request: {str(e)}",
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_resources_for_beneficiary(
    identity_id: str,
    impersonate_user: str,
    bearer_token: str,
    system_id: str = None,
    context_id: str = None,
    resource_name: str = None,
) -> str:
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

    IMPORTANT: This function requires 3 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        identity_id: The identity UId (32-character UUID, NOT the integer Id field!)
                    Example: "e3e869c4-369a-476e-a969-d57059d0b1e4" (CORRECT)
                    NOT: 1006715 (WRONG - this is the Id field, not UId)
                    PROMPT: "Please provide the identity UId (32-character UUID from the UId field, not the Id field)"
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional parameters:
        system_id: System ID to filter resources by (e.g., "1c2768e9-86fd-43fd-9e0d-5c8fee21b59b")
        context_id: Context ID to filter resources by (e.g., "6dd03400-ddb5-4cc4-bfff-490d94b195a9")
        resource_name: Resource name to filter by (string, partial match supported)
                      Example: "Sales" will match "Sales Team Access", "Sales Reports", etc.

    Returns:
        JSON response with resources data or error message
    """
    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            identity_id=identity_id, impersonate_user=impersonate_user
        )
        if error:
            return error

        # Validate that identity_id is a UUID (32 characters), not an integer Id
        if identity_id.strip().isdigit():
            return build_error_response(
                error_type="ValidationError",
                message=f"Invalid identity_id: '{identity_id}' appears to be an integer Id field, but this function requires the UId field (32-character UUID). "
                f"When you query an Identity, you get both 'Id' (integer like 1006715) and 'UId' (UUID like 'e3e869c4-369a-476e-a969-d57059d0b1e4'). "
                f"You MUST use the UId field, not the Id field.",
                hint="Query the identity first, then extract the 'UId' field (not 'Id') from the response",
            )

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

        # Execute GraphQL request with caching support
        result = await _execute_graphql_request_cached(
            query, impersonate_user, bearer_token=bearer_token, use_cache=True
        )

        if result["success"]:
            data = result["data"]
            # Extract resources from the GraphQL response
            if "data" in data and "accessRequestComponents" in data["data"]:
                access_request_components = data["data"]["accessRequestComponents"]
                resources = access_request_components.get("resources", {}).get(
                    "data", []
                )

                return build_success_response(
                    data=resources,
                    endpoint=result["endpoint"],
                    beneficiary_id=identity_id,
                    impersonated_user=impersonate_user,
                    system_id=system_id,
                    context_id=context_id,
                    resources_count=len(resources),
                    resources=resources,
                )
            else:
                return build_error_response(
                    error_type="NoResourcesFound",
                    message="No resources found in response",
                    beneficiary_id=identity_id,
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                beneficiary_id=identity_id,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            beneficiary_id=identity_id,
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_requestable_resources(
    identity_id: str,
    impersonate_user: str,
    bearer_token: str,
    system_id: str = None,
    context_id: str = None,
    resource_name: str = None,
) -> str:
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
        bearer_token=bearer_token,
    )


@with_function_logging
@mcp.tool()
async def get_identities_for_beneficiary(
    impersonate_user: str, bearer_token: str, page: int = None, rows: int = None
) -> str:
    """
    Get a list of identities available for access requests using Omada GraphQL API.

    USE THIS FUNCTION when user asks to:
    - "list identities for access request"
    - "show identities I can request for"
    - "get beneficiary identities"
    - "list identities available for access requests"

    This function queries the accessRequestComponents.identities endpoint to get identities
    that can be used as beneficiaries in access requests.

    IMPORTANT: This function requires 2 mandatory parameters.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional parameters:
        page: Page number for pagination (e.g., 1, 2, 3...)
        rows: Number of rows per page (e.g., 10, 20, 50...)

    Returns:
        JSON response with identities data including pagination metadata or error message
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_identities_for_beneficiary(impersonate_user={impersonate_user}, page={page}, rows={rows})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(impersonate_user=impersonate_user)
        if error:
            return error

        # Build pagination clause using helper
        pagination_clause = build_pagination_clause(page=page, rows=rows)

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

        # Execute GraphQL request with caching support
        result = await _execute_graphql_request_cached(
            query, impersonate_user, bearer_token=bearer_token, use_cache=True
        )

        if result["success"]:
            data = result["data"]
            # Extract identities from the GraphQL response
            if "data" in data and "accessRequestComponents" in data["data"]:
                access_request_components = data["data"]["accessRequestComponents"]
                identities_obj = access_request_components.get("identities", {})
                identities = identities_obj.get("data", [])
                total = identities_obj.get("total", len(identities))
                pages = identities_obj.get("pages", 1)

                return build_success_response(
                    data=identities,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    pagination={
                        "current_page": page,
                        "rows_per_page": rows,
                        "total_identities": total,
                        "total_pages": pages,
                    },
                    identities_count=len(identities),
                    identities=identities,
                )
            else:
                return build_error_response(
                    error_type="NoIdentitiesFound",
                    message="No identities found in response",
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_calculated_assignments_detailed(
    impersonate_user: str,
    bearer_token: str,
    identity_ids: str = None,
    resource_type_name: str = None,
    resource_type_operator: str = "CONTAINS",
    compliance_status: str = None,
    compliance_status_operator: str = "CONTAINS",
    account_name: str = None,
    account_name_operator: str = "CONTAINS",
    system_name: str = None,
    system_name_operator: str = "CONTAINS",
    identity_name: str = None,
    identity_name_operator: str = "CONTAINS",
    resource_name: str = None,
    resource_name_operator: str = "CONTAINS",
    violations: str = None,
    violations_operator: str = "CONTAINS",
    valid_from: str = None,
    valid_from_operator: str = "LESS_THAN",
    valid_to: str = None,
    valid_to_operator: str = "LESS_THAN",
    category: str = None,
    category_operator: str = "EQUALS",
    disabled: bool = None,
    is_application_accounts_system_visible: bool = None,
    reason_type: str = None,
    resource_ids: str = None,
    system_id: str = None,
    sort_by: str = "RESOURCE_NAME",
    page: int = 1,
    rows: int = 50,
    use_cache: bool = True,
) -> str:
    """
    Get detailed calculated assignments with compliance and violation status using Omada GraphQL API (requires Graph API v3.2+).

    At least one filter must be specified for the query to work.

    *** CRITICAL RULE - NEVER USE identityName WITH IS_EMPTY ***
    When the user does NOT mention a specific identity or person, DO NOT pass the identityName
    parameter at all. Leave it out entirely. NEVER set identity_name_operator to "IS_EMPTY".
    IS_EMPTY does NOT mean "all identities" — it searches for records with broken/missing identity
    data, which returns wrong results. Simply omit identity_name and identity_name_operator.

    This rule applies to ALL prompts including "orphan accounts", "unlinked accounts",
    "unassigned accounts", "accounts with no owner". For orphan account queries, use the
    get_compliance_workbench_data tool instead — it returns per-system orphan account counts
    directly via the complianceStatus.orphaned field.

    CORRECT for "show orphan accounts":   Use get_compliance_workbench_data tool
    WRONG for "show orphan accounts":     This tool with identityName IS_EMPTY
    *** END CRITICAL RULE ***

    IMPORTANT LLM INSTRUCTIONS - When to Use This Tool:
        USE THIS TOOL (GraphQL) when the user asks for assignments with ANY of these patterns:

        System Name Queries:
        - "Get me all the assignments in system {X}" (e.g., "in system AD", "in Active Directory")
        - "Show assignments for {person} in system {X}"
        - "What assignments does {person} have in {system}?"
        - "List all {system} assignments for {person}"
        - "Get assignments filtered by system name"
        - Any query that filters by system_name parameter

        Account Name Queries:
        - "Show me assignments for account {NAME}" (e.g., "for account HANULR", "for account JohnDoe")
        - "Get assignments using account {NAME}"
        - "What assignments use account {NAME}?"
        - "List assignments for account name {NAME}"
        - "Show me what {account} has access to"
        - Any query that filters by account_name parameter

        DO NOT use OData query_calculated_assignments or query_omada_entity for these requests.
        This GraphQL tool has system_name and account_name filters that are more efficient and provide richer data.

        Example user requests that MUST use this tool:
        - "Get all assignments in system AD for Robert Wolf"
        - "Show me assignments in Active Directory system"
        - "What does John have in the SAP system?"
        - "Show me assignments for account HANULR"
        - "Get assignments using account JohnDoe"
        - "What does account ROBWOL have access to?"

    IMPORTANT: At least one filter parameter must be provided. If the user wants to filter
    by identity, prompt for the identity UId.

    CRITICAL - Identity ID Field Name:
        WRONG: Do NOT use the "IdentityID" field (e.g., "ROBWOL") - this is a user-readable identifier
        WRONG: Do NOT use the "Id" field (e.g., 1006715) - this is the integer database ID
        CORRECT: Use the "UId" field (e.g., "2c68e1df-1335-4e8c-8ef9-eff1d2005629") - this is the 32-character GUID

        When querying Identity data, you MUST:
        1. Query the Identity entity to get the user record
        2. Extract the "UId" field (NOT "Id" or "IdentityID") from the result
        3. Use that UId value as the identity_ids parameter

        Example workflow:
        - Query: query_omada_identity with EMAIL filter returns {"UId": "2c68e1df-...", "Id": 1006715, "IdentityID": "ROBWOL"}
        - Use UId: "2c68e1df-..." as identity_ids parameter (32 character GUID)
        - DO NOT use Id: 1006715 (this will fail!)
        - DO NOT use IdentityID: "ROBWOL" (this will fail!)

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: OAuth2 bearer token for authentication (required for API access)
                     PROMPT: "Please provide a valid bearer token"

    Optional filter parameters (at least one must be specified):
        identity_ids: One or more identity UIds (32-character GUIDs from the "UId" field)
                     Can be a single UId or multiple UIds separated by commas
                     Example: "2c68e1df-1335-4e8c-8ef9-eff1d2005629"
        resource_type_name: Filter by resource type name (e.g., "Active Directory - Security Group")
        resource_type_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        compliance_status: Filter by compliance status (e.g., "NOT APPROVED", "APPROVED")
        compliance_status_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        account_name: Filter by account name (e.g., "HANULR")
        account_name_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        system_name: Filter by system name (e.g., "AD")
        system_name_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        identity_name: Filter by identity name (e.g., "ROBERT WOLF")
        identity_name_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        resource_name: Filter by resource name (e.g., "VPN Access")
        resource_name_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        violations: Filter by violation text
        violations_operator: Operator (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY; default: CONTAINS)
        valid_from: Filter by valid from date (ISO format, e.g. "2024-01-01")
        valid_from_operator: Operator (LESS_THAN or GREATER_THAN; default: LESS_THAN)
        valid_to: Filter by valid to date (ISO format, e.g. "2024-12-31")
        valid_to_operator: Operator (LESS_THAN or GREATER_THAN; default: LESS_THAN)
        category: Filter by assignment category (e.g., "ACCOUNT_ASSIGNMENTS")
        category_operator: Operator (EQUALS or CONTAINS; default: EQUALS)
        disabled: Filter by disabled status (true or false)
        is_application_accounts_system_visible: Filter by application accounts system visibility (true or false)
        reason_type: Filter by reason type (e.g., "DIRECT")
        resource_ids: Filter by resource ID(s) (GUID)
        system_id: Filter by system ID (GUID)

    Other optional parameters:
        sort_by: Field to sort results by (default: "RESOURCE_NAME")
                Valid values: "RESOURCE_NAME", "IDENTITY_NAME", "ACCOUNT_NAME", "RESOURCE_TYPE",
                             "COMPLIANCE_STATUS", "SYSTEM_NAME", "VALID_FROM", "VALID_TO",
                             "DISABLED", "VIOLATION_STATUS"
        page: Page number to retrieve (default: 1, minimum: 1)
        rows: Number of rows per page (default: 50, minimum: 1, maximum: 1000)

    Returns:
        JSON response with detailed assignments including:
        - total: Total number of assignments matching filters
        - current_page: The page number returned
        - rows_per_page: Number of rows per page
        - assignments_returned: Number of assignments in current page
        - data: Array of assignment objects for current page

    Schema Reference:
        For Identity field definitions: schema://omada/identity
        For Resource field definitions: schema://omada/resource
        Query schema://omada/entities to see all available schemas.
    """
    # WORKAROUND: Manually set logger level since decorator isn't working for this function
    old_level = logger.level
    old_handler_levels = [(handler, handler.level) for handler in logger.handlers]

    func_log_level = os.getenv(
        "LOG_LEVEL_get_calculated_assignments_detailed", LOG_LEVEL
    ).upper()
    new_level = getattr(logging, func_log_level, logging.INFO)
    logger.setLevel(new_level)
    for handler in logger.handlers:
        handler.setLevel(new_level)

    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_calculated_assignments_detailed(identity_ids={identity_ids}, impersonate_user={impersonate_user}, resource_type_name={resource_type_name}, compliance_status={compliance_status}, account_name={account_name}, system_name={system_name}, identity_name={identity_name}, page={page}, rows={rows})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            bearer_token=bearer_token,
        )
        if error:
            return error

        # Validate that at least one filter is specified
        has_filter = any([
            identity_ids, resource_type_name, compliance_status, account_name,
            system_name, identity_name, resource_name, violations, valid_from,
            valid_to, category, disabled is not None,
            is_application_accounts_system_visible is not None, reason_type,
            resource_ids, system_id,
        ])
        if not has_filter:
            return build_error_response(
                error_type="ValidationError",
                message="At least one filter parameter must be specified for calculatedAssignments query.",
                impersonated_user=impersonate_user,
            )

        # Validate pagination parameters
        if page < 1:
            return build_error_response(
                error_type="InvalidPaginationParameter",
                message=f"Invalid page number: {page}. Page must be >= 1.",
                impersonated_user=impersonate_user,
            )

        if rows < 1 or rows > 1000:
            return build_error_response(
                error_type="InvalidPaginationParameter",
                message=f"Invalid rows per page: {rows}. Rows must be between 1 and 1000.",
                impersonated_user=impersonate_user,
            )

        # Build the filters object dynamically based on provided parameters
        filters = []

        # Identity IDs filter (optional in v3.2)
        if identity_ids:
            filters.append(f'multipleIdentityIds: {json.dumps(identity_ids)}')

        # Text filters with operators (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY)
        text_filters = {
            "resourceTypeName": (resource_type_name, resource_type_operator),
            "complianceStatus": (compliance_status, compliance_status_operator),
            "accountName": (account_name, account_name_operator),
            "systemName": (system_name, system_name_operator),
            "identityName": (identity_name, identity_name_operator),
            "resourceName": (resource_name, resource_name_operator),
            "violations": (violations, violations_operator),
        }
        for field_name, (value, operator) in text_filters.items():
            if operator in ("IS_EMPTY", "IS_NOT_EMPTY"):
                filters.append(f'{field_name}: {{operator: {operator}}}')
            elif value is not None and str(value).strip():
                filters.append(
                    f'{field_name}: {{filterValue: {json.dumps(value)}, operator: {operator}}}'
                )

        # Date filters (LESS_THAN or GREATER_THAN)
        date_filters = {
            "validFrom": (valid_from, valid_from_operator),
            "validTo": (valid_to, valid_to_operator),
        }
        for field_name, (value, operator) in date_filters.items():
            if value is not None:
                filters.append(
                    f'{field_name}: {{filterValue: {json.dumps(value)}, operator: {operator}}}'
                )

        # Category filter (typically EQUALS)
        if category is not None:
            filters.append(
                f'category: {{filterValue: {category}, operator: {category_operator}}}'
            )

        # Boolean filters
        if disabled is not None:
            filters.append(f'disabled: {str(disabled).lower()}')

        if is_application_accounts_system_visible is not None:
            filters.append(f'isApplicationAccountsSystemVisible: {str(is_application_accounts_system_visible).lower()}')

        # Simple value filters
        if reason_type is not None:
            filters.append(f'reasonType: {reason_type}')

        if resource_ids is not None:
            filters.append(f'resourceIds: {json.dumps(resource_ids)}')

        if system_id is not None:
            filters.append(f'systemId: {json.dumps(system_id)}')

        # Join filters
        filters_string = ", ".join(filters)

        # Validate sort_by parameter
        valid_sort_options = [
            "RESOURCE_NAME",
            "IDENTITY_NAME",
            "ACCOUNT_NAME",
            "RESOURCE_TYPE",
            "COMPLIANCE_STATUS",
            "SYSTEM_NAME",
            "VALID_FROM",
            "VALID_TO",
            "DISABLED",
            "VIOLATION_STATUS",
        ]
        if sort_by not in valid_sort_options:
            return build_error_response(
                error_type="InvalidSortOption",
                message=f"Invalid sort_by: {sort_by}. Valid values are: {', '.join(valid_sort_options)}",
                impersonated_user=impersonate_user,
            )

        # Build GraphQL query with the filters and pagination
        query = f"""query GetCalculatedAssignmentsDetailed {{
  calculatedAssignments(
    sorting: {{sortOrder: ASCENDING, sortBy: {sort_by}}}
    pagination: {{page: {page}, rows: {rows}}}
    filters: {{{filters_string}}}
  ) {{
    total
    data {{
      violations {{
        violationStatus
        description
      }}
      validTo
      validFrom
      resource {{
        system {{
          name
          id
        }}
        riskLevel {{
          name
        }}
        resourceType {{
          id
        }}
        resourceFolder {{
          name
          id
        }}
        resourceCategory {{
          name
        }}
        maxValidity
        id
        name
        description
        childResourceIds
        accountTypes {{
          id
          name
        }}
      }}
      reason {{
        description
        causeObjectKey
        reasonType
      }}
      identity {{
        lastName
        id
        firstName
        displayName
        identityId
      }}
      id
      disabled
      complianceStatus
      account {{
        accountName
        id
        accountType {{
          id
          name
        }}
        system {{
          id
          name
        }}
      }}
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 WITH CACHING
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract calculated assignments from the GraphQL response
            if "data" in data and "calculatedAssignments" in data["data"]:
                calculated_assignments = data["data"]["calculatedAssignments"]
                assignments_data = calculated_assignments.get("data", [])
                total = calculated_assignments.get("total", 0)

                return build_success_response(
                    data=assignments_data,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    total_assignments=total,
                    current_page=page,
                    rows_per_page=rows,
                    assignments_returned=len(assignments_data),
                )
            else:
                return build_error_response(
                    error_type="NoAssignmentsFound",
                    message="No calculated assignments found in response",
                    identity_ids=identity_ids,
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                identity_ids=identity_ids,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            identity_ids=identity_ids,
            impersonated_user=impersonate_user,
        )
    finally:
        # Restore logger levels (workaround for decorator not working)
        logger.setLevel(old_level)
        for handler, level in old_handler_levels:
            handler.setLevel(level)


@with_function_logging
@mcp.tool()
async def get_identity_contexts(
    identity_id: str, impersonate_user: str, bearer_token: str
) -> str:
    """
    Get contexts for a specific identity using Omada GraphQL API.

    IMPORTANT: This function requires 3 mandatory parameters. If any are missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        identity_id: The identity ID to get contexts for (e.g., "e3e869c4-369a-476e-a969-d57059d0b1e4")
                    PROMPT: "Please provide the identity ID"
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Returns:
        JSON response with contexts data including:
        - id: Internal GUID for the context (use this for subsequent GraphQL calls)
        - displayName: Human-readable name of the context
        - type: Context type

    IMPORTANT LLM INSTRUCTIONS - Context ID Handling:
        When presenting results to the user:
        1. DO NOT display the "id" field in your response to the user
        2. ONLY show "displayName" and "type" fields to the user
        3. INTERNALLY store/remember the "id" value for each context
        4. When the user selects a context by its displayName, USE the corresponding "id" value
           for any subsequent API calls that require a context_id parameter
        5. The "id" field is a technical GUID required by other GraphQL operations but not
           useful for end users to see

        Example user presentation:
        "Available contexts:
        - Personal (type: PERSONAL)
        - Finance Department (type: ORGANIZATIONAL)"

        But internally remember:
        - Personal: id="a1b2c3d4-..."
        - Finance Department: id="e5f6g7h8-..."
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_identity_contexts(identity_id={identity_id}, impersonate_user={impersonate_user})"
    )

    # Validate mandatory fields
    error = validate_required_fields(
        identity_id=identity_id, impersonate_user=impersonate_user
    )
    if error:
        return error

    try:
        logger.debug(
            f"get_identity_contexts called with identity_id={identity_id}, impersonate_user={impersonate_user}"
        )
        logger.debug(
            f"Validation passed, building GraphQL query for identity_id: {identity_id}"
        )

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

        # Execute GraphQL request with caching support
        result = await _execute_graphql_request_cached(
            query, impersonate_user, bearer_token=bearer_token, use_cache=True
        )

        if result["success"]:
            data = result["data"]
            # Extract contexts from the GraphQL response
            if "data" in data and "accessRequestComponents" in data["data"]:
                access_request_components = data["data"]["accessRequestComponents"]
                contexts = access_request_components.get("contexts", [])

                return build_success_response(
                    data=contexts,
                    endpoint=result["endpoint"],
                    identity_id=identity_id,
                    impersonated_user=impersonate_user,
                    contexts_count=len(contexts),
                    contexts=contexts,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No contexts found in response",
                    identity_id=identity_id,
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                identity_id=identity_id,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            identity_id=identity_id,
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_pending_approvals(
    impersonate_user: str,
    bearer_token: str,
    workflow_step: str = None,
    summary_mode: bool = True,
) -> str:
    """
    Get pending approval survey questions from Omada GraphQL API.

    IMPORTANT: This function requires 2 mandatory parameters. If missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional parameters:
        workflow_step: Filter by workflow step (one of: "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")
                      If not provided, returns all pending approvals
        summary_mode: If True (default), returns only key fields (workflowStep, workflowStepTitle, reason)
                     If False, returns all fields including surveyId and surveyObjectKey

    ⚠️ IMPORTANT FOR CLAUDE - DISPLAY TO USER:
    When presenting pending approvals to the user, you MUST ALWAYS include:
    - Resource Name (resourceAssignment.resource.name)
    - System Name (resourceAssignment.resource.system.name)
    - Workflow Step (workflowStep)
    - Reason/Justification (reason)

    These fields provide essential context for the user to understand what access
    is being requested and make informed approval decisions.

    Returns:
        JSON response with pending approval survey questions including resource and system details,
        or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_pending_approvals(impersonate_user={impersonate_user}, workflow_step={workflow_step}, summary_mode={summary_mode})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(impersonate_user=impersonate_user)
        if error:
            return error

        # Validate workflow_step if provided
        valid_workflow_steps = [
            "ManagerApproval",
            "ResourceOwnerApproval",
            "SystemOwnerApproval",
        ]
        if workflow_step and workflow_step not in valid_workflow_steps:
            return build_error_response(
                error_type="ValidationError",
                message=f"Invalid workflow_step '{workflow_step}'. Must be one of: {', '.join(valid_workflow_steps)}",
                impersonated_user=impersonate_user,
                workflow_step_filter=workflow_step,
            )

        # Build filter clause conditionally
        filter_clause = (
            f'(filters: {{workflowStep: {{filterValue: "{workflow_step}", operator: EQUALS}}}})'
            if workflow_step
            else ""
        )

        # Build GraphQL query with conditional filter
        query = f"""query myAccessRequestApprovalSurveyQuestions {{
  accessRequestApprovalSurveyQuestions{filter_clause} {{
    pages
    total
    data {{
      reason
      surveyId
      surveyObjectKey
      workflowStep
      history
      workflowStepTitle
      resourceAssignment {{
        resource {{
          id
          name
          system {{
            id
            name
          }}
          resourceType {{
            name
            id
          }}
        }}
      }}
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.0 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.0",
            bearer_token=bearer_token,
            use_cache=True,
        )

        if result["success"]:
            data = result["data"]
            # Extract approval questions from the GraphQL response
            if (
                "data" in data
                and "accessRequestApprovalSurveyQuestions" in data["data"]
            ):
                approval_questions = data["data"][
                    "accessRequestApprovalSurveyQuestions"
                ]
                questions_data = approval_questions.get("data", [])
                total = approval_questions.get("total", 0)
                pages = approval_questions.get("pages", 0)

                # Apply summarization if requested
                response_data = questions_data
                if summary_mode:
                    logger.debug(
                        f"Applying summarization to {len(questions_data)} pending approvals"
                    )
                    logger.debug(
                        f"Original data fields: {list(questions_data[0].keys()) if questions_data else []}"
                    )
                    response_data = _summarize_graphql_data(
                        questions_data, "PendingApproval"
                    )
                    logger.debug(
                        f"Summarized data fields: {list(response_data[0].keys()) if response_data else []}"
                    )

                return build_success_response(
                    data=response_data,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    workflow_step_filter=workflow_step if workflow_step else "none",
                    total_approvals=total,
                    pages=pages,
                    approvals_returned=len(response_data),
                    summary_mode=summary_mode,
                    approvals=response_data,
                )
            else:
                return build_error_response(
                    error_type="NoApprovalsFound",
                    message="No pending approvals found in response",
                    impersonated_user=impersonate_user,
                    workflow_step_filter=workflow_step if workflow_step else "none",
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                workflow_step_filter=workflow_step if workflow_step else "none",
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
            workflow_step_filter=workflow_step if workflow_step else "none",
        )


@with_function_logging
@mcp.tool()
async def get_access_request_approval_survey_questions(
    impersonate_user: str,
    bearer_token: str,
    account_type: str = None,
    account_type_operator: str = "CONTAINS",
    workflow_step: str = None,
    workflow_step_operator: str = "CONTAINS",
    valid_to: str = None,
    valid_to_operator: str = "LESS_THAN",
    resource: str = None,
    resource_operator: str = "CONTAINS",
    request_type: str = None,
    request_type_operator: str = "EQUALS",
    identity: str = None,
    identity_operator: str = "CONTAINS",
    sort_by: str = None,
    sort_order: str = "ASCENDING",
    second_sort_by: str = None,
    second_sort_order: str = "ASCENDING",
    summary_mode: bool = True,
    use_cache: bool = True,
) -> str:
    """
    Get pending approval survey questions from Omada GraphQL API (requires Graph API v3.2+).

    This is the v3.2 version with expanded filters, sorting, and a deeper field set compared
    to get_pending_approvals. Use this when you need advanced filtering or the full response data.

    IMPORTANT: This function requires 2 mandatory parameters. If missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional filter parameters (all combinable):
        account_type: Filter by account type
        account_type_operator: Operator (CONTAINS or EQUALS, default: CONTAINS)
        workflow_step: Filter by workflow step (e.g., "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")
        workflow_step_operator: Operator (CONTAINS or EQUALS, default: CONTAINS)
        valid_to: Filter by valid to date (ISO format, e.g. "2024-12-31")
        valid_to_operator: Operator (LESS_THAN or GREATER_THAN, default: LESS_THAN)
        resource: Filter by resource name
        resource_operator: Operator (CONTAINS or EQUALS, default: CONTAINS)
        request_type: Filter by request type (e.g., "REQUEST_ACCESS")
        request_type_operator: Operator (EQUALS or CONTAINS, default: EQUALS)
        identity: Filter by identity name
        identity_operator: Operator (CONTAINS or EQUALS, default: CONTAINS)
        sort_by: Primary sort field (e.g., IDENTITY, RESOURCE, WORKFLOW_STEP, VALID_TO, REQUEST_TYPE, ACCOUNT_TYPE)
        sort_order: Primary sort order (ASCENDING or DESCENDING, default: ASCENDING)
        second_sort_by: Secondary sort field (same options as sort_by)
        second_sort_order: Secondary sort order (ASCENDING or DESCENDING, default: ASCENDING)
        summary_mode: If True (default), returns only key fields. If False, returns all fields.
        use_cache: Whether to use cache for this request (default: True)

    LLM INSTRUCTIONS - FILTER TO RESPONSE FIELD MAPPING:
        The filters map to the following response attributes:
        - account_type  → resourceAssignment.resource.accountTypes[].name (e.g., "Personal")
        - workflow_step → workflowStepTitle (e.g., "Perform resource owner approval")
                          Common values: "Perform resource owner approval", "Perform manager approval",
                          "Perform system owner approval"
        - valid_to      → validTo (ISO 8601, e.g., "2026-01-08T23:00:00Z")
                          NOTE: A validTo of "9999-12-30T23:00:00Z" means permanent/no expiry
        - resource      → resourceAssignment.resource.name (e.g., "VPN Access - Full")
        - request_type  → requestType.name (display: "Request access", filter uses enum: "REQUEST_ACCESS")
        - identity      → resourceAssignment.identity.displayName (e.g., "Berry Black") or
                          resourceAssignment.identity.identityId (e.g., "BERBLA")

    LLM INSTRUCTIONS - DISPLAY TO USER:
        When presenting pending approvals to the user, you MUST ALWAYS include:
        1. Resource Name (resourceAssignment.resource.name) - what access is being requested
        2. System Name (resourceAssignment.resource.system.name) - which target system
        3. Workflow Step Title (workflowStepTitle) - current approval stage
        4. Reason/Justification (reason) - why access was requested
        5. Identity (resourceAssignment.identity.displayName) - who the request is for
        6. Risk Level (resourceAssignment.resource.riskLevel.name) - risk classification (e.g., "Low")
        7. Route Time (routeTime) - when the approval task was assigned to the current approver

        Additional context fields to present when relevant:
        - Resource Category (resourceAssignment.resource.resourceCategory.name) - e.g., "Permission"
        - Resource Folder (resourceAssignment.resource.resourceFolder.name) - organizational grouping
        - Account Type (resourceAssignment.resource.accountTypes[].name) - e.g., "Personal"
        - Valid From/To (resourceAssignment.validFrom / validTo) - access validity period
        - Access Reference Key (resourceAssignment.accessReferenceKey) - short reference code (e.g., "8UI9B4")
        - Context (context.displayName) - organizational context for the request
        - Identity Contexts (resourceAssignment.identity.contexts[]) - identity's org positions
          (types include: OrgUnit, Company, JOB_TITLES, DIVISION, C_SCREENINGOBJECT)

    LLM INSTRUCTIONS - TECHNICAL IDs (DO NOT DISPLAY, STORE INTERNALLY):
        The following fields are technical identifiers needed for downstream operations
        (e.g., make_approval_decision). Do NOT show these to the user, but store them internally:
        - surveyId: Required for make_approval_decision
        - surveyObjectKey: Required for make_approval_decision
        - resourceAssignment.id: Internal assignment GUID
        - All .id fields on nested objects (system.id, riskLevel.id, resourceType.id, etc.)

    LLM INSTRUCTIONS - HISTORY FIELD:
        The "history" field contains a human-readable audit trail of the approval workflow.
        It includes who submitted the request, when, the reason, and who the approval is assigned to.
        This is useful for understanding the full context of an approval but can be verbose.
        Only display if the user asks about the history or approval chain.

    Returns:
        JSON response with pending approval survey questions including resource and system details,
        or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_access_request_approval_survey_questions(impersonate_user={impersonate_user}, summary_mode={summary_mode})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(impersonate_user=impersonate_user)
        if error:
            return error

        # Build individual filter entries
        filter_parts = []
        active_filters = {}

        # Text-based filters (CONTAINS or EQUALS)
        text_filters = {
            "accountType": (account_type, account_type_operator),
            "workflowStep": (workflow_step, workflow_step_operator),
            "resource": (resource, resource_operator),
            "requestType": (request_type, request_type_operator),
            "identity": (identity, identity_operator),
        }
        for field_name, (value, operator) in text_filters.items():
            if value is not None:
                filter_parts.append(
                    f'{field_name}: {{filterValue: {json.dumps(value)}, operator: {operator}}}'
                )
                active_filters[field_name] = f"{operator} {value}"

        # Date-based filters (LESS_THAN or GREATER_THAN)
        if valid_to is not None:
            filter_parts.append(
                f'validTo: {{filterValue: {json.dumps(valid_to)}, operator: {valid_to_operator}}}'
            )
            active_filters["validTo"] = f"{valid_to_operator} {valid_to}"

        # Build the full filter clause
        filter_clause = ""
        if filter_parts:
            filter_clause = f"filters: {{{', '.join(filter_parts)}}}"

        # Build sorting clauses
        sorting_clause = ""
        if sort_by:
            sorting_clause = f"sorting: {{sortBy: {sort_by}, sortOrder: {sort_order}}}"

        second_sorting_clause = ""
        if second_sort_by:
            second_sorting_clause = f"secondSorting: {{sortBy: {second_sort_by}, sortOrder: {second_sort_order}}}"

        # Combine all arguments
        query_args_parts = [p for p in [filter_clause, sorting_clause, second_sorting_clause] if p]
        query_args = ""
        if query_args_parts:
            query_args = f"({', '.join(query_args_parts)})"

        logger.debug(
            f"Getting pending approvals (v2) for user: {impersonate_user}, filters: {active_filters if active_filters else 'none'}"
        )

        # Build GraphQL query with full v3.2 field set
        query = f"""query GetAccessRequestApprovalSurveyQuestions {{
  accessRequestApprovalSurveyQuestions{query_args} {{
    total
    pages
    data {{
      workflowStepTitle
      validTo
      surveyObjectKey
      surveyId
      routeTime
      resourceAssignment {{
        validTo
        validFrom
        resource {{
          system {{
            name
            id
          }}
          riskLevel {{
            name
            id
          }}
          resourceType {{
            id
          }}
          resourceFolder {{
            name
          }}
          resourceCategory {{
            name
          }}
          name
          maxValidity
          description
          createTime
          childResourceIds
          accountTypes {{
            id
            name
          }}
        }}
        identity {{
          lastName
          id
          firstName
          identityId
          displayName
          contexts {{
            id
            displayName
            type
            typeId
            createTime
          }}
          accounts {{
            accountName
            id
            system {{
              id
              name
              createTime
            }}
          }}
        }}
        id
        attributes {{
          attributeDisplayValues
          displayName
          id
          systemName
        }}
        accountType {{
          id
        }}
        accountName
        accessReferenceKey
      }}
      requestType {{
        name
        id
      }}
      reason
      history
      context {{
        id
        type
        displayName
      }}
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract approval questions from the GraphQL response
            if (
                "data" in data
                and "accessRequestApprovalSurveyQuestions" in data["data"]
            ):
                approval_questions = data["data"][
                    "accessRequestApprovalSurveyQuestions"
                ]
                questions_data = approval_questions.get("data", [])
                total = approval_questions.get("total", 0)
                pages = approval_questions.get("pages", 0)

                # Apply summarization if requested
                response_data = questions_data
                if summary_mode:
                    logger.debug(
                        f"Applying summarization to {len(questions_data)} pending approvals"
                    )
                    response_data = _summarize_graphql_data(
                        questions_data, "PendingApproval"
                    )

                return build_success_response(
                    data=response_data,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    filters_applied=active_filters if active_filters else "none",
                    total_approvals=total,
                    total_pages=pages,
                    approvals_returned=len(response_data),
                    summary_mode=summary_mode,
                )
            else:
                return build_error_response(
                    error_type="NoApprovalsFound",
                    message="No pending approvals found in response",
                    impersonated_user=impersonate_user,
                    filters_applied=active_filters if active_filters else "none",
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                filters_applied=active_filters if active_filters else "none",
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_access_request_approval_survey_question_by_id(
    impersonate_user: str,
    bearer_token: str,
    survey_id: str,
    survey_object_key: str,
    use_cache: bool = True,
) -> str:
    """
    Look up a single access request approval survey question by its surveyId and surveyObjectKey
    from Omada GraphQL API (requires Graph API v3.2+).

    Returns the full detail of a specific pending approval including the workflow step,
    resource assignment details, identity, request type, reason, history, and context.
    Use this when you have a specific approval's technical IDs and need the complete detail
    for that single approval.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"
        survey_id: The survey ID for the approval (GUID).
                  This comes from the surveyId field in get_pending_approvals or
                  GetAccessRequestApprovalSurveyQuestions results.
                  Example: "31cd9342-84db-4f71-92e1-a5c88aa103a9"
                  PROMPT: "Please provide the survey ID"
        survey_object_key: The survey object key for the approval (GUID).
                          This comes from the surveyObjectKey field in get_pending_approvals or
                          GetAccessRequestApprovalSurveyQuestions results.
                          Example: "2EC3860F-8263-4B90-A52A-130C0B9A0CA9"
                          PROMPT: "Please provide the survey object key"

    Optional parameters:
        use_cache: Whether to use cache for this request (default: True)

    LLM INSTRUCTIONS - RESPONSE FIELD GUIDE:
        Workflow fields:
        - workflowStepTitle: Human-readable step name (e.g., "Perform resource owner approval")
        - workflowStep: Internal step identifier (e.g., "ResourceOwnerApproval")
        - validTo: Expiry date for the requested access (ISO 8601)
        - routeTime: When this approval step was routed/assigned (ISO 8601)

        Technical IDs (returned for reference):
        - surveyId: The survey ID (matches input)
        - surveyObjectKey: The survey object key (matches input)

        resourceAssignment object:
        - accessReferenceKey: Short reference code (e.g., "8UI9B4")
        - accountName: Account name for the assignment
        - createTime: When the assignment was created
        - id: Assignment GUID
        - validFrom / validTo: Assignment validity period
        - resource: The resource being requested, including:
          - name: Resource name (e.g., "VPN Access - Full")
          - description: What the resource provides
          - maxValidity: Maximum validity in days (0 = unlimited)
          - system.name: Target system (e.g., "Active Directory corporate.com")
          - resourceType.name: Type (e.g., "Application Role")
          - resourceFolder.name: Organizational folder grouping
          - resourceCategory.name: Category (e.g., "Permission", "Role")
        - accountType: Account type (id and name, e.g., "Personal")
        - identity: The identity the resource is assigned to, including:
          - displayName, firstName, lastName: Name fields
          - identityId: Short identity ID (e.g., "BERBLA")
        - attributes[]: Additional attributes with displayName, attributeDisplayValues, systemName

        requestType object:
        - name: Type of request (e.g., "Request access")
        - id: Request type GUID

        Other fields:
        - reason: Justification text provided by the requester
        - history: Human-readable audit trail of the approval workflow (who submitted, when,
          the reason, and who the approval is assigned to). Can be verbose.
        - context: Organizational context (id, displayName, type)

    LLM INSTRUCTIONS - DISPLAY TO USER:
        When presenting the approval detail to the user, show:
        1. Workflow Step (workflowStepTitle) - current approval stage
        2. Resource Name (resourceAssignment.resource.name) and Description
        3. System Name (resourceAssignment.resource.system.name)
        4. Identity (resourceAssignment.identity.displayName) - who it's for
        5. Reason (reason) - justification
        6. Request Type (requestType.name)
        7. Valid From/To (resourceAssignment.validFrom / validTo)
        8. Route Time (routeTime) - when approval was assigned
        9. Context (context.displayName) - organizational context

    LLM INSTRUCTIONS - TECHNICAL IDs (DO NOT DISPLAY, STORE INTERNALLY):
        Do NOT display these to the user, but store them for downstream operations
        (e.g., make_approval_decision):
        - surveyId: Required for make_approval_decision
        - surveyObjectKey: Required for make_approval_decision
        - resourceAssignment.id
        - All nested .id fields (resource.id, system.id, identity.id, etc.)

    Returns:
        JSON response with the full approval survey question detail,
        or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_access_request_approval_survey_question_by_id(impersonate_user={impersonate_user}, survey_id={survey_id}, survey_object_key={survey_object_key})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            survey_id=survey_id,
            survey_object_key=survey_object_key,
        )
        if error:
            return error

        # Build GraphQL query
        query = f"""query accessRequestApprovalSurveyQuestionById {{
  accessRequestApprovalSurveyQuestionById(surveyId: {json.dumps(survey_id)}, surveyObjectKey: {json.dumps(survey_object_key)}) {{
    workflowStepTitle
    workflowStep
    validTo
    surveyId
    routeTime
    resourceAssignment {{
      accessReferenceKey
      accountName
      createTime
      id
      validFrom
      validTo
      resource {{
        name
        maxValidity
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
        resourceFolder {{
          name
          id
        }}
        resourceCategory {{
          name
        }}
      }}
      accountType {{
        id
        name
      }}
      identity {{
        identityId
        id
        firstName
        displayName
        lastName
      }}
      attributes {{
        attributeDisplayValues
        displayName
        id
        systemName
      }}
    }}
    surveyObjectKey
    reason
    history
    context {{
      id
      displayName
      type
    }}
    requestType {{
      name
      id
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract the approval detail from the GraphQL response
            if "data" in data and "accessRequestApprovalSurveyQuestionById" in data["data"]:
                approval_detail = data["data"]["accessRequestApprovalSurveyQuestionById"]

                return build_success_response(
                    data={"approval_detail": approval_detail},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    survey_id=survey_id,
                    survey_object_key=survey_object_key,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No approval survey question found for the provided surveyId and surveyObjectKey",
                    impersonated_user=impersonate_user,
                    survey_id=survey_id,
                    survey_object_key=survey_object_key,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                survey_id=survey_id,
                survey_object_key=survey_object_key,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
            survey_id=survey_id if "survey_id" in locals() else "N/A",
            survey_object_key=survey_object_key if "survey_object_key" in locals() else "N/A",
        )


@with_function_logging
@mcp.tool()
async def get_access_approval_workflow_steps_question_count(
    impersonate_user: str,
    bearer_token: str,
    workflow_step_name: str = None,
    use_cache: bool = True,
) -> str:
    """
    Get a count of pending approval questions per workflow step from Omada GraphQL API (requires Graph API v3.2+).

    Returns the number of pending approval questions (questionsCount) for each workflow step.
    This is useful for getting a quick overview of how many approvals are waiting at each stage
    of the approval workflow without fetching the full approval details.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional parameters:
        workflow_step_name: Filter to a specific workflow step name. If omitted, returns counts
                          for all workflow steps.
                          Known values: "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval"
        use_cache: Whether to use cache for this request (default: True)

    LLM INSTRUCTIONS - RESPONSE FIELD GUIDE:
        Returns an array of workflow step objects, each containing:
        - workflowStepTitle: Human-readable step name (e.g., "Perform resource owner approval")
        - workflowStep: Internal step identifier used for filtering in other tools
          (e.g., "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")
        - questionsCount: Number of pending approval questions at this workflow step (integer)
          A count of 0 means no approvals are waiting at that step.

    LLM INSTRUCTIONS - DISPLAY TO USER:
        Present the results as a summary table or list showing:
        1. Workflow Step Title (workflowStepTitle) - the human-readable name
        2. Pending Count (questionsCount) - how many approvals are waiting
        Highlight any steps with questionsCount > 0 as these have pending work.
        Example presentation:
        - Perform manager approval: 0 pending
        - Perform resource owner approval: 4 pending
        - Perform system owner approval: 0 pending

    LLM INSTRUCTIONS - RELATIONSHIP TO OTHER TOOLS:
        - The workflowStep values (e.g., "ResourceOwnerApproval") can be used as the
          workflow_step filter in get_pending_approvals to drill into the specific approvals.
        - This tool is a good starting point before calling get_pending_approvals, as it
          shows the user where approvals are waiting without fetching all the detail.

    Returns:
        JSON response with workflow step question counts, or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_access_approval_workflow_steps_question_count(impersonate_user={impersonate_user}, workflow_step_name={workflow_step_name})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(impersonate_user=impersonate_user)
        if error:
            return error

        # Build the optional filter parameter
        filter_param = ""
        if workflow_step_name is not None:
            filter_param = f"(workflowStepName: {json.dumps(workflow_step_name)})"

        # Build GraphQL query
        query = f"""query accessApprovalWorkflowStepsQuestionCount {{
  accessApprovalWorkflowStepsQuestionCount{filter_param} {{
    workflowStepTitle
    workflowStep
    questionsCount
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract workflow step counts from the GraphQL response
            if "data" in data and "accessApprovalWorkflowStepsQuestionCount" in data["data"]:
                step_counts = data["data"]["accessApprovalWorkflowStepsQuestionCount"]

                return build_success_response(
                    data={"workflow_step_counts": step_counts},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    workflow_step_filter=workflow_step_name if workflow_step_name else "none",
                    steps_returned=len(step_counts) if isinstance(step_counts, list) else 1,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No workflow step question counts found in response",
                    impersonated_user=impersonate_user,
                    workflow_step_filter=workflow_step_name if workflow_step_name else "none",
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                workflow_step_filter=workflow_step_name if workflow_step_name else "none",
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_approval_details(
    impersonate_user: str, bearer_token: str, workflow_step: str = None
) -> str:
    """
    Get FULL approval details including technical IDs (surveyId, surveyObjectKey) needed for making decisions.

    Use this function when you need to make an approval decision and need the technical IDs.
    This returns all fields including surveyId and surveyObjectKey which are required for make_approval_decision.

    IMPORTANT: This function requires 2 mandatory parameters.

    REQUIRED PARAMETERS:
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
        bearer_token: Bearer token for authentication (required for GraphQL API)

    Optional parameters:
        workflow_step: Filter by workflow step (one of: "ManagerApproval", "ResourceOwnerApproval", "SystemOwnerApproval")

    Returns:
        JSON response with FULL approval details including surveyId and surveyObjectKey
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_approval_details(impersonate_user={impersonate_user}, workflow_step={workflow_step})"
    )

    # Call get_pending_approvals with summary_mode=False to get all fields
    return await get_pending_approvals(
        impersonate_user=impersonate_user,
        bearer_token=bearer_token,
        workflow_step=workflow_step,
        summary_mode=False,  # Get full details including technical IDs
    )


@with_function_logging
@mcp.tool()
async def make_approval_decision(
    impersonate_user: str,
    survey_id: str,
    survey_object_key: str,
    decision: str,
    bearer_token: str,
) -> str:
    """
    Make an approval decision (APPROVE or REJECT) for an access request using Omada GraphQL API.

    ⚠️ CRITICAL SECURITY WARNING FOR CLAUDE ⚠️
    This function performs a PERMANENT approval/rejection that affects access control.
    You MUST get explicit human confirmation before calling this function.

    MANDATORY CONFIRMATION PROTOCOL:
    Before calling this function, you MUST:
    1. Display the complete request details to the user (requester, resource, reason, etc.)
    2. Ask explicitly: "Do you want to APPROVE, REJECT, or CANCEL this request?"
    3. Wait for the user's explicit response (APPROVE/REJECT/CANCEL)
    4. Only call this function after receiving APPROVE or REJECT from the user
    5. If user says CANCEL, do NOT call this function

    NEVER call this function without completing all steps above.
    The user must see the request details and explicitly type their decision.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        survey_id: The survey ID for the approval (e.g., "d67d8182-5d9e-466d-b9c2-d499a095e06a")
                  PROMPT: "Please provide the survey ID"
        survey_object_key: The survey object key for the approval (e.g., "40501018-04D0-4C67-A4BD-E698C109B60C")
                          PROMPT: "Please provide the survey object key"
        decision: The approval decision - must be either "APPROVE" or "REJECT"
                 PROMPT: "Please provide the decision (APPROVE or REJECT)"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Returns:
        JSON response with approval submission result or error message
    """
    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            survey_id=survey_id,
            survey_object_key=survey_object_key,
            decision=decision,
        )
        if error:
            return error

        # Validate decision value
        valid_decisions = ["APPROVE", "REJECT"]
        decision_upper = decision.strip().upper()
        if decision_upper not in valid_decisions:
            return build_error_response(
                error_type="ValidationError",
                message=f"Invalid decision '{decision}'. Must be one of: {', '.join(valid_decisions)}",
            )

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
            graphql_version="3.0",
            bearer_token=bearer_token,
        )

        if result["success"]:
            data = result["data"]
            # Extract submission result from the GraphQL response
            if "data" in data and "submitRequestQuestions" in data["data"]:
                submission_result = data["data"]["submitRequestQuestions"]
                questions_submitted = submission_result.get(
                    "questionsSuccessfullySubmitted", False
                )

                return build_success_response(
                    data={"questions_successfully_submitted": questions_submitted},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    survey_id=survey_id,
                    survey_object_key=survey_object_key,
                    decision=decision_upper,
                )
            elif "errors" in data:
                # Handle GraphQL errors
                return build_error_response(
                    error_type="GraphQLError",
                    message="GraphQL mutation failed",
                    impersonated_user=impersonate_user,
                    survey_id=survey_id,
                    survey_object_key=survey_object_key,
                    decision=decision_upper,
                    errors=data["errors"],
                    endpoint=result["endpoint"],
                )
            else:
                return build_error_response(
                    error_type="UnexpectedResponse",
                    message="Unexpected response format from submitRequestQuestions",
                    impersonated_user=impersonate_user,
                    survey_id=survey_id,
                    survey_object_key=survey_object_key,
                    decision=decision_upper,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                survey_id=survey_id,
                survey_object_key=survey_object_key,
                decision=decision_upper,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
            survey_id=survey_id if "survey_id" in locals() else "N/A",
            survey_object_key=(
                survey_object_key if "survey_object_key" in locals() else "N/A"
            ),
            decision=decision if "decision" in locals() else "N/A",
        )


@with_function_logging
@mcp.tool()
async def get_approval_workflow_status(
    impersonate_user: str,
    bearer_token: str,
    survey_object_ids: str,
    viewer: str = "ASSIGNEE",
    use_cache: bool = True,
) -> str:
    """
    Get the approval workflow status for one or more access request approvals (requires Graph API v3.2+).

    Returns the workflow step details including approval status, assignees, and completion time
    for a given set of survey object IDs.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"
        survey_object_ids: Comma-separated survey object IDs to look up workflow status for.
                          These are the surveyObjectKey values from get_pending_approvals.
                          Example: "2EC3860F-8263-4B90-A52A-130C0B9A0CA9"
                          PROMPT: "Please provide the survey object ID(s)"

    Optional parameters:
        viewer: The viewer perspective for the workflow status (default: "ASSIGNEE")
                Controls which workflow steps are visible based on the viewer's role.
        use_cache: Whether to use cache for this request (default: True)

    LLM INSTRUCTIONS - WHERE TO GET survey_object_ids:
        The survey_object_ids parameter comes from the surveyObjectKey field returned by
        get_pending_approvals or get_approval_details. The typical workflow is:
        1. Call get_pending_approvals to list pending approvals
        2. Extract the surveyObjectKey from the approval(s) of interest
        3. Pass those surveyObjectKey values as survey_object_ids to this function
        Example surveyObjectKey: "2EC3860F-8263-4B90-A52A-130C0B9A0CA9"

    LLM INSTRUCTIONS - RESPONSE FIELD GUIDE:
        - active: Whether this workflow step is currently active (True/False)
        - approvalStatus: Current status of the approval (e.g., "Pending", "Approved", "Rejected")
        - uId: Unique identifier for the workflow step
        - name: Internal name of the workflow step (e.g., "ResourceOwnerApproval")
        - surveyObjectKey: The survey object key (matches the input)
        - displayName: Human-readable workflow step name (e.g., "Perform resource owner approval")
        - completeTime: When the step was completed (null if still pending)
        - assignees: List of people assigned to this approval step, each with:
          - displayName: Full name (e.g., "Paul Walker")
          - firstName / lastName: Name parts
          - id: Internal user ID (store internally, do not display)
          - userName: Login username (e.g., "PAWA@OMADA.NET")

    LLM INSTRUCTIONS - DISPLAY TO USER:
        When presenting workflow status to the user, show:
        1. Display Name (displayName) - the workflow step title
        2. Approval Status (approvalStatus) - current status
        3. Active (active) - whether this step is the current one
        4. Assignees (assignees[].displayName, assignees[].userName) - who needs to act
        5. Complete Time (completeTime) - when it was completed, if applicable
        Do NOT display: uId, assignees[].id

    Returns:
        JSON response with approval workflow status details, or error message if the request fails
    """
    # ENTRY LOGGING
    logger.debug(
        f"DEBUG: ENTRY - get_approval_workflow_status(impersonate_user={impersonate_user}, survey_object_ids={survey_object_ids})"
    )

    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            survey_object_ids=survey_object_ids,
        )
        if error:
            return error

        # Build GraphQL query
        query = f"""query accessApprovalWorkflowStatus {{
  accessApprovalWorkflowStatus(options: {{viewer: {viewer}}}, surveyObjectIds: {json.dumps(survey_object_ids)}) {{
    active
    approvalStatus
    uId
    name
    surveyObjectKey
    displayName
    completeTime
    assignees {{
      displayName
      firstName
      id
      lastName
      userName
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.2 and caching support
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.2",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract workflow status from the GraphQL response
            if "data" in data and "accessApprovalWorkflowStatus" in data["data"]:
                workflow_status = data["data"]["accessApprovalWorkflowStatus"]

                return build_success_response(
                    data={"workflow_status": workflow_status},
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    survey_object_ids=survey_object_ids,
                    viewer=viewer,
                    steps_returned=len(workflow_status) if isinstance(workflow_status, list) else 1,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No approval workflow status found in response",
                    impersonated_user=impersonate_user,
                    survey_object_ids=survey_object_ids,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
                survey_object_ids=survey_object_ids,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
            survey_object_ids=survey_object_ids if "survey_object_ids" in locals() else "N/A",
        )


@with_function_logging
@mcp.tool()
async def get_compliance_workbench_survey_and_compliance_status(
    impersonate_user: str, bearer_token: str
) -> str:
    """
    Get compliance workbench configuration including compliance status values and survey templates from Omada GraphQL API.

    This function retrieves the compliance workbench configuration which includes:
    - Compliance status values (name and value pairs)
    - Survey templates (with ID, name, type, system name, and survey initiation activity ID)

    IMPORTANT: This function requires 2 mandatory parameters. If missing,
    you MUST prompt the user to provide them before calling this function.

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Returns:
        JSON response with compliance workbench configuration including:
        - complianceStatus: Array of {name, value} objects
        - surveyTemplates: Array of survey template objects with id, name, type, systemName, and surveyInitiationActivityId
    """
    try:
        # Validate mandatory field using helper
        error = validate_required_fields(impersonate_user=impersonate_user)
        if error:
            return error

        # Build GraphQL query (no parameters needed for this query)
        query = """query GetComplianceWorkbenchConfiguration {
  complianceWorkbenchConfiguration {
    complianceStatus {
      name
      value
    }
    surveyTemplates {
      name
      id
      surveyTemplateType
      systemName
      surveyInitiationActivityId
    }
  }
}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.0
        result = await _execute_graphql_request(
            query=query,
            impersonate_user=impersonate_user,
            graphql_version="3.0",
            bearer_token=bearer_token,
        )

        if result["success"]:
            data = result["data"]
            # Extract compliance workbench configuration from the GraphQL response
            if "data" in data and "complianceWorkbenchConfiguration" in data["data"]:
                config = data["data"]["complianceWorkbenchConfiguration"]

                compliance_status = config.get("complianceStatus", [])
                survey_templates = config.get("surveyTemplates", [])

                return build_success_response(
                    data={
                        "compliance_status": compliance_status,
                        "survey_templates": survey_templates,
                    },
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    compliance_status_count=len(compliance_status),
                    survey_templates_count=len(survey_templates),
                )
            else:
                return build_error_response(
                    error_type="NoConfigurationFound",
                    message="No compliance workbench configuration found in response",
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_compliance_workbench_data(
    impersonate_user: str,
    bearer_token: str,
    show_accounts: bool = False,
    use_cache: bool = True,
) -> str:
    """
    Get compliance workbench data with per-system compliance summary including orphan accounts,
    violations, and system health using Omada GraphQL API.

    This is the tool to use when the user asks about:
    - "orphan accounts" or "orphaned accounts" — look at the complianceStatus.orphaned field
    - "system health" or "compliance health" — look at the systemHealth percentage
    - "not approved" assignments per system — look at complianceStatus.notApproved
    - "pending deprovisioning" — look at complianceStatus.pendingDeprovisioning
    - "in violation" or "violations" per system — look at complianceStatus.inViolation
    - Compliance overview or compliance dashboard
    - Per-system compliance breakdown or summary

    IMPORTANT LLM INSTRUCTIONS - DISPLAY TO USER:
        Present results as a table with one row per system. Recommended columns:
        - System Name
        - System Health (percentage, e.g., "81.18%")
        - Explicitly Approved
        - Implicitly Approved
        - Implicitly Assigned
        - Not Approved
        - Orphaned
        - In Violation
        - Pending Deprovisioning
        - None (unclassified)

        Skip systems where ALL compliance counts are zero unless the user asks for all systems.

        When the user asks specifically about "orphan accounts":
        - Filter/highlight systems where orphaned > 0
        - If all systems show orphaned = 0, tell the user "No orphan accounts found across any system"

        TECHNICAL IDs (do NOT display to user unless asked):
        - system.id — internal GUID for the system
        - system.systemCategory.id — internal GUID for the system category
        - system.createTime — system creation timestamp
        - system.autoCreateAccounts — internal system configuration flag

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Optional parameters:
        show_accounts: Whether to include account-level detail (default: False).
                      Set to True only if the user specifically asks for account-level data.
        use_cache: Whether to use cache for this request (default: True)

    Returns:
        JSON response with per-system compliance data including:
        - total_systems: Number of systems returned
        - data: Array of system objects, each containing:
            - systemHealth: Health percentage (0-100)
            - system: System details (name, id, autoCreateAccounts, createTime, systemCategory)
            - complianceStatus: Compliance counts (explicitlyApproved, implicitlyApproved,
              implicitlyAssigned, none, notApproved, orphaned, inViolation, pendingDeprovisioning)
    """
    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            bearer_token=bearer_token,
        )
        if error:
            return error

        # Build GraphQL query
        show_accounts_value = "true" if show_accounts else "false"
        query = f"""query GetComplianceWorkbenchData {{
  complianceWorkbenchData(filters: {{showAccounts: {show_accounts_value}}}) {{
    systemHealth
    system {{
      autoCreateAccounts
      createTime
      id
      name
      systemCategory {{
        displayName
        id
      }}
    }}
    complianceStatus {{
      explicitlyApproved
      implicitlyApproved
      implicitlyAssigned
      none
      notApproved
      orhpaned
      pendingDeprovisioning
      inViolation
    }}
  }}
}}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.3 WITH CACHING
        result = await _execute_graphql_request_cached(
            query,
            impersonate_user,
            graphql_version="3.3",
            bearer_token=bearer_token,
            use_cache=use_cache,
        )

        if result["success"]:
            data = result["data"]
            # Extract compliance workbench data from the GraphQL response
            if "data" in data and "complianceWorkbenchData" in data["data"]:
                workbench_data = data["data"]["complianceWorkbenchData"]

                # Rename the misspelled "orhpaned" field to "orphaned" in each entry
                for entry in workbench_data:
                    if "complianceStatus" in entry and entry["complianceStatus"]:
                        cs = entry["complianceStatus"]
                        if "orhpaned" in cs:
                            cs["orphaned"] = cs.pop("orhpaned")

                return build_success_response(
                    data=workbench_data,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    total_systems=len(workbench_data),
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No compliance workbench data found in response",
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            # Handle GraphQL request failure using helper
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


@with_function_logging
@mcp.tool()
async def get_graphql_api_versions(
    impersonate_user: str,
    bearer_token: str,
) -> str:
    """
    Get the list of supported GraphQL API versions from the Omada Identity platform.

    Use this tool when the user asks:
    - "What API versions are available?"
    - "What is the latest GraphQL version?"
    - "Which API versions does Omada support?"
    - "What version of the Graph API is running?"

    IMPORTANT LLM INSTRUCTIONS - DISPLAY TO USER:
        Present the versions as a simple list formatted as "major.minor" (e.g., "3.3").
        Highlight the latest (highest) version.
        Example output: "Omada supports GraphQL API versions 1.0 through 3.3. The latest version is 3.3."

    REQUIRED PARAMETERS (prompt user if missing):
        impersonate_user: Email address of the user to impersonate (e.g., "user@domain.com")
                         PROMPT: "Please provide the email address to impersonate"
        bearer_token: Bearer token for authentication (required for GraphQL API)
                     PROMPT: "Please provide the bearer token"

    Returns:
        JSON response with:
        - total_versions: Number of API versions available
        - latest_version: The highest version available (e.g., "3.3")
        - data: Array of version objects with major and minor fields
    """
    try:
        # Validate mandatory fields using helper
        error = validate_required_fields(
            impersonate_user=impersonate_user,
            bearer_token=bearer_token,
        )
        if error:
            return error

        # Build GraphQL query
        query = """query GetGraphQLApiVersions {
  versions {
    major
    minor
  }
}"""

        logger.debug(f"GraphQL query: {query}")

        # Execute GraphQL request with version 3.3
        result = await _execute_graphql_request(
            query=query,
            impersonate_user=impersonate_user,
            graphql_version="3.3",
            bearer_token=bearer_token,
        )

        if result["success"]:
            data = result["data"]
            if "data" in data and "versions" in data["data"]:
                versions = data["data"]["versions"]

                # Find the latest version
                latest = max(versions, key=lambda v: (v["major"], v["minor"]))
                latest_version = f"{latest['major']}.{latest['minor']}"

                # Format versions as "major.minor" strings
                version_strings = [f"{v['major']}.{v['minor']}" for v in versions]

                return build_success_response(
                    data=versions,
                    endpoint=result["endpoint"],
                    impersonated_user=impersonate_user,
                    total_versions=len(versions),
                    latest_version=latest_version,
                    version_list=version_strings,
                )
            else:
                return build_error_response(
                    error_type="NoDataFound",
                    message="No version data found in response",
                    impersonated_user=impersonate_user,
                    response=data,
                )
        else:
            return build_error_response(
                error_type=result.get("error_type", "GraphQLError"),
                result=result,
                impersonated_user=impersonate_user,
            )

    except Exception as e:
        return build_error_response(
            error_type=type(e).__name__,
            message=str(e),
            impersonated_user=impersonate_user,
        )


if __name__ == "__main__":
    mcp.run()
