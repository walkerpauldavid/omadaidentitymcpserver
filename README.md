# Omada Identity MCP Server

A Model Context Protocol (MCP) server that provides integration with Omada Identity Governance and Administration system. This server enables Claude Desktop and other MCP clients to interact with Omada's OData REST API and GraphQL API for identity management, access requests, approval workflows, compliance monitoring, and more.

## Features

- **Bearer Token Authentication** - Uses bearer tokens for API authentication (OAuth handled by oauth_mcp_server)
- **OData API Integration** - Query identities, resources, roles, assignments, and any entity type
- **GraphQL API Support** - Access requests, approval workflows, calculated assignments, compliance workbench, identity contexts, and resource lookups (v1.1, v3.0, v3.2)
- **Intelligent Caching** - In-memory cache with per-endpoint TTL, stats, and efficiency monitoring
- **Comprehensive Logging** - File and console logging with per-function log level control
- **Error Handling** - Custom exceptions with detailed error responses
- **LLM Hints** - Rich docstrings guiding Claude on when and how to use each tool

## Prerequisites

- Python 3.13+ (developed on 3.13.7)
- Omada Identity Cloud instance
- Bearer token for authentication (obtain from oauth_mcp_server)
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd omada-mcp-server
```

2. Create and activate a virtual environment:
```bash
python -m venv omada-mcp-server/venv
# Windows
omada-mcp-server\venv\Scripts\activate
# Linux/Mac
source omada-mcp-server/venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables (see Configuration section)

## Dependencies

| Package | Required Version | Installed Version | Purpose |
|---|---|---|---|
| `httpx` | >=0.28.0 | 0.28.1 | HTTP client for Omada API requests |
| `python-dotenv` | >=1.1.0 | 1.2.1 | Environment variable loading from .env |
| `mcp` | >=1.13.0 | 1.21.0 | Model Context Protocol server framework |
| `fastmcp` | >=2.12.0 | 2.13.0.2 | High-level MCP server framework |
| `pytest` | >=8.0.0 | 9.0.1 | Testing framework |
| `pytest-asyncio` | >=0.23.0 | 1.3.0 | Async test support |
| `requests` | >=2.31.0 | 2.32.5 | HTTP library (used in test files) |
| `black` | - | 25.11.0 | Code formatter |
| `isort` | - | 7.0.0 | Import sorter |

## Configuration

### Setting up the .env File

The `.env` file contains configuration settings and is **not included in the repository** for security reasons. You must create this file manually.

**Note:** OAuth2 authentication has been moved to the separate `oauth_mcp_server` project. This server uses bearer tokens provided by that OAuth server.

**Step-by-step setup:**

1. **Create the .env file** in the `omada-mcp-server/omada-mcp-server/` directory (alongside `server.py`):
   ```bash
   cd omada-mcp-server/omada-mcp-server
   touch .env    # On Linux/Mac
   # Or create manually on Windows
   ```

2. **Copy the template below** into your `.env` file

3. **Replace placeholder values** with your actual configuration

### .env File Template

```bash
# =============================================================================
# REQUIRED CONFIGURATION - You must set these values
# =============================================================================

# Omada Identity Configuration
OMADA_BASE_URL=https://your-instance.omada.cloud # Your Omada instance URL (no trailing slash)
GRAPHQL_ENDPOINT_VERSION=3.0                     # Default GraphQL API version
                                                 # Individual tools override this (e.g., v3.2 for newer tools)

# =============================================================================
# OPTIONAL CONFIGURATION - Customize as needed
# =============================================================================

# Logging Configuration
LOG_LEVEL=INFO                                   # Global log level: DEBUG, INFO, WARNING, ERROR
LOG_FILE=omada_mcp_server.log                   # Log file path (relative or absolute)

# Per-Function Log Levels (override global LOG_LEVEL for specific functions)
# Useful for debugging specific operations without flooding logs
#
# GraphQL Tools
LOG_LEVEL_get_access_requests=INFO
LOG_LEVEL_get_access_requests_by_ids=INFO
LOG_LEVEL_create_access_request=DEBUG
LOG_LEVEL_get_resources_for_beneficiary=DEBUG
LOG_LEVEL_get_requestable_resources=DEBUG
LOG_LEVEL_get_identities_for_beneficiary=DEBUG
LOG_LEVEL_get_identity_contexts=DEBUG
LOG_LEVEL_get_calculated_assignments_detailed=DEBUG
#
# Approval Workflow Tools
LOG_LEVEL_get_pending_approvals=DEBUG
LOG_LEVEL_get_approval_details=DEBUG
LOG_LEVEL_make_approval_decision=DEBUG
LOG_LEVEL_get_access_request_approval_survey_questions=DEBUG
LOG_LEVEL_get_access_request_approval_survey_question_by_id=DEBUG
LOG_LEVEL_get_access_approval_workflow_steps_question_count=DEBUG
LOG_LEVEL_get_approval_workflow_status=DEBUG
#
# Compliance
LOG_LEVEL_get_compliance_workbench_survey_and_compliance_status=DEBUG
#
# OData Tools
LOG_LEVEL_query_omada_entity=INFO
LOG_LEVEL_query_omada_identity=INFO
LOG_LEVEL_query_omada_resources=INFO
LOG_LEVEL_query_omada_entities=INFO
LOG_LEVEL_query_calculated_assignments=INFO
LOG_LEVEL_get_all_omada_identities=INFO
#
# Utility
LOG_LEVEL_ping=INFO

# Omada Resource Type Mappings
# Get these IDs from your Omada instance (Resource Types section)
RESOURCE_TYPE_APPLICATION_ROLES=1011066
# Add more resource types as needed:
# RESOURCE_TYPE_BUSINESS_ROLES=1011067
# RESOURCE_TYPE_IT_ROLES=1011068
# RESOURCE_TYPE_AD_GROUPS=1011069
```

