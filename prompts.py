# prompts.py - MCP Prompts for Omada Identity Server
#
# Prompts help guide Claude through complex workflows by providing
# templates and examples for common Omada operations.

def register_prompts(mcp):
    """Register all MCP prompts with the FastMCP server."""

    @mcp.prompt()
    def request_access_workflow():
        """
        Guide user through requesting access to a resource in Omada.

        This prompt helps with the complete access request workflow:
        1. Find the user's identity
        2. Get available contexts
        3. List requestable resources
        4. Create the access request
        """
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

    @mcp.prompt()
    def approve_requests_workflow():
        """
        Guide user through approving pending access requests in Omada.

        This prompt helps with the approval workflow:
        1. Get pending approvals
        2. Review approval details
        3. Make approval decision
        """
        return """I'll help you review and approve pending access requests in Omada.

**Step 1: Get Pending Approvals**
First, I'll retrieve all access requests waiting for your approval.

Required:
- Email address to impersonate (the approver)
- Bearer token

Optional:
- Workflow step filter (ManagerApproval, ResourceOwnerApproval, SystemOwnerApproval)

**Step 2: Review Details**
I'll show you the approval details including:
- Who requested access
- What resource they're requesting
- The reason for the request
- Workflow step information

**Step 3: Make Decision**
For each approval, you can:
- APPROVE the request
- REJECT the request

I'll need:
- Survey ID (from the approval details)
- Survey Object Key (from the approval details)
- Your decision (APPROVE or REJECT)

Let's begin! Please provide:
1. Your email address (as approver)
2. Your bearer token
"""

    @mcp.prompt()
    def search_identity_workflow():
        """
        Guide user through searching for identities in Omada.

        This prompt provides examples of different search methods.
        """
        return """I'll help you search for identities in the Omada system.

**Search Methods:**

**1. Search by Email** (most common)
- Field: EMAIL
- Example: EMAIL eq 'user@domain.com'

**2. Search by Name**
- Field: FIRSTNAME and/or LASTNAME
- Example: FIRSTNAME eq 'John' and LASTNAME eq 'Smith'
- Supports operators: eq, contains, startswith

**3. Search by Department**
- Field: DEPARTMENT
- Example: DEPARTMENT contains 'Engineering'

**4. Search by Employee ID**
- Field: EMPLOYEEID
- Example: EMPLOYEEID eq 'EMP12345'

**Important Field Names (use EXACTLY as shown):**
- EMAIL (not "email", "MAIL", or "EMAILADDRESS")
- FIRSTNAME (not "firstname" or "first_name")
- LASTNAME (not "lastname" or "last_name")
- DISPLAYNAME, EMPLOYEEID, DEPARTMENT, STATUS

**What would you like to search for?**
Provide:
1. The search criteria (field and value)
2. Your bearer token
"""

    @mcp.prompt()
    def review_assignments_workflow():
        """
        Guide user through reviewing a user's resource assignments and compliance.

        This prompt helps with:
        1. Finding the user's identity
        2. Getting their calculated assignments
        3. Reviewing compliance and violations
        """
        return """I'll help you review a user's resource assignments and compliance status in Omada.

**What This Shows:**
- All resources assigned to the user
- Compliance status (APPROVED, NOT APPROVED, etc.)
- Violation details if any
- Account information
- Resource details including system and type

**Optional Filters:**
- Resource Type Name (e.g., "Active Directory - Security Group")
- Compliance Status (e.g., "NOT APPROVED", "APPROVED")

**Step 1: Find the User**
First, I need to identify the user. I can search by:
- Email address
- Employee ID
- Name

**Step 2: Get Assignments**
I'll retrieve their calculated assignments with full details.

**Step 3: Review Results**
I'll show you:
- Compliant assignments
- Non-compliant assignments with violation reasons
- Resource and account details

To begin, please provide:
1. How to identify the user (email, employee ID, or name)
2. Your bearer token
3. Optional: Resource type or compliance status filter
"""

    @mcp.prompt()
    def authentication_workflow():
        """
        Guide user through the OAuth device code authentication flow.

        This prompt explains how to get a bearer token.
        """
        return """I'll guide you through getting an authentication token using Device Code flow.

**Authentication Steps:**

**Using oauth_mcp_server:**

1. **Start Device Authentication**
   Call: start_device_auth()
   This gives you:
   - A user code (e.g., "A1B2C3D4")
   - A verification URL (https://microsoft.com/devicelogin)
   - Device code (used internally)

2. **Complete Authentication in Browser**
   - Open the verification URL in your browser
   - Enter the user code when prompted
   - Sign in with your Microsoft credentials
   - Approve the permissions

3. **Complete Device Authentication**
   Call: complete_device_auth()
   This returns your bearer token

4. **Use the Token**
   Pass the bearer token to any Omada function:
   Example: `get_pending_approvals(impersonate_user="user@domain.com", bearer_token="eyJ0...")`

The bearer token:
- Stays in the conversation context
- No need to save to files
- Valid for ~1 hour
- Use it for all subsequent operations

**Ready to authenticate?**
Type: "start device authentication"
"""

    @mcp.prompt()
    def troubleshooting_workflow():
        """
        Common troubleshooting tips for Omada MCP operations.
        """
        return """Here are solutions to common issues:

**Issue: "Missing bearer_token parameter"**
Solution: All Omada functions require authentication. Use oauth_mcp_server to get a token:
1. Run: start_device_auth()
2. Complete auth in browser
3. Run: complete_device_auth()
4. Use the returned token in your Omada function calls

**Issue: "Could not find identity for email"**
Solution: Check that:
- Email address is correct and complete
- Field name is "EMAIL" (all caps)
- User exists in Omada system

**Issue: "No resources found"**
Solution: This could mean:
- User doesn't have permission to request any resources
- Filters are too restrictive (try removing filters)
- Context or system ID is incorrect

**Issue: "Invalid entity type"**
Solution: Valid entity types are:
- Identity, Resource, Role, Account, Application, System, CalculatedAssignments, AssignmentPolicy

**Issue: "Authentication failed - token may be expired"**
Solution: Tokens expire after ~1 hour. Get a new token:
1. Run: complete_device_auth() (if you've already started auth)
2. Or start fresh with: start_device_auth()

**Issue: Field Names Not Working**
Solution: Omada field names are UPPERCASE and specific:
- Use "EMAIL" not "email", "MAIL", or "EMAILADDRESS"
- Use "FIRSTNAME" not "firstname" or "FirstName"
- Use "LASTNAME" not "lastname" or "LastName"

**Still having issues?**
Check the logs:
- Log file location shown at startup
- Set LOG_LEVEL_<function_name>=DEBUG in .env for detailed logs
"""

    print("✅ Registered 6 MCP prompts: request_access_workflow, approve_requests_workflow, search_identity_workflow, review_assignments_workflow, authentication_workflow, troubleshooting_workflow")
