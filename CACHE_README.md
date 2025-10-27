# Omada MCP Server - Cache System

## Overview

The Omada MCP Server includes a SQLite-based caching system to improve performance and reduce API calls to the Omada Identity system. The cache provides clear visibility into when cached data is used versus when fresh data is fetched from the API.

## Features

- ✅ **Automatic caching** of API responses with configurable TTL
- ✅ **User-specific caching** - cache is isolated per authenticated user for security
- ✅ **Clear visibility logging** - shows when cache is HIT vs MISS
- ✅ **1-hour default TTL** - cached data expires and refreshes automatically
- ✅ **Cache management tools** - clear cache, view statistics
- ✅ **Optimized identity lookups** - fast lookups by email or UId
- ✅ **SQLite storage** - lightweight, no external dependencies

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable/disable caching (default: true)
CACHE_ENABLED=true

# Cache TTL in seconds (default: 3600 = 1 hour)
CACHE_TTL_SECONDS=3600

# Automatic cleanup of expired entries (default: true)
# Runs every CACHE_TTL_SECONDS to remove expired cache
CACHE_AUTO_CLEANUP=true
```

### How It Works

1. **First Request** - Data fetched from Omada API, stored in cache
   ```
   ❌ CACHE MISS for graphql - fetching from API
   💾 CACHE STORED for graphql (TTL: 3600s, expires: 15:30:45)
   ```

2. **Subsequent Requests (within TTL)** - Data served from cache
   ```
   🎯 CACHE HIT for graphql (age: 127.3s)
   ```

3. **After TTL Expires** - Fresh data fetched automatically
   ```
   ❌ CACHE MISS for graphql - fetching from API
   💾 CACHE STORED for graphql (TTL: 3600s, expires: 16:30:45)
   ```

4. **Automatic Cleanup** - Background thread removes expired entries
   ```
   🔄 Auto-cleanup thread started (interval: 3600s)
   🧹 AUTO-CLEANUP: Removed 15 expired entries
   ```

### Automatic Cache Cleanup

The cache includes an automatic cleanup system that runs in the background:

- **How it works**: A background thread runs every `CACHE_TTL_SECONDS` (default: 1 hour)
- **What it does**: Removes all expired cache entries from the database
- **Why it matters**: Prevents the cache database from growing indefinitely
- **Configuration**: Controlled by `CACHE_AUTO_CLEANUP=true` in `.env`

**Log messages you'll see:**
```
🔄 Auto-cleanup thread started (interval: 3600s)
🧹 AUTO-CLEANUP: Removed 23 expired entries
🛑 Auto-cleanup thread stopped
```

**Performance impact:**
- Minimal - runs in a separate daemon thread
- Only activates once per hour (or your configured TTL)
- Database operations are quick (typically <100ms)

## Security: User-Specific Caching

**IMPORTANT**: The cache is isolated per authenticated user to prevent data leakage between users.

### How It Works

When caching API responses, the system automatically:

1. **Extracts user identity from JWT bearer token**
   - Reads standard JWT claims: email, upn, unique_name, preferred_username, sub, or oid
   - Example: User john.doe@company.com gets their own cache space

2. **Includes user identity in cache key**
   - Cache keys are generated from: query + parameters + **user_identity**
   - Different users get different cache entries even for identical queries

3. **Prevents cross-user data access**
   - User A's cached data is NEVER returned to User B
   - Each user's cache is completely isolated

### Example Scenario

```
User A (alice@company.com) queries access requests:
- Bearer token decoded → user_identity="alice@company.com"
- Cache key: sha256("graphql:{query}:alice@company.com:...")
- Data cached with User A's identity

User B (bob@company.com) queries same access requests:
- Bearer token decoded → user_identity="bob@company.com"
- Cache key: sha256("graphql:{query}:bob@company.com:...")
- Gets DIFFERENT cache entry (cache MISS)
- User B never sees User A's data ✅
```

### Fallback Behavior

If the system cannot extract user identity from the JWT:
- Falls back to using a hash of the bearer token
- Still prevents cross-user access (different tokens = different cache)
- Warning logged: "Could not extract user identity from JWT claims"

### Security Guarantees

✅ **No cross-user data leakage** - each user's cache is isolated
✅ **Works with token refresh** - user identity extracted from new tokens
✅ **Automatic** - no configuration needed, works out of the box
✅ **Auditable** - user identity logged at DEBUG level

## Cache Management Tools

### Get Cache Statistics

View cache performance metrics:

```python
get_cache_stats()
```

Returns:
- Total cached entries (valid vs expired)
- Cache hit counts
- Most frequently accessed endpoints
- Configuration details

Example output:
```json
{
  "cache_enabled": true,
  "cache_statistics": {
    "api_cache": {
      "total_entries": 25,
      "valid_entries": 23,
      "expired_entries": 2,
      "total_hits": 156,
      "avg_hits_per_entry": 6.24
    },
    "identity_cache": {
      "total_entries": 15,
      "valid_entries": 15,
      "total_hits": 89
    },
    "top_endpoints": [
      {"endpoint": "graphql", "hits": 102},
      {"endpoint": "identity", "hits": 54}
    ]
  },
  "expired_entries_cleaned": 2
}
```

### Clear Cache

Force fresh data from API:

```python
# Clear all cache
clear_cache()

