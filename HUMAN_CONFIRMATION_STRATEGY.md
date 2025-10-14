# Human Confirmation Strategy for Approval Decisions

## The Challenge

When using MCP tools to make approval decisions in Omada, we need to ensure that a human explicitly confirms critical actions like APPROVE or REJECT before they're executed.

## Current State

The `make_approval_decision` function currently:
- ✅ Requires all parameters (impersonate_user, survey_id, survey_object_key, decision)
- ✅ Validates the decision is either APPROVE or REJECT
- ❌ Does NOT have explicit human confirmation step
- ❌ Executes immediately when called by Claude

## The Problem

Claude Desktop can call MCP tools automatically. Without proper safeguards:
- Claude might approve/reject requests without explicit user consent
- User might not review the full context before decision
- Risk of accidental bulk approvals
- Compliance/audit concerns

## Solution Options

### Option 1: Prompt-Based Confirmation (RECOMMENDED)

Use the MCP prompt workflow to guide Claude to ask for explicit confirmation before calling the approval function.

#### Implementation in prompts.py:

```python
@mcp.prompt()
def approve_requests_workflow():
    return """I'll help you review and approve pending access requests in Omada.

**Step 1: Get Pending Approvals**
[... retrieve approvals ...]

**Step 2: Review Details**
[... show approval details ...]

**Step 3: Get Explicit Confirmation**
IMPORTANT: Before I call make_approval_decision, I will:
1. Show you the full approval details:
   - Requester name and email
   - Resource being requested
   - Justification/reason
   - Current workflow step
2. Ask you explicitly: "Do you want to APPROVE or REJECT this request?"
3. Wait for your explicit response (APPROVE/REJECT/CANCEL)
4. Only then call make_approval_decision

**Security Note:**
- I will NEVER approve requests without your explicit confirmation
- I will show you all details before asking for confirmation
- You must type APPROVE or REJECT explicitly
- If you're uncertain, I can show more details or you can CANCEL
"""
```

#### Usage Pattern:

```
Claude: I found 1 pending approval:

Requester: John Doe (john.doe@company.com)
Resource: VPN Access - Engineering Group
Reason: "Need VPN access for remote development work"
Workflow Step: ManagerApproval

Do you want to APPROVE or REJECT this request?
Type: APPROVE, REJECT, or CANCEL

User: APPROVE

Claude: ✅ Confirmed. Calling make_approval_decision to approve this request...
[calls the function]
```

**Pros:**
- ✅ Explicit user confirmation required
- ✅ No code changes to server needed
- ✅ Works with current MCP architecture
- ✅ Audit trail in conversation
- ✅ User sees full context before deciding

**Cons:**
- ⚠️ Relies on Claude following prompt instructions
- ⚠️ No technical enforcement (Claude could theoretically bypass)

---

### Option 2: Confirmation Parameter

Add a required confirmation parameter to the function.

#### Implementation:

```python
async def make_approval_decision(
    impersonate_user: str,
    survey_id: str,
    survey_object_key: str,
    decision: str,
    user_confirmed: bool = False,  # NEW: Must be True
    confirmation_token: str = None,  # NEW: Optional verification
    ...
) -> str:
    """
    Make an approval decision with mandatory human confirmation.

    CRITICAL SECURITY REQUIREMENT:
    This function will REFUSE to execute unless user_confirmed=True.
    Claude must explicitly ask the user for confirmation before setting this to True.

    NEW REQUIRED PARAMETERS:
        user_confirmed: Must be True to execute. Claude must get explicit user confirmation.
                       PROMPT: Show full request details, then ask:
                       "Type CONFIRM to approve/reject this request"
        confirmation_token: Optional random token shown to user that they must type back
    """

    # Enforce confirmation
    if not user_confirmed:
        return json.dumps({
            "status": "confirmation_required",
            "message": "Human confirmation required before executing approval decision",
            "instructions": "Please review the request details and provide explicit confirmation",
            "error_type": "ConfirmationRequired"
        }, indent=2)

    # Optional: Verify confirmation token
    if confirmation_token:
        # Store expected token in conversation context or session
        # Verify it matches what user typed
        pass

    # Proceed with approval...
```

