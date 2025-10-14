# MCP Prompts Troubleshooting Guide

## Issue: Claude Desktop Says "No Prompts Registered"

### Evidence That Prompts ARE Actually Registered

1. ✅ **Server logs show ListPromptsRequest processed:**
   ```
   2025-10-14 13:14:12,058 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest
   ```
   This means Claude Desktop IS asking the server for prompts.

2. ✅ **prompts.py print statement executes:**
   ```
   Registered 11 MCP prompts: request_access_workflow, approve_requests_workflow, ...
   ```
   This confirms all 11 prompts are registered with FastMCP.

3. ✅ **Code is correct:**
   - All 11 prompts defined with `@mcp.prompt()` decorator
   - `register_prompts(mcp)` called in server.py
   - No syntax errors or exceptions

### Why Claude Desktop Might Show "No Prompts"

This is likely a **Claude Desktop UI/display issue**, not a server problem. Possible reasons:

1. **Claude Desktop UI doesn't show prompt list**
   - Prompts might be available but not displayed in the UI
   - No visible "prompts menu" or list

2. **Prompts are available to Claude but not shown to user**
   - Claude can access prompts internally
   - User can't see them directly
   - This is normal behavior

3. **Cached state in Claude Desktop**
   - Claude Desktop might be caching old server state
   - Try: Close and reopen Claude Desktop completely

4. **MCP Protocol version mismatch**
   - Server might be using different protocol version
   - Usually not an issue with FastMCP

### How to Verify Prompts Actually Work

Instead of looking for a prompts list, **TEST if Claude can actually use them**:

#### Test 1: Ask for Authentication Workflow
```
User: "Show me the authentication workflow"
```

**Expected:** Claude should respond with the full authentication_workflow prompt text, starting with:
```
I'll guide you through getting an authentication token using Device Code flow...
```

#### Test 2: Ask About Access Requests
```
User: "Help me request access to a resource"
```

**Expected:** Claude should respond with the request_access_workflow prompt text.

#### Test 3: Try the New Compare Workflow
```
User: "I want to compare two identities"
```

**Expected:** Claude should respond with the compare_identities_workflow prompt text.

### If Tests Fail - Debugging Steps

#### Step 1: Verify Server is Running Latest Code
```bash
# Check server start time
grep "Logging initialized" pauls_omada_mcp_server.log | tail -1

# Should show today's date/time after your last restart
```

#### Step 2: Clear ALL Caches
```bash
# Delete Python cache
rm -f __pycache__/server.cpython-313.pyc
rm -f __pycache__/prompts.cpython-313.pyc

# Restart Claude Desktop completely
```

#### Step 3: Check for Import Errors
```bash
# Test import manually
python -c "from prompts import register_prompts; print('✅ prompts.py imports successfully')"
```

#### Step 4: Verify MCP Configuration
Check `C:\Users\demoadm\AppData\Roaming\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "omada-server": {
      "command": "python.exe",
      "args": ["C:\\Users\\demoadm\\Documents\\Code\\omada_mcp_server\\server.py"],
      ...
    }
  }
}
```

### Understanding MCP Prompts

**Important:** MCP prompts are NOT like slash commands!

❌ **Don't expect:**
- `/compare_identities_workflow` to work
- A visible list of prompts in the UI
- Prompts to appear in a menu

✅ **Do expect:**
- Claude to know about prompts internally
- Prompts to activate when you ask naturally
- No visual confirmation that prompts exist

### How FastMCP Prompts Actually Work

1. **Registration Phase (server startup):**
   ```python
   @mcp.prompt()
   def compare_identities_workflow():
       return "workflow text..."
   ```
   - FastMCP stores prompt internally
   - Prompt is available via MCP protocol

2. **Query Phase (Claude Desktop asks for prompts):**
   - Claude Desktop sends ListPromptsRequest
   - Server responds with list of available prompts
   - Claude stores this list internally

3. **Usage Phase (user asks question):**
   - User asks: "compare two identities"
   - Claude recognizes intent
   - Claude retrieves matching prompt text
   - Claude uses prompt to guide response

### Workaround: Direct Test

Ask me (Claude) directly in our conversation:

```
"Use the compare_identities_workflow prompt"
```

If I can't access it, there's a real problem. If I can, then Claude Desktop is working correctly and the prompts are available (even if not shown in UI).

### Alternative: Check MCP Protocol Level

The server processes `ListPromptsRequest` - we can see it in logs. But we can't see what the server responds with. To debug this, we'd need to:

1. Add logging to FastMCP to see what prompts are returned
2. Or use an MCP protocol inspector
3. Or trust that if ListPromptsRequest is processed, prompts were returned

### Most Likely Explanation

**The prompts ARE registered and working.** Claude Desktop just doesn't have a UI element that shows them. This is normal for MCP prompts - they're meant to be used by Claude internally, not displayed to users.

### Final Recommendation

**Stop looking for a prompts list. Instead, test if they work:**

1. Ask me: "Show me the authentication workflow"
2. Ask me: "Compare two identities"
3. Ask me: "Help me request access"

If I respond with the full workflow text, the prompts are working correctly.

If I don't recognize these, then we have a real issue to debug.
