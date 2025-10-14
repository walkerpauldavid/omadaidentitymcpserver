# Bearer Token Storage Strategy

## Security vs Performance Trade-offs

You're right to be concerned about security. Let's analyze the options:

## Current Approach: Client-Side Token Storage
**How it works:** Claude Desktop (MCP client) stores the token and passes it with every request

### Pros:
✅ **Most Secure**
- Token never stored on server
- Token never written to disk on server
- No risk of token theft from server filesystem
- Follows principle of least privilege
- MCP server is stateless (can restart without losing tokens)
- Each user session is isolated

✅ **Best Practice**
- Matches OAuth2 security model (client holds tokens)
- Server can't use tokens for unauthorized requests
- Easier to audit (token only in one place)
- No risk of token leakage through server logs

### Cons:
❌ **Verbose in UI**
- Long token strings in every request
- Can clutter conversation
- Slightly slower (token transmitted every time)

### Performance Impact:
- Negligible: Bearer tokens are ~2KB, network overhead is minimal
- Modern HTTP/2 compression handles repetitive data efficiently

---

## Alternative 1: Server-Side In-Memory Token Cache
**How it works:** Server stores tokens in memory (Python dict), indexed by session ID

### Implementation:
```python
# In server.py
token_cache = {}  # session_id -> bearer_token

def cache_token(session_id: str, bearer_token: str, ttl_seconds: int = 3600):
    """Cache token in memory with expiration"""
    expiry = time.time() + ttl_seconds
    token_cache[session_id] = (bearer_token, expiry)

def get_cached_token(session_id: str) -> Optional[str]:
    """Retrieve token from cache if not expired"""
    if session_id in token_cache:
        token, expiry = token_cache[session_id]
        if time.time() < expiry:
            return token
        else:
            del token_cache[session_id]  # Clean up expired
    return None
```

### Pros:
✅ Cleaner UI (session ID instead of full token)
✅ Slightly faster (no token transmission)
✅ Better for batch operations (many requests in sequence)

### Cons:
❌ **Security Risks:**
- Token stored in server memory (could be dumped)
- Server restart loses all tokens (users must re-authenticate)
- Server process compromise exposes all cached tokens
- Memory dump/crash dump could leak tokens
- Server logs might accidentally log session IDs

❌ **Complexity:**
- Need session management
- Need token expiration logic
- Need cleanup of expired tokens
- Need to handle server restarts gracefully

---

## Alternative 2: Encrypted File Storage
**How it works:** Server stores encrypted tokens in file, decrypts on use

### Pros:
✅ Survives server restarts
✅ Can implement proper token lifecycle

### Cons:
❌ **Major Security Risks:**
- Encryption key must be stored somewhere (key management problem)
- If server is compromised, attacker gets all tokens
- File permissions issues (who can read the file?)
- Audit trail complexity
- GDPR/compliance issues (storing auth credentials)

❌ **Performance:**
- Disk I/O for every token retrieval
- Encryption/decryption overhead

❌ **Not Recommended for OAuth tokens**

---

## Alternative 3: Database Storage
**How it works:** Store tokens in SQLite/PostgreSQL

### Cons:
❌ All the security issues of file storage
❌ Additional infrastructure complexity
❌ Database can be compromised
❌ Even worse for compliance
❌ **Strongly Not Recommended**

---

## Recommended Approach: Enhanced Client-Side with Token Aliases

### Best of Both Worlds Strategy

**How it works:**
1. Client stores token
2. Client creates a short alias (e.g., "work-token-1")
3. Client passes alias in requests
4. **MCP server does NOT store tokens**
5. MCP client-side config maps alias to actual token

### Implementation in Claude Desktop Config:

```json
{
  "mcpServers": {
    "omada-server": {
      "command": "python.exe",
      "args": ["server.py"],
      "env": {
        "PYTHONPATH": "...",
        "BEARER_TOKEN_work": "eyJ0eXAiOi...<full token>",
        "BEARER_TOKEN_dev": "eyJ0eXAiOi...<another token>",
        "BEARER_TOKEN_prod": "eyJ0eXAiOi...<prod token>"
      }
    }
  }
}
```

### Update MCP Functions to Support Aliases:

