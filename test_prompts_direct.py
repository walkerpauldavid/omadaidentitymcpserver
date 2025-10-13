#!/usr/bin/env python3
"""
Direct test script for MCP Prompts - calls prompt functions directly
"""

import sys

def test_prompt(prompt_name):
    """Test a specific prompt by importing and calling it."""

    # Import the prompts module
    from prompts import register_prompts
    from mcp.server.fastmcp.server import FastMCP

    # Create MCP server and register prompts
    mcp = FastMCP("TestServer")

    # Define all prompt functions inline so we can call them
    prompt_functions = {}

    # Define each prompt as a function
    def request_access_workflow():
        return """I'll help you request access to resources in Omada. This workflow involves several steps:

**Step 1: Identify the User**
First, I need to identify who is requesting access. I'll look up the user by email.

Required information:
- Email address of the person requesting access
- Bearer token for authentication

**Step 2: Get User's Contexts**
Next, I'll retrieve the business contexts available to this user (like department, cost center, etc.)

**Step 3: List Available Resources**
Then I'll show you what resources this user can request access to.

Optional filters:
- System ID (to filter by specific system)
- Context ID (to filter by specific business context)

**Step 4: Create Access Request**
Finally, I'll create the access request with:
- Reason for access
- Business context
- Resource(s) to request
- Optional: Valid from/to dates

Let's get started! Please provide:
1. The email address of the person requesting access
2. Your bearer token (from oauth_mcp_server)
"""

    def bulk_access_request_workflow():
        return """I'll help you request access for multiple users at once in Omada.

**Bulk Access Request Workflow:**

**Step 1: Find Beneficiaries**
First, I'll get a list of identities that can be beneficiaries in access requests.

Required:
- Email address to impersonate
- Bearer token

Optional pagination:
- Page number (e.g., 1, 2, 3)
- Rows per page (e.g., 10, 20, 50)

**Step 2: Review Identity List**
I'll show you all available identities with:
- Display name
- Identity ID
- First and last name
- Available contexts

**Step 3: Find Requestable Resources**
For selected users, I'll find what resources they can request.
You can filter by:
- System ID
- Context ID
- Resource name

**Step 4: Create Multiple Requests**
I'll create access requests for each selected user with:
- Same reason for all
- Same business context
- Same resources
- Optional: Same validity dates

**Benefits of Bulk Operations:**
- Save time when onboarding multiple users
- Ensure consistent access across teams
- Standardize access request reasons

Let's begin! Please provide:
1. Your email address (to impersonate)
2. Your bearer token
3. Optional: Pagination settings (page and rows)
"""

    def compliance_audit_workflow():
        return """I'll help you audit compliance violations in Omada.

**Compliance Audit Workflow:**

**Step 1: Define Audit Scope**
Choose how to identify users to audit:
- By department (e.g., DEPARTMENT contains 'Engineering')
- By status (e.g., STATUS eq 'ACTIVE')
- All users (use with caution on large datasets)

**Step 2: Get User Assignments**
For each user, I'll retrieve their calculated assignments including:
- Compliance status
- Violation details
- Resource assignments
- Account information

**Step 3: Filter Violations**
Focus on specific issues:
- Compliance Status filter: "NOT APPROVED", "VIOLATION", "APPROVED"
- Resource Type filter: e.g., "Active Directory - Security Group"

**Step 4: Review Results**
I'll provide a summary showing:
- Users with violations
- Type of violations
- Affected resources
- Violation descriptions

**Common Compliance Checks:**
- Segregation of Duties (SoD) violations
- Unauthorized access (NOT APPROVED)
- Expired assignments
- Missing approvals

**Important Notes:**
- This uses the GUID (UId) field, not the IdentityID field
- Results show detailed violation information
- Can be filtered by resource type for targeted audits

To begin, please provide:
1. Search criteria for users to audit
2. Email address to impersonate
3. Your bearer token
4. Optional: Compliance status filter (default: all statuses)
"""

    def identity_context_workflow():
        return """I'll help you understand and work with identity contexts in Omada.

**What are Identity Contexts?**
Contexts represent business dimensions like:
- Organizational units (departments, teams)
- Cost centers
- Projects
- Locations
- Other business hierarchies

**Why Contexts Matter:**
- Required for creating access requests
- Determine what resources are available
- Help route approvals to the right people
- Filter resources by business scope

**Working with Contexts:**

**Step 1: Get Contexts for an Identity**
I'll show all contexts available for a specific user.

Required:
- Identity ID (UId field - 32 character GUID, NOT the IdentityID field)
- Email address to impersonate
- Bearer token

**Step 2: Understanding Context Data**
Each context includes:
- Context ID (use this for access requests)
- Display name
- Context type

**Step 3: Using Contexts**
Contexts are used when:
- Creating access requests (required field)
- Filtering requestable resources
- Routing approvals through workflows

**Common Context Operations:**

1. **Find User's Contexts:**
   - Get identity UId from user lookup
   - Call get_identity_contexts
   - Review available contexts

2. **Filter Resources by Context:**
   - Use context_id parameter
   - Shows only resources available in that context

3. **Create Access Request:**
   - Select appropriate context
   - Provide context ID in request

**Important: Identity ID vs IdentityID**
- Use the "UId" field (32-character GUID like "e3e869c4-...")
- NOT the "IdentityID" field (like "ROBWOL")
- NOT the "Id" field (integer like 1006715)

Let's explore contexts! Please provide:
1. How to identify the user (email, employee ID, or name)
2. Your bearer token
"""

    # Map prompt names to functions
    prompt_functions = {
        "request_access_workflow": request_access_workflow,
        "bulk_access_request_workflow": bulk_access_request_workflow,
        "compliance_audit_workflow": compliance_audit_workflow,
        "identity_context_workflow": identity_context_workflow,
    }

    # List all available prompts if requested
    if prompt_name == "list":
        print(">> Available prompts:")
        print("=" * 80)
        for i, name in enumerate(prompt_functions.keys(), 1):
            print(f"{i:2d}. {name}")
        print("=" * 80)
        return

    # Display specific prompt
    if prompt_name in prompt_functions:
        print(f">> Prompt: {prompt_name}")
        print("=" * 80)
        print(prompt_functions[prompt_name]())
        print("=" * 80)
    else:
        print(f"Prompt '{prompt_name}' not found. Available prompts:")
        for name in prompt_functions.keys():
            print(f"  - {name}")

def main():
    if len(sys.argv) > 1:
        prompt_name = sys.argv[1]
        test_prompt(prompt_name)
    else:
        test_prompt("list")

if __name__ == "__main__":
    main()
