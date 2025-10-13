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

**Step 2: Get User's Business Contexts**
I'll call get_identity_contexts to retrieve the business contexts available to this user.

IMPORTANT: "Context" means organizational context (department, cost center, team, etc.)
- NOT the reason or justification for access
- These come from get_identity_contexts tool
- You must select one context ID from the list returned
- Example contexts: "Sales Department", "Engineering Team", "Project Alpha"

**Step 3: List Available Resources**
Then I'll show you what resources this user can request access to.

Optional filters:
- System ID (to filter by specific system)
- Context ID (to filter resources by the business context selected)

**Step 4: Create Access Request**
Finally, I'll create the access request with TWO separate pieces of information:

1. **context** (REQUIRED): The business context ID from Step 2
   - This is an ID like "6dd03400-ddb5-4cc4-bfff-490d94b195a9"
   - Selected from the contexts returned by get_identity_contexts
   - Example: If contexts shows "Sales Department" with id "abc-123", use "abc-123"

2. **reason** (REQUIRED): Your justification text
   - This is a free-text explanation
   - Example: "Need to access project website that requires VPN connection"
   - Example: "Requires access to customer database for Q1 reporting"

Plus:
- Resource(s) to request (from Step 3)
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

4. **Token Handling - IMPORTANT**
   SECURITY BEST PRACTICE:
   - DO NOT display the full bearer token to the user unless explicitly requested
   - Store the token securely in the conversation context
   - Only show a masked version like "Token acquired: eyJ0...*** (hidden for security)"
   - If user asks "show me the token" or "what is my token", then display it

5. **Use the Token**
   Pass the bearer token to any Omada function:
   Example: `get_pending_approvals(impersonate_user="user@domain.com", bearer_token="[token from step 3]")`

The bearer token:
- Stays in the conversation context (you don't need to see it)
- No need to save to files
- Valid for ~1 hour
- Use it for all subsequent operations
- Treat it like a password - don't expose unnecessarily

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

    @mcp.prompt()
    def bulk_access_request_workflow():
        """
        Guide user through requesting access for multiple users (beneficiaries).

        This prompt helps with bulk access request operations:
        1. Get list of identities (potential beneficiaries)
        2. Select multiple users
        3. Find common resources they can request
        4. Create access requests for multiple users
        """
        return """I'll help you request access for multiple users at once in Omada.

**Bulk Access Request Workflow:**

**Step 1: Find Beneficiaries**
First, I'll get a list of identities that can be beneficiaries in access requests.
I'll use get_identities_for_beneficiary to retrieve the list.

Required:
- Email address to impersonate
- Bearer token

Optional pagination:
- Page number (e.g., 1, 2, 3)
- Rows per page (e.g., 10, 20, 50)

**Step 2: Get Business Contexts for Each User**
For each selected identity, I'll call get_identity_contexts to get their available business contexts.

IMPORTANT: "Context" means organizational context
- Examples: Department, Cost Center, Team, Project
- NOT the reason/justification for access
- Each user may have different contexts available
- Must select appropriate context for each user

**Step 3: Find Requestable Resources**
For selected users, I'll find what resources they can request.
You can filter by:
- System ID
- Context ID (from the contexts retrieved in Step 2)
- Resource name

**Step 4: Create Multiple Requests**
I'll create access requests for each selected user with TWO separate fields:

1. **context** (REQUIRED): Business context ID from get_identity_contexts
   - Different for each user based on their available contexts
   - Must be a valid context ID for that specific user
   - Example: "6dd03400-ddb5-4cc4-bfff-490d94b195a9"

2. **reason** (REQUIRED): Your justification text
   - Same reason for all users (or customized per user)
   - Free-text explanation
   - Example: "New team member onboarding - requires VPN access"
   - Example: "Quarterly project team access provisioning"

Plus:
- Same resources for all
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

    @mcp.prompt()
    def compliance_audit_workflow():
        """
        Guide user through auditing compliance violations across users.

        This prompt helps with compliance auditing:
        1. Search for users by department or criteria
        2. Get their calculated assignments
        3. Filter by compliance status
        4. Review violations
        """
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

    @mcp.prompt()
    def resource_discovery_workflow():
        """
        Guide user through discovering and exploring resources in Omada systems.

        This prompt helps with:
        1. Listing resources by system
        2. Filtering by resource type
        3. Understanding resource structure
        """
        return """I'll help you discover and explore resources available in Omada systems.

**Resource Discovery Workflow:**

**Step 1: Understand Resource Types**
Resources in Omada are organized by:
- System (e.g., Active Directory, SAP, Salesforce)
- Resource Type (e.g., Security Groups, Roles, Permissions)

**Step 2: List Resources**
I can show you resources filtered by:
- System ID
- Resource Type ID or Name
- Resource name (partial match)

**Two Discovery Modes:**

**A. Administrative Discovery** (query_omada_resources)
- Shows ALL resources in the system
- Administrative view, not user-scoped
- Good for: Inventory, reporting, analysis
- NOT for: Access request workflows

**B. Requestable Resources** (get_resources_for_beneficiary)
- Shows resources a specific user CAN request
- User-scoped and permission-aware
- Good for: Access requests, user onboarding
- Requires: Identity ID (UId field - 32 character GUID)

**Step 3: Explore Resource Details**
For each resource, I'll show:
- Name and description
- System it belongs to
- Resource type
- Resource ID (for access requests)

**Step 4: Use Resources**
Once you find resources, you can:
- Request access to them
- Use IDs for access request creation
- Filter by system or context

**Important: Which Function to Use?**
- Planning an access request? → Use get_resources_for_beneficiary
- Administrative inventory? → Use query_omada_resources
- Want to see what a user can request? → Use get_resources_for_beneficiary

Let's start exploring! Please provide:
1. What are you looking for? (discovery mode: admin inventory or requestable resources)
2. Your bearer token
3. Optional: System ID, resource type, or resource name filter
"""

    @mcp.prompt()
    def identity_context_workflow():
        """
        Guide user through understanding and using identity contexts.

        This prompt explains contexts and how they're used in access requests.
        """
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

    print("Registered 10 MCP prompts: request_access_workflow, approve_requests_workflow, search_identity_workflow, review_assignments_workflow, authentication_workflow, troubleshooting_workflow, bulk_access_request_workflow, compliance_audit_workflow, resource_discovery_workflow, identity_context_workflow")