**Usage Pattern:**

```python
# Claude would need to:
# 1. Show details
# 2. Ask for confirmation
# 3. Call with user_confirmed=True only after user confirms

await make_approval_decision(
    impersonate_user="approver@company.com",
    survey_id="abc-123",
    survey_object_key="def-456",
    decision="APPROVE",
    user_confirmed=True  # Only after user explicitly confirms
)
```

**Pros:**
- ✅ Technical enforcement (function refuses without confirmation)
- ✅ Clear API contract
- ✅ Can add confirmation token for extra security

**Cons:**
- ⚠️ Requires code changes to function signature
- ⚠️ Claude must be instructed to always set this parameter correctly
- ⚠️ Backward compatibility break for existing callers

---

### Option 3: Two-Step Approval Process

Split approval into two functions: prepare and execute.

#### Implementation:

```python
@mcp.tool()
async def prepare_approval_decision(
    impersonate_user: str,
    survey_id: str,
    survey_object_key: str,
    decision: str,
    ...
) -> str:
    """
    Prepare an approval decision and return a confirmation token.
    Does NOT execute the approval - just validates and returns details.
    """
    # Validate all parameters
    # Fetch additional details about the request
    # Generate a unique confirmation token
    confirmation_token = generate_token()

    return json.dumps({
        "status": "prepared",
        "confirmation_token": confirmation_token,
        "expires_in_seconds": 300,  # 5 minutes
        "request_details": {
            "requester": "John Doe",
            "resource": "VPN Access",
            "reason": "Remote work",
            ...
        },
        "message": "Review the details above. If correct, call execute_approval_decision with this token."
    })


@mcp.tool()
async def execute_approval_decision(
    confirmation_token: str,
    bearer_token: str = None
) -> str:
    """
    Execute a previously prepared approval decision.
    Requires the confirmation token from prepare_approval_decision.
    """
    # Look up the prepared decision by token
    # Verify token hasn't expired
    # Execute the approval
    # Invalidate the token

    return json.dumps({
        "status": "success",
        "decision_executed": True,
        ...
    })
```

**Usage Pattern:**

```
Step 1: Prepare
result = await prepare_approval_decision(...)
# Shows: "Token: XYZ123, expires in 5 minutes"

Step 2: User reviews and confirms
User: "Yes, execute the approval"

Step 3: Execute
result = await execute_approval_decision(confirmation_token="XYZ123")
```