# Clear specific endpoint
clear_cache(endpoint="graphql")
```

Use cases:
- After making changes in Omada (new assignments, approvals, etc.)
- When you need guaranteed fresh data
- Testing/debugging

## Cache Visibility in Logs

All cache operations are logged with clear indicators:

| Log Message | Meaning |
|------------|---------|
| `🎯 CACHE HIT` | Data served from cache |
| `❌ CACHE MISS` | Fetching fresh data from API |
| `💾 CACHE STORED` | New data cached |
| `🗑️ CACHE CLEARED` | Cache invalidated |
| `🧹 CLEANUP` | Expired entries removed |
| `📊 Cache stats` | Statistics requested |

Example log sequence:
```
2025-01-23 14:30:15 - INFO - ❌ CACHE MISS for graphql - fetching from API
2025-01-23 14:30:16 - INFO - 💾 CACHE STORED for graphql (TTL: 3600s, expires: 15:30:16)
2025-01-23 14:32:00 - INFO - 🎯 CACHE HIT for graphql (age: 105.2s)
2025-01-23 14:35:00 - INFO - 🎯 CACHE HIT for graphql (age: 285.7s)
2025-01-23 15:45:00 - INFO - ❌ CACHE MISS for graphql - fetching from API
2025-01-23 15:45:01 - INFO - 💾 CACHE STORED for graphql (TTL: 3600s, expires: 16:45:01)
```

## Cache TTL Strategy

Different data types have different default TTLs based on volatility:

| Data Type | Default TTL | Rationale |
|-----------|-------------|-----------|
| Resource Types, Systems | 24 hours | Very static data |
| Identities, Resources | 1 hour | Relatively static |
| Calculated Assignments | 15 minutes | Moderately dynamic |
| Pending Approvals | 5 minutes | Dynamic data |
| Write Operations | No cache | Always fresh |

You can override the global TTL using `CACHE_TTL_SECONDS` in `.env`.

## Cache Database

- **Location**: `omada_cache.db` (in server directory)
- **Type**: SQLite3
- **Size**: Typically < 10MB
- **Tables**:
  - `api_cache` - General API responses
  - `identity_cache` - Optimized identity lookups
  - `resource_type_cache` - Resource type mappings

The database is automatically created on first run and is excluded from git (`.gitignore`).

## Performance Benefits

With caching enabled:

- **10-100x faster** response times for cached queries
- **Reduced API load** - fewer calls to Omada
- **Lower bandwidth** usage
- **Better user experience** - instant responses for common queries

Example timing:
```
Without cache: 850ms API call
With cache:    8ms cache lookup (100x faster!)
```

## Disabling Cache

To disable caching completely:

```bash
# In .env
CACHE_ENABLED=false
```

Or temporarily for a single request:
```python
# Most functions support use_cache parameter
query_omada_identity(email="user@domain.com", use_cache=False)
```

## Troubleshooting

### Cache not working?

1. Check `.env` has `CACHE_ENABLED=true`
2. Verify no errors in logs during server startup
3. Run `get_cache_stats()` to confirm cache is initialized

### Stale data?

1. Use `clear_cache()` to force refresh
2. Reduce `CACHE_TTL_SECONDS` for more frequent updates
3. Check logs for cache age in `CACHE HIT` messages

### Cache too large?

1. Reduce `CACHE_TTL_SECONDS`
2. Run `get_cache_stats()` and note expired entries
3. Expired entries are automatically cleaned up

## Best Practices

1. **Keep cache enabled** for production use (default)
2. **Use default TTL (1 hour)** unless you have specific requirements
3. **Clear cache** after making changes in Omada
4. **Monitor cache stats** periodically to tune performance
5. **Check logs** to understand cache hit/miss patterns

## Technical Details

### Cache Key Generation

Cache keys are generated using SHA-256 hash of:
- Endpoint name
- Query parameters (sorted for consistency)

This ensures:
- Same query always generates same key
- Different parameters create different cache entries
- No collisions

### Expiration Strategy

- **Lazy expiration**: Expired entries are not served
- **Active cleanup**: Periodic cleanup removes expired entries
- **TTL-based**: Each entry has independent expiration time

### Thread Safety

The SQLite database handles concurrent access automatically. Multiple requests can safely read/write to the cache simultaneously.

## Example Workflows

### Workflow 1: User Lookup with Caching

```python
# First lookup - cache miss
query_omada_identity(email="john.doe@company.com")
# Log: ❌ CACHE MISS for identity - fetching from API
# Log: 💾 IDENTITY CACHED: john.doe@company.com

# Second lookup (within 1 hour) - cache hit
query_omada_identity(email="john.doe@company.com")
# Log: 🎯 IDENTITY CACHE HIT for email: john.doe@company.com (age: 45.2s)
```

### Workflow 2: Force Fresh Data

```python
# Get current assignments
get_calculated_assignments_detailed(identity_ids="abc-123", ...)
# Log: 🎯 CACHE HIT for graphql (age: 245.8s)

# Make changes in Omada, then clear cache
clear_cache()
# Log: 🗑️ ENTIRE cache cleared - 15 entries deleted

# Get updated assignments
get_calculated_assignments_detailed(identity_ids="abc-123", ...)
# Log: ❌ CACHE MISS for graphql - fetching from API
```

### Workflow 3: Monitor Performance

```python
# View cache statistics
get_cache_stats()

# Example output shows:
# - 45 valid cache entries
# - 230 total cache hits
# - Average 5.1 hits per entry
# - Top endpoint: graphql with 150 hits
```

## Future Enhancements

Potential improvements:
- Cache warming on server startup
- Configurable per-endpoint TTLs
- Cache versioning for schema changes
- Compression for large responses
- Cache invalidation webhooks (if Omada supports)

---

**Questions or issues?** Check the logs for detailed cache activity or run `get_cache_stats()` to inspect cache performance.
