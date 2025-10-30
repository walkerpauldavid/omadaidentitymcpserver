# How to Use MCP Prompts in Claude Desktop

## Important: MCP Prompts Are NOT Slash Commands!

MCP prompts **do not work** like slash commands (e.g., `/compare_identities_workflow`). They are invoked differently.

## How MCP Prompts Work

MCP prompts are **available to Claude** as reusable workflow templates that Claude can invoke when appropriate. They work in one of two ways:

### Method 1: Ask Claude Naturally (Recommended)

Simply ask Claude about the task you want to do. Claude will automatically choose the appropriate prompt workflow.

**Examples:**

```
You: "I want to compare two identities"
Claude: (automatically uses compare_identities_workflow prompt)

You: "Help me request access to a resource"
Claude: (automatically uses request_access_workflow prompt)

You: "I need to approve some pending requests"
Claude: (automatically uses approve_requests_workflow prompt)
```

### Method 2: Explicitly Ask for the Prompt

You can ask Claude to use a specific prompt by name:

**Examples:**

```
You: "Use the compare_identities_workflow"
You: "Show me the compare identities workflow"
You: "I want to use the identity comparison workflow"
```

## Available Prompts in omada_mcp_server

Here are all 11 registered prompts and how to invoke them:

### 1. **request_access_workflow**
**Ask:** "Help me request access" or "I want to request a resource"
**Purpose:** Guide through requesting access to resources

### 2. **approve_requests_workflow**
**Ask:** "I need to approve requests" or "Show me pending approvals"
**Purpose:** Guide through reviewing and approving access requests

### 3. **search_identity_workflow**
**Ask:** "How do I search for users?" or "Find an identity"
**Purpose:** Explains different ways to search for identities

### 4. **review_assignments_workflow**
**Ask:** "Review someone's access" or "Check user assignments"
**Purpose:** Guide through reviewing user's resource assignments and compliance

### 5. **authentication_workflow**
**Ask:** "How do I get a token?" or "Help me authenticate"
**Purpose:** Guide through OAuth device code authentication

### 6. **troubleshooting_workflow**
**Ask:** "I'm having issues" or "Troubleshoot errors"
**Purpose:** Common solutions to MCP/Omada issues

### 7. **bulk_access_request_workflow**
**Ask:** "Request access for multiple users" or "Bulk access requests"
**Purpose:** Guide through requesting access for multiple users at once

### 8. **compliance_audit_workflow**
**Ask:** "Audit compliance violations" or "Review compliance"
**Purpose:** Guide through auditing compliance violations across users

### 9. **resource_discovery_workflow**
**Ask:** "What resources are available?" or "Discover resources"
**Purpose:** Guide through discovering and exploring resources

### 10. **identity_context_workflow**
**Ask:** "What are contexts?" or "Explain identity contexts"
**Purpose:** Explains what contexts are and how to use them

### 11. **compare_identities_workflow** ✨ NEW
**Ask:** "Compare two identities" or "Compare two users"
**Purpose:** Detailed side-by-side comparison of two identities

## How to Verify Prompts Are Loaded

After restarting Claude Desktop, check the console or logs for:
```
Registered 11 MCP prompts: request_access_workflow, approve_requests_workflow, ...
```

This confirms that all prompts are available to Claude.

## Testing a Prompt

Try this in Claude Desktop:

```
You: "I want to compare two identities"
```

Claude should respond with the full compare_identities_workflow prompt text, which includes:
- Step-by-step workflow
- What data will be retrieved
- What analysis will be performed
- What you need to provide

Then you can provide the user information and Claude will execute the workflow.

## Why Prompts Don't Appear as Slash Commands

- MCP prompts are **templates for Claude**, not user commands
- They guide Claude's behavior and responses
- They provide context and structured workflows
- Claude invokes them automatically based on user intent
- They're not meant to be directly invoked by users with `/` syntax

## Difference from Slash Commands

| Slash Commands | MCP Prompts |
|----------------|-------------|
| User types `/command` | User asks naturally or requests by name |
| Directly invokes action | Provides workflow template to Claude |
| Part of Claude Desktop UI | Part of MCP server capability |
| Visible in command list | Claude knows about them internally |

## Additional Notes

- Prompts are registered when the MCP server starts
- They're available throughout the conversation
- Claude can switch between different prompts as needed
- Prompts help Claude provide consistent, structured workflows
- You can have multiple prompts active in a conversation

## Summary

**Don't type:** `/compare_identities_workflow`

**Instead, ask:** "Compare two identities" or "I want to use the compare identities workflow"

Claude will automatically invoke the appropriate prompt and guide you through the workflow!
