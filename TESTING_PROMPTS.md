# Testing MCP Prompts in omada_mcp_server

This guide explains how to test and use MCP prompts in the Omada MCP server.

## What Are MCP Prompts?

MCP Prompts are pre-defined workflow guides that help users complete complex tasks step-by-step. They provide:
- Structured instructions for multi-step operations
- Required and optional parameters
- Best practices and examples
- Troubleshooting tips

## Available Prompts

The omada_mcp_server now includes **10 prompts**:

### Original Prompts (1-6)
1. **request_access_workflow** - Guide for requesting access to resources
2. **approve_requests_workflow** - Guide for approving pending access requests
3. **search_identity_workflow** - Guide for searching identities in Omada
4. **review_assignments_workflow** - Guide for reviewing user assignments and compliance
5. **authentication_workflow** - Guide for OAuth device code authentication
6. **troubleshooting_workflow** - Common troubleshooting tips

### New Prompts (7-10)
7. **bulk_access_request_workflow** - Guide for requesting access for multiple users
8. **compliance_audit_workflow** - Guide for auditing compliance violations
9. **resource_discovery_workflow** - Guide for discovering and exploring resources
10. **identity_context_workflow** - Guide for understanding and using identity contexts

## How to Test Prompts

### Method 1: Using the Direct Test Script (Recommended)

```bash
# List all available prompts
python test_prompts_direct.py list

# View a specific prompt
python test_prompts_direct.py bulk_access_request_workflow
python test_prompts_direct.py compliance_audit_workflow
python test_prompts_direct.py identity_context_workflow
```

### Method 2: Through Claude Desktop (MCP Client)

1. **Start the MCP Server**: Make sure your omada_mcp_server is running and registered in Claude Desktop

2. **Use the Prompt**: In Claude Desktop, you can invoke prompts by saying:
   - "Use the bulk access request workflow"
   - "Show me the compliance audit workflow"
   - "I need help with identity contexts"

3. **Claude will display the prompt content** and guide you through the workflow

### Method 3: Programmatically via MCP Protocol

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# Connect to MCP server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # List all prompts
        prompts = await session.list_prompts()

        # Get a specific prompt
        result = await session.get_prompt("bulk_access_request_workflow")
```

## Testing Each New Prompt

### 1. Bulk Access Request Workflow

**Purpose**: Request access for multiple users at once

**Test Command**:
```bash
python test_prompts_direct.py bulk_access_request_workflow
```

**Expected Output**: Should display a step-by-step guide including:
- Finding beneficiaries
- Reviewing identity list
- Finding requestable resources
- Creating multiple requests

**Key Features**:
- Pagination support for large identity lists
- Bulk operations for efficiency
- Standardized access request reasons

### 2. Compliance Audit Workflow

**Purpose**: Audit compliance violations across users

**Test Command**:
```bash
python test_prompts_direct.py compliance_audit_workflow
```

**Expected Output**: Should display guidance on:
- Defining audit scope
- Getting user assignments
- Filtering violations
- Reviewing results

**Key Features**:
- Filter by department or status
- Focus on specific violation types
- Detailed violation information
- Uses UId field (not IdentityID)

### 3. Resource Discovery Workflow

**Purpose**: Discover and explore resources in Omada systems

**Test Command**:
```bash
python test_prompts_direct.py resource_discovery_workflow
```

**Expected Output**: Should explain:
- Resource types and organization
- Two discovery modes (admin vs requestable)
- Filtering options
- When to use which function

**Key Features**:
- Explains difference between admin and user-scoped views
- Guides on using correct function for the task
- Resource structure education

### 4. Identity Context Workflow

**Purpose**: Understand and work with identity contexts

**Test Command**:
```bash
python test_prompts_direct.py identity_context_workflow
```

**Expected Output**: Should cover:
- What contexts are
- Why they matter
- How to get and use contexts
- Field name clarifications (UId vs IdentityID vs Id)

**Key Features**:
- Clear explanation of context concept
- Context usage in access requests
- Critical field name guidance

## Verifying Prompts in Server

### Check Prompt Registration

When you start the server, you should see:
```
Registered 10 MCP prompts: request_access_workflow, approve_requests_workflow,
search_identity_workflow, review_assignments_workflow, authentication_workflow,
troubleshooting_workflow, bulk_access_request_workflow, compliance_audit_workflow,
resource_discovery_workflow, identity_context_workflow
```

### Check MCP Server Response

The server should respond to MCP `prompts/list` request with all 10 prompts available.

## Integration with Tools

Each prompt references specific MCP tools:

- **bulk_access_request_workflow** → `get_identities_for_beneficiary`, `get_resources_for_beneficiary`, `create_access_request`
- **compliance_audit_workflow** → `query_omada_identity`, `get_calculated_assignments_detailed`
- **resource_discovery_workflow** → `query_omada_resources`, `get_resources_for_beneficiary`
- **identity_context_workflow** → `get_identity_contexts`, `query_omada_identity`

## Best Practices for Using Prompts

1. **Start with prompts for complex workflows** - Don't try to remember all the steps
2. **Follow the step-by-step guidance** - Prompts break down complex operations
3. **Pay attention to field names** - Prompts emphasize critical distinctions (UId vs IdentityID)
4. **Use appropriate prompts** - Different prompts for different use cases

## Troubleshooting

### Prompt Not Found
- Ensure server is running latest code
- Check that prompts.py is properly imported
- Verify `register_prompts(mcp)` is called in server.py

### Prompt Content Not Displaying
- Check MCP client connection
- Verify prompt function returns a string
- Check for syntax errors in prompts.py

### Wrong Prompt Called
- Use exact prompt name from list
- Names use underscores (e.g., `bulk_access_request_workflow`)
- Case-sensitive in some clients

## Summary

You've successfully added 4 new prompts to the omada_mcp_server:

✅ **bulk_access_request_workflow** - For bulk user onboarding
✅ **compliance_audit_workflow** - For security auditing
✅ **resource_discovery_workflow** - For resource exploration
✅ **identity_context_workflow** - For context understanding

These prompts enhance the MCP server by providing guided workflows for complex operations, making it easier for users to interact with the Omada Identity system.

## Testing Checklist

- [ ] All 10 prompts show in list
- [ ] Each prompt returns formatted content
- [ ] Prompts reference correct tool names
- [ ] Field name guidance is clear (UId vs IdentityID)
- [ ] Server startup shows "Registered 10 MCP prompts"
- [ ] Prompts work in Claude Desktop (if available)
- [ ] Test scripts run without errors
