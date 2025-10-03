# Omada Identity MCP Server

A Model Context Protocol (MCP) server that provides integration with Omada Identity Governance and Administration system. This server enables Claude Desktop and other MCP clients to interact with Omada's OData REST API and GraphQL API for identity management, access requests, and compliance monitoring.

## Features

- **Azure AD OAuth2 Authentication** - Secure authentication using client credentials flow
- **OData API Integration** - Query identities, resources, roles, and assignments
- **GraphQL API Support** - Access requests, contexts, and detailed calculated assignments
- **Comprehensive Logging** - File and console logging with per-function log level control
- **Error Handling** - Custom exceptions with detailed error responses
- **Token Caching** - Automatic OAuth2 token caching and refresh

## Prerequisites

- Python 3.8 or higher
- Omada Identity Cloud instance
- Azure AD application registration with client credentials
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/walkerpauldavid/omadaidentitymcpserver.git
cd omadaidentitymcpserver
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (see Configuration section)

## Configuration

### Setting up the .env File

The `.env` file contains sensitive credentials and is **not included in the repository** for security reasons. You must create this file manually.

**Step-by-step setup:**

1. **Create the .env file** in the project root directory:
   ```bash
   cd omada_mcp_server
   touch .env    # On Linux/Mac
   # Or create manually on Windows
   ```

2. **Copy the template below** into your `.env` file

3. **Replace placeholder values** with your actual credentials:
   - Get Azure AD values from your Azure portal app registration
   - Get Omada URL from your Omada instance
   - Configure logging preferences as needed

### .env File Template

Copy this complete template into your `.env` file and update the values:

```bash
# =============================================================================
# REQUIRED CONFIGURATION - You must set these values
# =============================================================================

# Azure AD OAuth2 Configuration
# Get these from your Azure Portal > App Registrations > Your App
TENANT_ID=your-tenant-id-here                    # Azure AD Tenant ID (GUID)
CLIENT_ID=your-client-id-here                    # Application (client) ID
CLIENT_SECRET=your-client-secret-here            # Client secret value
OAUTH2_SCOPE=api://your-client-id-here/.default  # OAuth2 scope (use your CLIENT_ID)

# Omada Identity Configuration
OMADA_BASE_URL=https://your-instance.omada.cloud # Your Omada instance URL (no trailing slash)
GRAPHQL_ENDPOINT_VERSION=3.0                     # GraphQL API version (default: 3.0)

# =============================================================================
# OPTIONAL CONFIGURATION - Customize as needed
# =============================================================================

# Logging Configuration
LOG_LEVEL=INFO                                   # Global log level: DEBUG, INFO, WARNING, ERROR
LOG_FILE=omada_mcp_server.log                   # Log file path (relative or absolute)
                                                 # Examples:
                                                 # - omada_mcp_server.log (current directory)
                                                 # - logs/omada_mcp_server.log (subdirectory)
                                                 # - /var/log/omada_mcp_server.log (absolute path)

# Per-Function Log Levels (override global LOG_LEVEL for specific functions)
# Useful for debugging specific operations without flooding logs
LOG_LEVEL_get_identity_contexts=DEBUG
LOG_LEVEL_get_resources_for_beneficiary=DEBUG
LOG_LEVEL_get_calculated_assignments_detailed=DEBUG
LOG_LEVEL_create_access_request=DEBUG
LOG_LEVEL_get_access_requests=INFO

# Core Query Functions
LOG_LEVEL_query_omada_entity=INFO
LOG_LEVEL_query_omada_identity=INFO
LOG_LEVEL_query_omada_resources=INFO
LOG_LEVEL_query_omada_entities=INFO
LOG_LEVEL_query_calculated_assignments=INFO

# Identity Management Functions
LOG_LEVEL_get_all_omada_identities=INFO
LOG_LEVEL_count_omada_identities=INFO

# Authentication Functions
LOG_LEVEL_get_azure_token=INFO
LOG_LEVEL_get_azure_token_info=INFO
LOG_LEVEL_test_azure_token=INFO

# Utility Functions
LOG_LEVEL_ping=INFO

# Omada Resource Type Mappings
# Get these IDs from your Omada instance (Resource Types section)
RESOURCE_TYPE_APPLICATION_ROLES=1011066
# Add more resource types as needed:
# RESOURCE_TYPE_BUSINESS_ROLES=1011067
# RESOURCE_TYPE_IT_ROLES=1011068
# RESOURCE_TYPE_AD_GROUPS=1011069
```

### How to Get Your Azure AD Values

1. **Log into Azure Portal**: https://portal.azure.com
2. **Navigate to**: Azure Active Directory > App registrations
3. **Select your app** (or create a new one)
4. **Get values**:
   - **TENANT_ID**: Overview page > Directory (tenant) ID
   - **CLIENT_ID**: Overview page > Application (client) ID
   - **CLIENT_SECRET**: Certificates & secrets > Client secrets > Create new secret
   - **OAUTH2_SCOPE**: Use format `api://{CLIENT_ID}/.default`