**Pros:**
- ✅ Technical enforcement (can't execute without prepare)
- ✅ Time-limited tokens (expire after 5 minutes)
- ✅ Clear two-phase commit pattern
- ✅ Can store full context with token
- ✅ Can audit: "prepared at X, executed at Y"

**Cons:**
- ⚠️ More complex (two functions instead of one)
- ⚠️ Need token storage/management
- ⚠️ Need token cleanup for expired tokens

---

### Option 4: Dry Run Mode

Add a dry_run parameter that shows what would happen without executing.

#### Implementation:

```python
async def make_approval_decision(
    impersonate_user: str,
    survey_id: str,
    survey_object_key: str,
    decision: str,
    dry_run: bool = True,  # Default to dry run!
    ...
) -> str:
    """
    Make an approval decision.

    SAFETY FEATURE:
    - dry_run=True (default): Shows what would happen, doesn't execute
    - dry_run=False: Actually executes the decision

    Claude should ALWAYS call with dry_run=True first to show the user
    what will happen, then call again with dry_run=False only after
    explicit user confirmation.
    """

    if dry_run:
        return json.dumps({
            "status": "dry_run",
            "message": "DRY RUN - No changes made",
            "would_execute": {
                "decision": decision,
                "survey_id": survey_id,
                "impact": "This would APPROVE/REJECT the access request"
            },
            "next_step": "To actually execute, call with dry_run=False"
        })

    # Actually execute the approval
    ...
```

**Pros:**
- ✅ Safe by default (dry_run=True)
- ✅ User sees preview before execution
- ✅ Simple to implement

**Cons:**
- ⚠️ User might forget dry_run=False
- ⚠️ Two calls needed for every approval

---

## Recommended Approach: Hybrid Strategy

Combine multiple approaches for defense in depth:

### 1. Update prompts.py (Immediate - No Code Changes)

```python
@mcp.prompt()
def approve_requests_workflow():
    return """
...

**CRITICAL SECURITY PROTOCOL:**

Before calling make_approval_decision, I MUST:

1. Display complete request details in a formatted summary:
   ---
   APPROVAL DECISION SUMMARY
   Requester: [Name] ([Email])
   Resource: [Resource Name]
   Reason: [Justification]
   Decision: [APPROVE/REJECT]
   ---

2. Ask explicitly: "Type APPROVE, REJECT, or CANCEL"

3. Wait for your response

4. Only call make_approval_decision after receiving your explicit APPROVE or REJECT

I will NEVER call make_approval_decision without completing all steps above.
"""
```

### 2. Add Confirmation to Function Docstring (Immediate - Documentation Only)

```python
async def make_approval_decision(...):
    """
    ...

    SECURITY WARNING FOR CLAUDE:
    You MUST get explicit human confirmation before calling this function.

    Before calling:
    1. Show the user: requester name, resource, reason, decision
    2. Ask: "Type APPROVE or REJECT to confirm"
    3. Wait for explicit user response
    4. Only then call this function

    This function performs a PERMANENT action that affects access control.
    """
```

### 3. Optional: Add dry_run Parameter (Code Change - High Impact)

Add dry_run with default=True for maximum safety.

---

## Implementation Plan

### Phase 1: Immediate (No Code Changes)

1. ✅ Update `approve_requests_workflow` in prompts.py
2. ✅ Add security warnings to function docstrings
3. ✅ Update workflow documentation

### Phase 2: Enhanced Safety (Code Changes)

1. Add `dry_run=True` default parameter
2. Add `user_confirmed` parameter
3. Return rich preview in dry_run mode

### Phase 3: Advanced (If Needed)

1. Implement two-step prepare/execute pattern
2. Add confirmation tokens
3. Add audit logging for confirmations

---

## Testing the Confirmation Flow

### Test Script:

```python
# Test 1: Prompt should guide Claude to ask for confirmation
User: "I want to approve some requests"
Claude: [Shows workflow, gets approvals, displays details]
Claude: "Do you want to APPROVE or REJECT this request for John Doe?"
User: "APPROVE"
Claude: "Confirmed. Executing approval..." [calls function]

# Test 2: User should be able to cancel
Claude: "Do you want to APPROVE or REJECT?"
User: "CANCEL"
Claude: "Cancelled. No action taken."

# Test 3: Claude should not proceed without confirmation
# (This relies on prompt instructions)
```

---

## Audit Trail

Ensure confirmations are logged:

```python
logger.info(f"Approval decision: decision={decision}, survey_id={survey_id}, "
            f"user={impersonate_user}, confirmed_by_human=True")
```

---

## Summary

**Best Approach for Your Use Case:**

1. **Immediate:** Update `approve_requests_workflow` prompt to explicitly require confirmation
2. **Short-term:** Add `dry_run=True` as default parameter
3. **Long-term:** Consider two-step prepare/execute pattern for highest security

The prompt-based approach gives you immediate protection without code changes, while the dry_run parameter provides technical enforcement.

**Key Principle:**
> "Make it easy to review, hard to accidentally execute, and impossible to miss."

All approval decisions should require explicit human confirmation with full context displayed before execution.
