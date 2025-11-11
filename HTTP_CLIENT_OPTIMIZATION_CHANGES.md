# HTTP Client Optimization Changes

## Summary
Migrated from creating new `httpx.AsyncClient()` instances per request to using a shared, optimized module-level client with HTTP/2 support, connection pooling, and keepalive settings.

## Benefits
- **Connection Reuse**: All HTTP requests share the same connection pool
- **HTTP/2 Multiplexing**: Multiple concurrent requests can use a single TCP connection
- **Keepalive Optimization**: Connections stay open for 5 minutes and are reused across requests
- **Better Performance**: Eliminates overhead from creating/tearing down clients per request
- **Lower Latency**: Connection establishment happens once, not per request

## Changes Made

### 1. Added Module-Level Shared HTTP Client (Lines 60-75)

```python
# Configure optimized HTTP client with HTTP/2 support and connection pooling
# This client is reused across all requests for better performance
http_client = httpx.AsyncClient(
    http2=True,  # Enable HTTP/2 multiplexing for concurrent requests
    timeout=httpx.Timeout(30.0, connect=10.0),  # 30s total, 10s connect timeout
    limits=httpx.Limits(
        max_keepalive_connections=20,  # Reuse up to 20 connections
        max_connections=100,  # Support up to 100 concurrent requests
        keepalive_expiry=300.0  # Keep connections alive for 5 minutes
    ),
    headers={
        "User-Agent": "Omada-MCP-Server/1.0",
    },
)

logger.info("HTTP client configured with HTTP/2 support and connection pooling")
```

**Configuration Details:**
- `http2=True`: Enables HTTP/2 protocol for multiplexing multiple requests over a single connection
- `timeout=httpx.Timeout(30.0, connect=10.0)`:
  - Total timeout: 30 seconds for the entire request
  - Connect timeout: 10 seconds to establish the connection
- `limits=httpx.Limits(...)`:
  - `max_keepalive_connections=20`: Keep up to 20 connections alive in the pool
  - `max_connections=100`: Allow up to 100 concurrent connections total
  - `keepalive_expiry=300.0`: Keep idle connections alive for 5 minutes (300 seconds)
- `headers`: Set a consistent User-Agent for all requests

### 2. Updated OData Query Function (Line 643)

**Before:**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(endpoint_url, headers=headers, timeout=30.0)

    if response.status_code == 200:
        # Parse the response
        data = response.json()
        # ...
```

**After:**
```python
response = await http_client.get(endpoint_url, headers=headers, timeout=30.0)

if response.status_code == 200:
    # Parse the response
    data = response.json()
    # ...
```

**Changes:**
- Removed `async with httpx.AsyncClient() as client:` context manager
- Changed `client.get()` to `http_client.get()` using the shared client
- Adjusted indentation for all subsequent lines (removed one level of indentation)

**Location:** `query_omada_entity` function in [server.py:643](c:\Users\demoadm\Documents\Code\omada_mcp_server\server.py#L643)

### 3. Updated GraphQL Request Function (Line 1574)

**Before:**
```python
# Execute request
async with httpx.AsyncClient() as client:
    response = await client.post(graphql_url, json=payload, headers=headers, timeout=30.0)

    # Capture raw HTTP details for debugging
    raw_request_body = json.dumps(payload, indent=2)
    raw_response_body = response.text
    # ...
```

**After:**
```python
# Execute request using shared optimized client
response = await http_client.post(graphql_url, json=payload, headers=headers, timeout=30.0)

# Capture raw HTTP details for debugging
raw_request_body = json.dumps(payload, indent=2)
raw_response_body = response.text
# ...
```

**Changes:**
- Removed `async with httpx.AsyncClient() as client:` context manager
- Changed `client.post()` to `http_client.post()` using the shared client
- Updated comment to reflect use of shared optimized client
- Adjusted indentation for all subsequent lines (removed one level of indentation)

**Location:** `_execute_graphql_request` function in [server.py:1574](c:\Users\demoadm\Documents\Code\omada_mcp_server\server.py#L1574)

## Files Modified
- `c:\Users\demoadm\Documents\Code\omada_mcp_server\server.py`

## Testing Recommendations

1. **Verify Connection Reuse**: Monitor network connections to confirm that connections are being reused across multiple requests
2. **Test Concurrent Requests**: Ensure that concurrent requests work correctly with the shared client
3. **Check Performance**: Compare response times before/after the change (should see improvement, especially for multiple requests)
4. **Validate HTTP/2**: Confirm that HTTP/2 is being used when the server supports it
5. **Test Error Handling**: Verify that error handling still works correctly with the shared client

## Performance Expectations

### Before (New Client Per Request)
- Each request creates a new AsyncClient instance
- TCP connection established for each request
- TLS handshake for each request
- Higher latency and resource usage

### After (Shared Client with Connection Pooling)
- Single AsyncClient instance reused across all requests
- Connections kept alive and reused from the pool
- TLS handshake only on first connection
- HTTP/2 multiplexing allows multiple requests on single connection
- Lower latency and resource usage

## Migration Notes

### Pattern Change
The migration follows this pattern:

```python
# OLD PATTERN (Context Manager - Creates New Client)
async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers, timeout=30.0)
    # Process response...

# NEW PATTERN (Shared Client)
response = await http_client.get(url, headers=headers, timeout=30.0)
# Process response...
```

### Why This Works
- The shared `http_client` is created at module level (during import)
- It persists for the lifetime of the application
- It's safe to use across multiple async functions (httpx.AsyncClient is designed for this)
- Connection pooling and keepalive are handled automatically by httpx

## Additional Notes

- Test files (in `tests/` directory) still use the old pattern - they are not affected by these changes
- The shared client is configured once at startup, providing consistent behavior across all requests
- All existing timeout and header configurations are preserved in the function calls
- No API contract changes - all functions maintain the same signatures and behavior

## References

- httpx Documentation: https://www.python-httpx.org/
- HTTP/2 Support: https://www.python-httpx.org/http2/
- Connection Pooling: https://www.python-httpx.org/advanced/#pool-limit-configuration
- Timeout Configuration: https://www.python-httpx.org/advanced/#timeout-configuration