### How to Get Your Omada URL

Your Omada base URL is the URL you use to access your Omada instance:
- Format: `https://your-company-name.omada.cloud`
- **Do not include** a trailing slash
- Example: `https://pawa-poc2.omada.cloud`

### Verifying Your Configuration

After creating your `.env` file, you can test the configuration:

```bash
# Test Azure authentication
python -c "from server import get_azure_token; import asyncio; print(asyncio.run(get_azure_token()))"

# Or use the ping function to verify the server starts
python server.py
```

## Available Functions

### Authentication Functions

- **`get_azure_token`** - Get OAuth2 bearer token for API authentication
- **`get_azure_token_info`** - Get detailed token information including expiry
- **`test_azure_token`** - Test token validity by making an API call

### Identity Query Functions

- **`query_omada_identity`** - Query identities with field filters and OData parameters
- **`get_all_omada_identities`** - Retrieve all identities with pagination support
- **`count_omada_identities`** - Count identities with optional filtering
- **`query_omada_entities`** - Generic query for any entity type (Identity, Resource, Role, etc.)
- **`query_omada_entity`** - Advanced generic query with full OData support

### Resource Query Functions

- **`query_omada_resources`** - Query resources by type and system
- **`get_resources_for_beneficiary`** - Get resources available for access requests
  - **Required**: `identity_id`, `impersonate_user`
  - **Optional**: `system_id`, `context_id`

### Access Request Functions

- **`get_access_requests`** - Retrieve access requests with optional filtering
  - **Required**: `impersonate_user`
  - **Optional**: `filter_field`, `filter_value`

- **`create_access_request`** - Create new access request
  - **Required**: `impersonate_user`, `reason`, `context`, `resources`
  - **Optional**: `valid_from`, `valid_to`

### Identity Context Functions

- **`get_identity_contexts`** - Get contexts for a specific identity
  - **Required**: `identity_id`, `impersonate_user`

### Calculated Assignments Functions

- **`query_calculated_assignments`** - Query calculated assignments for an identity
  - **Optional**: `identity_id`, `select_fields`, `expand`, filters

- **`get_calculated_assignments_detailed`** - Get detailed assignments with compliance and violations
  - **Required**: `identity_id`, `impersonate_user`
  - **Optional**: `resource_type_name`, `compliance_status`
  - Uses GraphQL API version 2.19

### Utility Functions

- **`ping`** - Health check endpoint

## Usage Examples

### Using with Claude Desktop

1. Configure the MCP server in Claude Desktop's configuration file

2. Ask Claude to use the functions:
```
Get detailed calculated assignments for identity "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"
impersonating "user@domain.com" filtering by compliance status "NOT APPROVED"
```

### Python Testing

Run test scripts from the `tests/` directory:

```bash
# Test identity contexts
python tests/test_get_identity_contexts.py

# Test calculated assignments
python tests/test_get_calculated_assignments_detailed.py

# Test access request creation
python tests/test_create_access_request.py
```

### Running the Server

```bash
python server.py
```

## API Details

### OData API
- **Endpoint**: `{OMADA_BASE_URL}/OData/DataObjects/{EntityType}`
- **Supported Entities**: Identity, Resource, Role, Account, Application, System, AssignmentPolicy
- **Features**: Filtering, pagination, field selection, ordering, expansion

### GraphQL API
- **Endpoint**: `{OMADA_BASE_URL}/api/Domain/{version}`
- **Default Version**: 3.0
- **Assignments Version**: 2.19 (for calculated assignments)
- **Features**: Access requests, contexts, resources, detailed assignments

## Logging

Logs are written to both file and console:
- **Default log file**: `omada_mcp_server.log` in project directory
- **Format**: `timestamp - logger_name - level - message`
- **Per-function levels**: Control log verbosity per function via environment variables

Example log output:
```
2024-10-01 20:30:15 - __main__ - INFO - Logging initialized. Writing logs to: /path/to/omada_mcp_server.log
2024-10-01 20:30:16 - __main__ - DEBUG - GraphQL query: query GetContextsForIdentity { ... }
```

## Project Structure

```
omada_mcp_server/
 server.py                          # Main MCP server implementation
 .env                               # Environment configuration (not in git)
 .gitignore                        # Git ignore rules
 README.md                         # This file
 requirements.txt                  # Python dependencies
 graphql_*.txt                     # GraphQL query reference files
 tests/                            # Test scripts
    test_get_identity_contexts.py
    test_get_calculated_assignments_detailed.py
    test_create_access_request.py
    ... (25+ test files)
 utility/                          # Utility scripts
     kill_claude.bat
     kill_claude.ps1
     quick_kill_claude.ps1
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

- Never commit `.env` file - contains sensitive credentials
- Log files (`.log`) are excluded from git
- OAuth2 tokens are cached in memory only
- All API calls use HTTPS

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly using test scripts
4. Commit with descriptive messages
5. Push and create pull request

## License

[Add your license information here]

## Support

For issues or questions, please open an issue on GitHub.
