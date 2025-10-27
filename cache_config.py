# cache_config.py
"""
Cache TTL configuration based on data volatility.

This module defines time-to-live (TTL) values for different types of data
based on how frequently the data changes in the Omada system.
"""

# Default TTL for all cached data: 1 hour (3600 seconds)
DEFAULT_TTL = 3600

# Cache TTL configuration by data type
CACHE_TTL = {
    # Very static data (rarely changes) - 24 hours
    "resource_types": 86400,
    "systems": 86400,
    "compliance_config": 86400,

    # Relatively static data - 1 hour (default)
    "identities": 3600,
    "identity_by_email": 3600,
    "identity_by_uid": 3600,
    "resources": 3600,
    "roles": 3600,
    "contexts": 3600,

    # Moderately dynamic data - 15 minutes
    "calculated_assignments": 900,
    "access_requests": 900,

    # Dynamic data (minimal caching) - 5 minutes
    "pending_approvals": 300,
    "approval_details": 300,

    # Never cache (0 = no caching)
    "create_access_request": 0,
    "make_approval_decision": 0,
    "tokens": 0,
    "oauth": 0,
}


def get_ttl_for_operation(operation_name: str, is_mutation: bool = False) -> int:
    """
    Get appropriate TTL based on operation name and type.

    Args:
        operation_name: Name of the operation/function being cached
        is_mutation: True if this is a write operation (create/update/delete)

    Returns:
        TTL in seconds (0 means no caching)
    """
    # Never cache write operations
    if is_mutation:
        return 0

    # Convert operation name to lowercase for matching
    operation_lower = operation_name.lower()

    # Check for specific matches in CACHE_TTL
    for key, ttl in CACHE_TTL.items():
        if key.lower() in operation_lower:
            return ttl

    # Default: 1 hour for unknown query operations
    return DEFAULT_TTL


def should_cache(operation_name: str, is_mutation: bool = False) -> bool:
    """
    Determine if an operation should be cached.

    Args:
        operation_name: Name of the operation/function
        is_mutation: True if this is a write operation

    Returns:
        True if should cache, False otherwise
    """
    ttl = get_ttl_for_operation(operation_name, is_mutation)
    return ttl > 0