```python
def resolve_bearer_token(token_or_alias: str) -> str:
    """
    Resolve a token alias to actual bearer token.

    If token starts with 'env:', look it up in environment.
    Otherwise, assume it's the actual token.
    """
    if token_or_alias.startswith('env:'):
        # e.g., "env:work" -> os.getenv("BEARER_TOKEN_work")
        alias = token_or_alias[4:]  # Remove "env:" prefix
        env_var = f"BEARER_TOKEN_{alias}"
        token = os.getenv(env_var)
        if not token:
            raise ValueError(f"Token alias '{alias}' not found in environment (expected {env_var})")
        return token
    else:
        # Assume it's the actual token
        return token_or_alias
```

### Usage:
```python
# Instead of passing full token:
bearer_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."

# Pass alias:
bearer_token="env:work"
```

### Pros:
✅ **Secure:**
- Token still stored on client side (in config)
- Server never stores tokens
- Config file can be encrypted by OS
- Token only loaded when server starts (in env vars)

✅ **Clean UI:**
- User types "env:work" instead of long token
- Easy to switch between tokens (work/dev/prod)

✅ **Performance:**
- Token lookup is just env var access (very fast)
- No network overhead reduction, but cleaner

### Cons:
❌ Still requires restart to switch tokens (but that's acceptable)
❌ Token visible in process environment (but better than alternatives)

---

## Current Architecture Analysis

Looking at your current code:

```python
async def query_omada_entity(..., bearer_token: str = None):
    if bearer_token:
        # Use provided token
    else:
        # Acquire new token via oauth_mcp_server
```

This is **already secure** because:
- ✅ Server doesn't store tokens
- ✅ Optional `bearer_token` parameter
- ✅ Falls back to acquiring new token if not provided

---

## Security Best Practices Ranking

**From Most Secure to Least Secure:**

1. ✅ **Current approach (client-side token, pass every time)** ← **RECOMMENDED**
2. ✅ **Client-side with environment variable aliases** ← **RECOMMENDED ENHANCEMENT**
3. ⚠️ Server-side in-memory cache (acceptable for short-lived sessions, single-user scenarios)
4. ❌ Encrypted file storage (not recommended)
5. ❌ Database storage (strongly discouraged)
6. ❌ Plain text file (never do this)

---

## Final Recommendation

### For Your Use Case:

**Keep your current client-side approach, but enhance it:**

1. **Immediate:** Keep passing tokens from Claude Desktop (no change needed)
   - Most secure
   - Already working
   - Zero security risk

2. **Enhancement (Optional):** Implement token alias support
   - Add `resolve_bearer_token()` helper function
   - Update all functions to call this helper
   - Users can put tokens in Claude Desktop config env vars
   - Users pass "env:work" instead of full token

3. **For Development/Testing Only:** Short-lived in-memory cache
   - Add a `cache_token()` function with 5-minute TTL
   - Only enable via environment variable `ENABLE_TOKEN_CACHE=true`
   - Add big warning in documentation
   - Never use in production

### Implementation Priority:

```
Priority 1: Keep current approach (DONE - already secure)
Priority 2: Add token alias support (optional improvement for UX)
Priority 3: Document security model (this document)
Priority 99: In-memory cache (only if absolutely needed for testing)
```

---

## Answer to Your Question

**Q: "What is best for security and performance?"**

**A: Client-side token storage (your current approach) is best for security.**

**Performance impact is negligible:**
- A 2KB bearer token adds <1ms to request time
- HTTP/2 compression reduces overhead
- Security benefit far outweighs tiny performance cost

**Do NOT store tokens on the server.** The security risks are not worth the marginal performance gain.

---

## OAuth2 Token Lifecycle Best Practices

Instead of long-lived tokens, consider:

1. **Short-lived access tokens** (1 hour)
2. **Refresh tokens** for getting new access tokens
3. **Re-authenticate when expired** (via oauth_mcp_server)

Your `oauth_mcp_server` handles this well with device code flow.

---

## Summary

✅ **Keep your current approach** - it's secure and correct

✅ **Optional enhancement:** Add environment variable token aliases for UX

❌ **Do not store tokens on the server** - security risk outweighs benefits

The "long bearer token string" is a minor UI inconvenience, but it's the **security-correct** approach. Users can use copy/paste or consider the token alias enhancement.

**Security > Convenience** when dealing with authentication tokens.
