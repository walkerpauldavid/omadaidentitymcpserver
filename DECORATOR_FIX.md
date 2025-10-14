# Decorator Fix for Per-Function Logging

## Problem
The `@with_function_logging` decorator was not working for `get_calculated_assignments_detailed` function. The decorator wrapper was not being called, so DEBUG logging configured via `LOG_LEVEL_get_calculated_assignments_detailed=DEBUG` had no effect.

**Symptoms:**
- Function body executed normally (INFO logs appeared)
- Decorator diagnostics never appeared (`[DECORATOR] async_wrapper called` was missing)
- DEBUG logs inside the function never appeared
- Same decorator worked correctly for other functions like `query_omada_entity`

## Root Cause
The decorator was not copying the `__annotations__` attribute from the original function to the wrapper. FastMCP uses type annotations to introspect function parameters and generate MCP tool schemas. Without `__annotations__`, FastMCP likely failed to properly register the decorated function and may have fallen back to an unwrapped version or cached definition.

## Solution
Updated `with_function_logging` decorator (lines 124-129 and 142-147) to copy all critical function metadata:

```python
# Manually preserve metadata without setting __wrapped__
async_wrapper.__name__ = func.__name__
async_wrapper.__doc__ = func.__doc__
async_wrapper.__module__ = func.__module__
async_wrapper.__qualname__ = func.__qualname__
async_wrapper.__annotations__ = func.__annotations__  # CRITICAL for FastMCP
```

**Key points:**
1. `__annotations__` - Contains type hints (e.g., `identity_id: str`). Critical for FastMCP.
2. `__name__` - Function name (e.g., `"get_calculated_assignments_detailed"`)
3. `__doc__` - Docstring
4. `__module__` - Module path (e.g., `"__main__"`)
5. `__qualname__` - Qualified name for nested functions
6. **NOT setting `__wrapped__`** - This would allow tools to bypass the decorator using `inspect.unwrap()`

## Why __annotations__ Matters
FastMCP inspects function signatures to:
- Generate MCP tool parameter schemas
- Validate arguments before calling the function
- Provide type information to MCP clients

Without `__annotations__`, FastMCP cannot properly understand the decorated function's signature, leading to registration issues.

## Testing
After this fix, restart Claude Desktop and test:
1. Call `get_calculated_assignments_detailed`
2. Check log file for `[DECORATOR] async_wrapper called for function: get_calculated_assignments_detailed`
3. Verify DEBUG logs from within the function appear
4. Confirm the GraphQL query is logged at DEBUG level

## Related Files
- [server.py](server.py) - Lines 112-148 (decorator implementation)
- [.env](.env) - Line 57 (`LOG_LEVEL_get_calculated_assignments_detailed=DEBUG`)
