# get_compliance_workbench_data

## Overview

New MCP tool added to the Omada MCP Server that retrieves compliance workbench data showing compliance status summaries by system.

**Location:** `server.py:3622-3775`

**GraphQL Query:** `complianceWorkbenchData`

**API Version:** 3.0

## Purpose

This tool provides summary information about the number of assignments in different compliance states for each system. It returns count-level data (not detailed account information) showing:
- How many assignments are approved
- How many are in violation
- How many are not approved
- Other compliance status counts per system

## Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `impersonate_user` | `str` | Email address of the user to impersonate (e.g., "user@domain.com") |
| `bearer_token` | `str` | Bearer token for authentication (required for GraphQL API) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_accounts` | `bool` | `True` | Whether to show account-level data |
| `is_application_accounts_system_visible` | `bool` | `False` | Whether application accounts systems are visible |

## Return Data

### Response Structure

```json
{
  "success": true,
  "data": [
    {
      "system": {
        "id": "system-guid",
        "name": "System Name",
        "systemCategory": {
          "displayName": "Category Name",
          "policyDefinitions": "policy-info"
        }
      },
      "complianceStatus": {
        "explicitlyApproved": 100,
        "implicitlyApproved": 50,
        "implicitlyAssigned": 25,
        "inViolation": 10,
        "none": 5,
        "notApproved": 15,
        "orphaned": 2,
        "pendingDeprovisioning": 3
      }
    }
  ],
  "summary": {
    "total_systems": 10,
    "systems_with_violations": 3,
    "total_violations": 45,
    "total_not_approved": 78
  },
  "filters": {
    "show_accounts": true,
    "is_application_accounts_system_visible": false
  }
}
```

### Compliance Status Fields

| Field | Description |
|-------|-------------|
| `explicitlyApproved` | Number of explicitly approved assignments |
| `implicitlyApproved` | Number of implicitly approved assignments |
| `implicitlyAssigned` | Number of implicitly assigned assignments |
| `inViolation` | Number of assignments in violation |
| `none` | Number of assignments with no status |
| `notApproved` | Number of not approved assignments |
| `orphaned` | Number of orphaned assignments |
| `pendingDeprovisioning` | Number of assignments pending deprovisioning |

### Summary Statistics

The response includes aggregate statistics:
- `total_systems`: Total number of systems returned
- `systems_with_violations`: Count of systems that have at least one violation
- `total_violations`: Sum of all violations across all systems
- `total_not_approved`: Sum of all not approved assignments across all systems

## Usage Examples

### When to Use This Tool

Use `get_compliance_workbench_data` when users ask:
- "Show compliance status by system"
- "How many violations per system"
- "Compliance workbench summary"
- "Show compliance data"
- "Which systems have violations"
- "Compliance status overview"

### Example Call

```python
result = await get_compliance_workbench_data(
    impersonate_user="user@domain.com",
    bearer_token="eyJ0eXAi...",
    show_accounts=True,
    is_application_accounts_system_visible=False
)
```

## Implementation Details

### GraphQL Query

```graphql
query GetComplianceWorkbenchData {
  complianceWorkbenchData(
    filters: {showAccounts: true, isApplicationAccountsSystemVisible: false}
  ) {
    system {
      id
      name
      systemCategory {
        displayName
        policyDefinitions
      }
    }
    complianceStatus {
      explicitlyApproved
      implicitlyApproved
      implicitlyAssigned
      inViolation
      none
      notApproved
      orphaned
      pendingDeprovisioning
    }
  }
}
```

### Key Features

1. **Performance Timing:** Includes TOOL START/END logging with duration
2. **Caching:** Uses `_execute_graphql_request_cached()` for improved performance
3. **Validation:** Validates required parameters using `validate_required_fields()`
4. **Error Handling:** Comprehensive error handling with `build_error_response()`
5. **Debug Logging:** Entry logging with all parameters
6. **Decorators:** Uses `@with_function_logging` and `@mcp.tool()`

### Code Pattern Followed

This tool follows the same implementation pattern as other tools in the Omada MCP Server:

```python
@with_function_logging
@mcp.tool()
async def get_compliance_workbench_data(...):
    # PERFORMANCE TIMING: Record start time
    start_time = datetime.now()
    logger.info(f"TOOL START - get_compliance_workbench_data called at ...")

    # ENTRY LOGGING
    logger.debug(f"DEBUG: ENTRY - get_compliance_workbench_data(...)")

    try:
        # Validate parameters
        # Build GraphQL query
        # Execute request with caching
        # Process response
        # Return success response
    except Exception as e:
        # Return error response
    finally:
        # PERFORMANCE TIMING: Calculate and log execution time
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logger.info(f"TOOL END - get_compliance_workbench_data | START: ... | END: ... | DURATION: ...")
```

## Related Tools

### Comparison with `get_compliance_workbench_survey_and_compliance_status`

| Feature | `get_compliance_workbench_data` | `get_compliance_workbench_survey_and_compliance_status` |
|---------|--------------------------------|-------------------------------------------------------|
| **Query** | `complianceWorkbenchData` | `complianceWorkbenchConfiguration` |
| **Purpose** | Get actual compliance data | Get configuration/metadata |
| **Returns** | System compliance counts | Status definitions and survey templates |
| **Use Case** | View current compliance state | Configure compliance workbench |
| **Data Type** | Operational data | Configuration data |

## Testing

After adding this tool:

1. **Clear Python cache:**
   ```bash
   rm -f C:\Users\demoadm\Documents\Code\omada_mcp_server\__pycache__\server.cpython-313.pyc
   ```

2. **Restart the MCP server** to load the new tool

3. **Test the tool** with a valid user and bearer token:
   ```python
   get_compliance_workbench_data(
       impersonate_user="test@domain.com",
       bearer_token="your-token-here"
   )
   ```

## Notes

- The tool returns summary counts only, not detailed account information
- Caching is enabled by default (`use_cache=True`)
- GraphQL API version 3.0 is required
- Boolean filter parameters are automatically converted to lowercase strings for GraphQL compatibility

## Change History

| Date | Change |
|------|--------|
| 2025-11-11 | Initial implementation based on `graphql_complianceWorkbenchresponse.txt` example |