### How to Get Your Omada URL

Your Omada base URL is the URL you use to access your Omada instance:
- Format: `https://your-company-name.omada.cloud`
- **Do not include** a trailing slash
- Example: `https://pawa-poc2.omada.cloud`

### Verifying Your Configuration

After creating your `.env` file, you can test the configuration:

```bash
# Use the ping function to verify the server starts
python server.py
```

### Authentication

This server requires bearer tokens for API authentication. OAuth2 token generation has been moved to the separate `oauth_mcp_server` project. Use that server to obtain bearer tokens, then provide them when calling functions in this server.

## Available Tools

All GraphQL and OData tools require `impersonate_user` (email) and `bearer_token` parameters.

### OData Query Tools

| Tool | Description |
|---|---|
| `query_omada_entity` | Advanced generic query with full OData support ($filter, $select, $expand, $orderby, count_only) |
| `query_omada_identity` | Query identities with field filters and OData parameters |
| `query_omada_resources` | Query resources by type and system |
| `query_omada_entities` | Generic query for any entity type (Identity, Resource, Role, etc.) |
| `query_calculated_assignments` | Query calculated assignments via OData with filters |
| `get_all_omada_identities` | Retrieve all identities with pagination support |

### Access Request Tools

| Tool | GraphQL Version | Description |
|---|---|---|
| `get_access_requests` | v3.2 | Retrieve access requests with 7 text filters (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY) + 3 date filters (LESS_THAN, GREATER_THAN) |
| `get_access_requests_by_ids` | v3.2 | Retrieve specific access requests by GUID(s), includes child assignments and violations |
| `create_access_request` | v1.1 | Create a new access request with reason, context, resources, and optional validity dates |

### Access Request Component Tools

| Tool | GraphQL Version | Description |
|---|---|---|
| `get_resources_for_beneficiary` | v3.2 | Get resources available for access requests for a specific identity |
| `get_requestable_resources` | v1.1 | Get requestable resources (alias/alternative for resource lookup) |
| `get_identities_for_beneficiary` | v3.2 | Get identities available as beneficiaries for access requests |
| `get_identity_contexts` | v3.2 | Get contexts for a specific identity (used in access request creation) |

### Approval Workflow Tools

| Tool | GraphQL Version | Description |
|---|---|---|
| `get_pending_approvals` | v3.0 | Get pending approval survey questions (summary mode, single workflow_step filter) |
| `get_access_request_approval_survey_questions` | v3.2 | Full-featured approval query with 6 filters + sorting (v3.2 replacement for get_pending_approvals) |
| `get_access_request_approval_survey_question_by_id` | v3.2 | Get a single approval question by survey_id + survey_object_key |
| `get_access_approval_workflow_steps_question_count` | v3.2 | Get question counts per workflow step (optional workflow_step_name filter) |
| `get_approval_details` | v3.0 | Get full approval details including technical IDs (surveyId, surveyObjectKey) |
| `make_approval_decision` | v3.0 | Submit APPROVE or REJECT decision (requires survey_id + survey_object_key) |
| `get_approval_workflow_status` | v3.2 | Get workflow status for survey objects (ASSIGNEE or REQUESTER_OR_BENEFICIARY viewer) |

### Calculated Assignments Tools

| Tool | GraphQL Version | Description |
|---|---|---|
| `query_calculated_assignments` | OData | Query calculated assignments via OData with filters |
| `get_calculated_assignments_detailed` | v3.2 | Detailed assignments with compliance/violations. 7 text filters (CONTAINS, EQUALS, IS_EMPTY, IS_NOT_EMPTY), 2 date filters, plus category, disabled, reason_type, resource_ids, system_id. At least one filter required. |

### Compliance Tools

| Tool | GraphQL Version | Description |
|---|---|---|
| `get_compliance_workbench_survey_and_compliance_status` | v3.0 | Get compliance workbench configuration and compliance status |

### Cache Management Tools

| Tool | Description |
|---|---|
| `get_cache_stats` | View cache hit/miss statistics and performance metrics |
| `clear_cache` | Clear cache entries (all or by specific endpoint) |
| `view_cache_contents` | View summary of cached entries with optional expired entries |
| `view_cache_contents_detailed` | View detailed cache contents for a specific endpoint |
| `get_cache_efficiency` | Get cache efficiency analysis and recommendations |

