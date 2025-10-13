# Prompt Updates Summary

## Changes Made to prompts.py

Updated the workflow prompts to clarify the critical distinction between **context** (business context ID) and **reason** (justification text) in access requests.

---

## Updated Prompts

### 1. request_access_workflow

**Changes:**
- Added explicit Step 2 explanation about calling `get_identity_contexts`
- Added "IMPORTANT" section clarifying what "context" means
- Split Step 4 into two clear sub-sections:
  - **context** (REQUIRED): Business context ID from get_identity_contexts
  - **reason** (REQUIRED): Justification text
- Added examples for both fields

**Key Clarifications:**
```
IMPORTANT: "Context" means organizational context (department, cost center, team, etc.)
- NOT the reason or justification for access
- These come from get_identity_contexts tool
- You must select one context ID from the list returned
```

**Example Usage Now Shown:**
- context: `"6dd03400-ddb5-4cc4-bfff-490d94b195a9"` (from get_identity_contexts)
- reason: `"Need to access project website that requires VPN connection"` (free text)

---

### 2. bulk_access_request_workflow

**Changes:**
- Updated Step 1 to explicitly mention `get_identities_for_beneficiary` tool
- Added new Step 2 specifically for getting contexts via `get_identity_contexts`
- Added "IMPORTANT" section explaining context
- Split Step 4 into two clear sub-sections with detailed explanations
- Added note that each user may have different available contexts

**Key Clarifications:**
```
IMPORTANT: "Context" means organizational context
- Examples: Department, Cost Center, Team, Project
- NOT the reason/justification for access
- Each user may have different contexts available
- Must select appropriate context for each user
```

**Example Usage Now Shown:**
- context: `"6dd03400-ddb5-4cc4-bfff-490d94b195a9"` (from get_identity_contexts, per user)
- reason: `"New team member onboarding - requires VPN access"` (can be same for all)

---

## Problem Solved

### Before Update:
Claude Desktop would confuse "context" with "reason" because:
- The prompt didn't explicitly distinguish between the two
- Users would see "Business context:" and provide text like "Need to access project website"
- This caused errors because context expects a GUID, not free text

### After Update:
Claude Desktop now understands:
1. Must call `get_identity_contexts` first to get available contexts
2. Context = ID from that list (GUID format)
3. Reason = separate free-text justification
4. Both are required but serve different purposes

---

## Supporting Documentation

### CONTEXT_VS_REASON.md
Created comprehensive guide explaining:
- What context is (organizational dimension)
- What reason is (justification text)
- How to get each one
- Common mistakes to avoid
- Complete workflow example
- Quick reference table

### Key Sections:
1. **Clear definitions** with examples
2. **Common mistakes** (❌ WRONG vs ✅ CORRECT)
3. **Complete workflow example** showing all 4 steps
4. **Quick reference table** for easy lookup

---

## Testing

To verify the prompts work correctly:

```bash
# Restart the MCP server
# You should see:
Registered 10 MCP prompts: request_access_workflow, approve_requests_workflow, ...

# In Claude Desktop, invoke the prompt:
"Use the request access workflow"

# Claude should now:
1. Ask for email and bearer token
2. Look up the user
3. Call get_identity_contexts and show the list
4. Ask you to SELECT a context from the list (not provide free text)
5. Ask for resources
6. Ask for reason (free text justification)
7. Create the access request with both context ID and reason
```

---

## Impact

These updates will:
- ✅ Prevent confusion between context and reason
- ✅ Guide Claude to call get_identity_contexts properly
- ✅ Ensure correct parameters are passed to create_access_request
- ✅ Reduce errors from invalid context values
- ✅ Provide clear examples of what each field should contain

---

## Files Modified

1. **prompts.py** - Updated two workflow prompts
   - Lines 20-65: request_access_workflow
   - Lines 297-356: bulk_access_request_workflow

2. **CONTEXT_VS_REASON.md** - New documentation file
   - Comprehensive guide explaining the distinction
   - Examples and common mistakes
   - Complete workflow demonstration

3. **PROMPT_UPDATES_SUMMARY.md** - This file
   - Summary of changes
   - Problem/solution description
   - Testing instructions

---

## Next Steps

1. Restart the omada_mcp_server to load the updated prompts
2. Test the request_access_workflow in Claude Desktop
3. Verify that Claude:
   - Calls get_identity_contexts
   - Shows the context list
   - Asks user to select from the list
   - Separates reason as a different field
4. Share CONTEXT_VS_REASON.md with users who need to understand the distinction

---

## Summary

The prompts now clearly distinguish between:
- **context** = Business context ID from get_identity_contexts (GUID)
- **reason** = Justification text (free text)

This prevents the common mistake of providing free text when a context ID is required!
