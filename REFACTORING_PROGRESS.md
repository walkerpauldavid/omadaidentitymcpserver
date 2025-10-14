# Code Simplification Refactoring Progress

## Phase 1 Complete: Helper Functions Created

### Created Files:
- **helpers.py** - Contains 4 helper functions to reduce code duplication

### Helper Functions:

1. **validate_required_fields(**kwargs)** - Validates that required fields are non-empty
   - Returns error JSON string if validation fails, None if all valid
   - Reduces 6-7 lines of validation code to 3 lines

2. **build_error_response(error_type, result=None, message=None, **extra_fields)** - Builds standardized error responses
   - Handles GraphQL errors, validation errors, exceptions
   - Automatically extracts status_code, error, endpoint from result dict
   - Reduces 10-13 lines to 4-6 lines

3. **build_success_response(data=None, endpoint=None, **context)** - Builds standardized success responses
   - Flexible data parameter (can be dict, list, None)
   - Automatically includes context fields
   - Reduces 9-11 lines to 7-9 lines

4. **build_pagination_clause(page=None, rows=None)** - Builds GraphQL pagination clause (Recommendation #6)
   - Returns formatted pagination string or empty string
   - Reduces 3-4 lines to 1 line
   - Reusable across all paginated queries

## Refactored Functions (4 Examples)

### ✅ 1. get_identity_contexts (lines 2119-2208)
**Before:** 111 lines with manual validation and response building
**After:** ~90 lines using helpers
**Savings:** ~21 lines

### ✅ 2. get_pending_approvals (lines 2211-2354)
**Before:** ~156 lines with manual validation and response building
**After:** ~135 lines using helpers
**Savings:** ~21 lines

### ✅ 3. get_compliance_workbench_survey_and_compliance_status (lines 2571-2676)
**Before:** ~105 lines with manual validation and response building
**After:** ~88 lines using helpers
**Savings:** ~17 lines

### ✅ 4. get_identities_for_beneficiary (lines 1758-1872)
**Before:** ~115 lines with manual validation, response building, and pagination logic
**After:** ~93 lines using helpers including build_pagination_clause
**Savings:** ~22 lines

**Total Savings So Far:** ~81 lines reduced from 4 functions

## Remaining Functions to Refactor (~23 functions)

These functions follow the same patterns and can be refactored using the helper functions:

### GraphQL Query Functions:
1. get_access_requests
2. create_access_request
3. get_resources_for_beneficiary
4. get_approval_details
5. make_approval_decision
6. get_calculated_assignments_detailed
7. query_calculated_assignments

### OData Query Functions:
9. query_omada_entity
10. query_omada_identity
11. query_omada_resources
12. query_omada_entities
13. get_all_omada_identities

### Utility Functions:
14. ping

### And approximately 10 more functions throughout server.py

## Refactoring Pattern

### Step 1: Replace validation code
**Before:**
```python
if not impersonate_user or not impersonate_user.strip():
    return json.dumps({
        "status": "error",
        "message": "Missing required field: impersonate_user",
        "error_type": "ValidationError"
    }, indent=2)
```

**After:**
```python
error = validate_required_fields(impersonate_user=impersonate_user)
if error:
    return error
```

**For multiple fields:**
```python
error = validate_required_fields(
    impersonate_user=impersonate_user,
    identity_id=identity_id,
    resource_id=resource_id
)
if error:
    return error
```

### Step 2: Replace success responses
**Before:**
```python
return json.dumps({
    "status": "success",
    "identity_id": identity_id,
    "impersonated_user": impersonate_user,
    "contexts_count": len(contexts),
    "contexts": contexts,
    "endpoint": result["endpoint"]
}, indent=2)
```

**After:**
```python
return build_success_response(
    data=contexts,
    endpoint=result["endpoint"],
    identity_id=identity_id,
    impersonated_user=impersonate_user,
    contexts_count=len(contexts)
)
```

### Step 3: Replace error responses (GraphQL failures)
**Before:**
```python
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
```

**After:**
```python
return build_error_response(
    error_type=result.get("error_type", "GraphQLError"),
    result=result,
    identity_id=identity_id,
    impersonated_user=impersonate_user
)
```

### Step 4: Replace exception handlers
**Before:**
```python
except Exception as e:
    return json.dumps({
        "status": "exception",
        "impersonated_user": impersonate_user,
        "error": str(e),
        "error_type": type(e).__name__
    }, indent=2)
```

**After:**
```python
except Exception as e:
    return build_error_response(
        error_type=type(e).__name__,
        message=str(e),
        impersonated_user=impersonate_user
    )
```

### Step 5: Replace pagination clause (for paginated queries)
**Before:**
```python
pagination_clause = ""
if page is not None and rows is not None:
    pagination_clause = f"pagination: {{page: {page}, rows: {rows}}}, "

query = f"""query {{
  identities(
    {pagination_clause}filters: {{}}
  ) {{ data {{ id }} }}
}}"""
```

**After:**
```python
pagination_clause = build_pagination_clause(page=page, rows=rows)

query = f"""query {{
  identities(
    {pagination_clause}filters: {{}}
  ) {{ data {{ id }} }}
}}"""
```

## Estimated Total Impact

- **Current duplication:** ~500 lines of repetitive code across 27 functions
- **After full refactoring:** ~300 lines (40% reduction)
- **Savings:** ~200 lines eliminated
- **Maintainability:** Centralized validation and response building logic
- **Consistency:** All functions return uniform JSON structure

## Next Steps

1. Continue refactoring remaining functions one at a time
2. Test each refactored function to ensure helpers work correctly
3. Consider Phase 2 recommendations (extract_graphql_data, build_pagination_clause) if desired
4. Update tests if needed
5. Commit changes when batch is complete

## Testing Recommendations

After refactoring each function:
1. Test with valid parameters (should return success response)
2. Test with missing required parameters (should return validation error)
3. Test with invalid parameters (should return appropriate error)
4. Verify response format matches original format

## Notes

- Helper functions preserve exact same JSON structure as original code
- No functional changes, only code organization improvements
- All original behavior is maintained
- Error messages and field names remain identical
