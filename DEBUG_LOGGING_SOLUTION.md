# DEBUG Logging Solution for get_calculated_assignments_detailed

## Problem
The `@with_function_logging` decorator was not being invoked at runtime for the `get_calculated_assignments_detailed` function, even though:
- The decorator was properly applied at import time
- Function metadata (__name__, __annotations__, etc.) was correctly preserved
- The same decorator worked perfectly for other functions like `query_omada_entity` and `get_pending_approvals`

This prevented per-function DEBUG logging from working when `LOG_LEVEL_get_calculated_assignments_detailed=DEBUG` was set in .env.

## Root Cause
**Unknown** - Despite extensive investigation, we could not determine why FastMCP's `@mcp.tool()` decorator was bypassing our `@with_function_logging` decorator wrapper specifically for this function. The decorator was applied correctly, but the wrapper was never called at runtime.

## Solution
**Workaround: Manual Logger Level Management**

Since the decorator approach failed for this specific function, we implemented a manual workaround directly in the function body:

```python
async def get_calculated_assignments_detailed(...):
    # WORKAROUND: Manually set logger level since decorator isn't working for this function
    old_level = logger.level
    old_handler_levels = [(handler, handler.level) for handler in logger.handlers]

    func_log_level = os.getenv("LOG_LEVEL_get_calculated_assignments_detailed", LOG_LEVEL).upper()
    new_level = getattr(logging, func_log_level, logging.INFO)
    logger.setLevel(new_level)
    for handler in logger.handlers:
        handler.setLevel(new_level)

    try:
        # Function body...
        logger.debug(f"GraphQL query: {query}")
        # ...
    finally:
        # Restore logger levels (workaround for decorator not working)
        logger.setLevel(old_level)
        for handler, level in old_handler_levels:
            handler.setLevel(level)
```

**What this does:**
1. At function entry, reads `LOG_LEVEL_get_calculated_assignments_detailed` from environment
2. Sets both logger and handler levels to the configured level (e.g., DEBUG)
3. Executes the function body with DEBUG logging enabled
4. Restores original logger levels in a `finally` block (ensures restoration even if errors occur)

## Why This Works
This approach:
- ✅ Bypasses whatever FastMCP issue was preventing the decorator from working
- ✅ Uses the same logic as the decorator (reads from .env, sets logger + handler levels)
- ✅ Properly restores levels after function execution
- ✅ Works reliably regardless of decorator/MCP framework quirks

## Files Modified
- **[server.py](server.py)** lines 1917-1935, 2092-2096: Added manual logger level management in `get_calculated_assignments_detailed`

## Testing
With `LOG_LEVEL_get_calculated_assignments_detailed=DEBUG` in .env:

```bash
# Check log file after calling the function
tail -100 pauls_omada_mcp_server.log | grep -A5 "get_calculated_assignments_detailed"
```

You should now see:
- DEBUG log with full GraphQL query
- Proper DEBUG-level logging throughout the function

## Future Improvements
If we can identify why FastMCP bypasses the decorator for this function, we could:
1. Fix the root cause and remove the workaround
2. Use the decorator approach consistently across all functions

For now, this manual workaround provides the needed DEBUG logging functionality.
