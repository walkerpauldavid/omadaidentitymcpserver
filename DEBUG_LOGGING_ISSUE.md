# Debugging Logging Issue: Line 2123 vs Line 1790

## The Problem

You reported that:
- Line 1790 (`get_identities_for_beneficiary`) IS logging the GraphQL query ✅
- Line 2123 (`get_identity_contexts`) is NOT logging the GraphQL query ❌

Both lines have identical code:
```python
logger.debug(f"GraphQL query: {query}")
```

## Root Cause Analysis

### Investigation Steps Taken:

1. **Checked both functions have decorators** ✅
   - Both have `@with_function_logging`
   - Both have `@mcp.tool()`

2. **Checked .env configuration** ✅
   - `LOG_LEVEL_get_identities_for_beneficiary=DEBUG` ✅
   - `LOG_LEVEL_get_identity_contexts=DEBUG` ✅

3. **Checked logging handler fixes** ✅
   - Server was restarted at 15:53:21
   - Decorator messages appear in logs
   - Logging system is working correctly

4. **Checked recent log entries** ❌
   - No calls to `get_identity_contexts` found in logs
   - Only `query_omada_entity` has been called since restart

## The Real Issue

**`get_identity_contexts` is NOT being called at all in your test workflow!**

The function is:
- ✅ Properly decorated
- ✅ Properly configured for DEBUG logging
- ✅ Registered as an MCP tool
- ✅ Contains the debug log statement

But it's **simply not being invoked** by Claude Desktop or your test client.

## Comparison

| Function | Line | Working? | Reason |
|----------|------|----------|---------|
| `get_identities_for_beneficiary` | 1790 | ✅ YES | Actually being called by client |
| `get_identity_contexts` | 2123 | ❓ N/A | Never called - can't test logging |

## How to Verify

### Option 1: Test Directly

Run the test script:
```bash
cd /c/Users/demoadm/Documents/Code/omada_mcp_server
python test_get_identity_contexts.py
```

You'll need:
- A valid identity UId (32-character GUID)
- An email to impersonate
- A bearer token

If the function works and logs appear, then the logging IS working - it's just not being called in your workflow.

### Option 2: Check MCP Client

In Claude Desktop or your MCP client, explicitly call:
```
Use get_identity_contexts with:
- identity_id: "7ac8b482-272f-4bf0-9339-ce3742c2b4ca"
- impersonate_user: "hanulr@54mv4c.onmicrosoft.com"
- bearer_token: "eyJ0..."
```

Then check the log file for:
```
DEBUG - Function 'get_identity_contexts' using log level: DEBUG
DEBUG - get_identity_contexts called with identity_id=..., impersonate_user=...
DEBUG - Validation passed, building GraphQL query for identity_id: ...
DEBUG - GraphQL query: query GetContextsForIdentity { ... }
```

## Why `get_identities_for_beneficiary` Shows Logs

This function is being called in your workflow, so you see:
1. Decorator message: `Function 'get_identities_for_beneficiary' using log level: DEBUG`
2. Debug logs from inside the function
3. GraphQL query output

## Why `get_identity_contexts` Doesn't Show Logs

This function is NOT being called in your workflow, so:
1. No decorator message appears
2. No debug logs appear
3. No GraphQL query appears

**It's not a logging problem - it's that the function isn't being invoked!**

## Solution

To see logs from `get_identity_contexts`:

1. **Actually call the function** in your workflow
2. Use Claude Desktop to explicitly request getting identity contexts
3. Run the test script: `python test_get_identity_contexts.py`
4. Check the prompts - make sure `request_access_workflow` or other prompts guide Claude to call this function

## Verification

After calling `get_identity_contexts`, you should see in the log:
```
2025-10-13 HH:MM:SS - __main__ - DEBUG - Function 'get_identity_contexts' using log level: DEBUG
2025-10-13 HH:MM:SS - __main__ - DEBUG - get_identity_contexts called with identity_id=7ac8b482-..., impersonate_user=hanulr@...
2025-10-13 HH:MM:SS - __main__ - DEBUG - Validation passed, building GraphQL query for identity_id: 7ac8b482-...
2025-10-13 HH:MM:SS - __main__ - DEBUG - GraphQL query: query GetContextsForIdentity {
  accessRequestComponents {
    contexts(identityIds: "7ac8b482-...") {
      id
      displayName
      type
    }
  }
}
2025-10-13 HH:MM:SS - __main__ - INFO - GraphQL Request to https://pawa-poc2.omada.cloud/api/Domain/3.0 with impersonation of hanulr@...
```

If you see all of the above, then logging IS working - you just weren't calling the function before!