### Utility Tools

| Tool | Description |
|---|---|
| `ping` | Health check endpoint |
| `check_omada_config` | Verify Omada configuration (URL, env vars) |

## Usage Examples

### Using with Claude Desktop

1. Configure the MCP server in Claude Desktop's configuration file (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "omada-server": {
      "command": "C:\\path\\to\\omada-mcp-server\\omada-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\omada-mcp-server\\omada-mcp-server\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\omada-mcp-server\\omada-mcp-server"
      }
    }
  }
}
```

2. Ask Claude to use the tools:
```
Show me all access requests for system "Active Directory"
```
```
Get detailed calculated assignments for identity "5da7f8fc-..." filtering by compliance status "NOT APPROVED"
```
```
Show me pending approvals for the ManagerApproval workflow step
```

### Running the Server

```bash
python omada-mcp-server/server.py
```

## API Details

### OData API
- **Endpoint**: `{OMADA_BASE_URL}/OData/DataObjects/{EntityType}`
- **Built-in Endpoint**: `{OMADA_BASE_URL}/OData/BuiltIn/CalculatedAssignments`
- **Supported Entities**: Identity, Resource, Role, Account, Application, System, AssignmentPolicy
- **Features**: Filtering ($filter), pagination ($top/$skip), field selection ($select), ordering ($orderby), expansion ($expand), counting (count_only)

### GraphQL API
- **Endpoint**: `{OMADA_BASE_URL}/api/Domain/{version}`
- **Versions in use**:
  - **v1.1** - `createAccessRequest`, `get_requestable_resources`
  - **v3.0** - `get_pending_approvals`, `get_approval_details`, `make_approval_decision`, `get_compliance_workbench_survey_and_compliance_status`
  - **v3.2** - `get_access_requests`, `get_access_requests_by_ids`, `get_calculated_assignments_detailed`, `get_access_request_approval_survey_questions`, `get_access_request_approval_survey_question_by_id`, `get_access_approval_workflow_steps_question_count`, `get_approval_workflow_status`, `get_resources_for_beneficiary`, `get_identities_for_beneficiary`, `get_identity_contexts`
- **Features**: Access requests, approval workflows, calculated assignments, compliance workbench, identity contexts, resource/identity lookups

## Logging

Logs are written to both file and console:
- **Default log file**: `omada_mcp_server.log` in project directory
- **Format**: `timestamp - logger_name - level - message`
- **Per-function levels**: Control log verbosity per function via `LOG_LEVEL_<function_name>` environment variables

Example log output:
```
2024-10-01 20:30:15 - __main__ - INFO - Logging initialized. Writing logs to: /path/to/omada_mcp_server.log
2024-10-01 20:30:16 - __main__ - DEBUG - GraphQL query: query GetContextsForIdentity { ... }
```

## Project Structure

```
omada-mcp-server/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── pytest.ini                         # Pytest configuration
├── LICENSE                            # License file
├── api_examples/                      # GraphQL query reference files
│   ├── graphql_cwconfig.txt
│   ├── graphql_doAccessRequest.txt
│   ├── graphql_getassigmentsdetailed.txt
│   ├── graphql_getcalculatedassignments.txt
│   ├── graphql_getpendingapprovals.txt
│   ├── graphql_getResourceDescAndId.txt
│   ├── graphql_makeApproval.txt
│   └── graphql_queryResourcesForRequest.txt
├── utility/                           # Utility scripts
│   ├── kill_claude.bat
│   ├── kill_claude.ps1
│   └── quick_kill_claude.ps1
└── omada-mcp-server/                  # Main server package
    ├── server.py                      # Main MCP server implementation (all tools)
    ├── helpers.py                     # Helper functions
    ├── cache.py                       # Caching implementation
    ├── completions.py                 # MCP completions support
    ├── prompts.py                     # MCP prompts support
    ├── schemas.py                     # Schema definitions
    ├── .env                           # Environment configuration (not in git)
    ├── venv/                          # Python virtual environment (not in git)
    └── tests/                         # Test scripts
        ├── test_access_requests_standalone.py
        ├── test_calculated_assignments.py
        ├── test_create_access_request.py
        ├── test_get_calculated_assignments_detailed.py
        ├── test_get_identity_contexts.py
        └── ... (20+ test files)
```

## Error Handling

The server uses custom exception classes:
- **`OmadaServerError`** - Base exception for server errors
- **`AuthenticationError`** - OAuth2 and token failures
- **`ODataQueryError`** - Malformed or failed OData queries

All functions return JSON responses with status indicators:
```json
{
  "status": "success|error|exception",
  "message": "Description of result or error",
  "error_type": "ValidationError|GraphQLError|etc"
}
```

## Security Notes

- Never commit `.env` file - contains configuration settings
- Log files (`.log`) are excluded from git
- Bearer tokens should be obtained from `oauth_mcp_server`
- All API calls use HTTPS

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly using test scripts
4. Commit with descriptive messages
5. Push and create pull request

## License

See the [LICENSE](./LICENSE) file for details.

## Support

For issues or questions, please open an issue on the repository.
