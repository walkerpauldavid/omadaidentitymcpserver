# schemas.py
"""
MCP Resource definitions for Omada entity schemas.

This module registers MCP resources that expose schema definitions for Omada entities,
helping LLM clients understand the data structures returned by the API.
"""

import json

# Resource entity schema definition based on Omada OData API
RESOURCE_SCHEMA = {
    "entity": "Resource",
    "description": "Represents a resource (role, permission, access right) in Omada Identity that can be assigned to identities.",
    "odata_endpoint": "/OData/DataObjects/Resource",
    "fields": {
        # Core identification fields
        "Id": {
            "type": "integer",
            "description": "Internal database ID (numeric). Use for OData queries with identity_id parameter.",
            "example": 1001362
        },
        "UId": {
            "type": "string (GUID)",
            "description": "Unique identifier (32-character GUID with dashes). Use for GraphQL queries with resource_ids parameter.",
            "example": "0c07c922-7310-480f-b23b-052f36fee3da"
        },
        "DisplayName": {
            "type": "string",
            "description": "Human-readable display name for the resource.",
            "example": "Domain Admins"
        },
        "NAME": {
            "type": "string",
            "description": "Resource name (often same as DisplayName).",
            "example": "Domain Admins"
        },
        "DESCRIPTION": {
            "type": "string",
            "description": "Detailed description of the resource and its purpose.",
            "example": "Members have full admin access to the domain"
        },
        "ROLEID": {
            "type": "string",
            "description": "Unique role identifier string used in provisioning systems.",
            "example": "OI_ROLEFOLDEROWNER"
        },

        # Timestamps
        "CreateTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the resource was created.",
            "example": "2022-01-12T11:30:23.2467471Z"
        },
        "ChangeTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the resource was last modified.",
            "example": "2025-06-24T11:45:23.2531325Z"
        },
        "DeleteTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the resource was deleted (if Deleted=true).",
            "example": "0001-01-01T00:00:00Z"
        },

        # Status fields
        "Deleted": {
            "type": "boolean",
            "description": "Whether the resource has been soft-deleted.",
            "example": False
        },
        "RESOURCESTATUS": {
            "type": "object (reference)",
            "description": "Current status of the resource (Active, Inactive, etc.).",
            "example": {"Id": 1011, "UId": "2cebbf25-b2b9-4922-b539-02f3c764c0fc", "Value": "Active"}
        },

        # Validity period
        "VALIDFROM": {
            "type": "datetime (ISO 8601) or null",
            "description": "Start date when the resource becomes valid.",
            "example": None
        },
        "VALIDTO": {
            "type": "datetime (ISO 8601) or null",
            "description": "End date when the resource expires.",
            "example": None
        },
        "MAXVALIDITY": {
            "type": "integer or null",
            "description": "Maximum validity period in days for assignments to this resource.",
            "example": None
        },

        # Risk and compliance
        "RISKSCORE": {
            "type": "integer",
            "description": "Numeric risk score for the resource (higher = more risky).",
            "example": 147
        },
        "RISKLEVEL": {
            "type": "object (reference)",
            "description": "Risk level classification (Low, Medium, High, Critical).",
            "example": {"Id": 1000239, "UId": "ee65fc68-f108-4fd1-b738-715b8f6e430f", "Value": "Medium"}
        },
        "POLICYRISKCHECK": {
            "type": "array",
            "description": "List of policy risk checks associated with this resource.",
            "example": []
        },

        # System and type references
        "SYSTEMREF": {
            "type": "object (reference)",
            "description": "Reference to the system this resource belongs to.",
            "example": {"Id": 1001361, "UId": "f05c44fa-7256-4b8b-8471-eaf598d9a99e", "DisplayName": "Active Directory"}
        },
        "ROLETYPEREF": {
            "type": "object (reference)",
            "description": "Reference to the resource type definition.",
            "example": {"Id": 1001359, "UId": "e2dbab91-f258-4d1b-ad56-4a8a0acf1c41", "DisplayName": "AD Security Group"}
        },
        "ROLECATEGORY": {
            "type": "object (reference)",
            "description": "Category of the resource (Role, Application, etc.).",
            "example": {"Id": 500, "UId": "2802e876-cc4b-42cf-958f-559963820fae", "Value": "Role"}
        },
        "ROLEFOLDER": {
            "type": "object (reference)",
            "description": "Folder/container where this resource is organized.",
            "example": {"Id": 1001356, "UId": "0b77602c-85a2-4d33-8794-ed5fd20567d3", "DisplayName": "IT Resources"}
        },

        # Ownership
        "OWNERREF": {
            "type": "array (references)",
            "description": "List of identity references who own this resource.",
            "example": []
        },
        "EXPLICITOWNER": {
            "type": "array (references)",
            "description": "List of explicitly assigned owners.",
            "example": []
        },
        "MANUALOWNER": {
            "type": "array (references)",
            "description": "List of manually assigned owners.",
            "example": []
        },

        # Relationships
        "CHILDROLES": {
            "type": "array (references)",
            "description": "Child resources that inherit from this resource.",
            "example": [{"Id": 1024105, "UId": "f9f0b06b-5a88-49b1-a44d-6ac88ff72268", "DisplayName": "Resource owners"}]
        },
        "ACCOUNTTYPE": {
            "type": "array (references)",
            "description": "Account types associated with this resource.",
            "example": []
        },

        # Provisioning settings
        "SKIPPROVISIONING": {
            "type": "boolean",
            "description": "Whether to skip provisioning for this resource.",
            "example": True
        },
        "PROVDEPENDSON": {
            "type": "object (reference) or null",
            "description": "Resource that this resource depends on for provisioning.",
            "example": None
        },

        # Self-service settings
        "PREVENTSELFSVC": {
            "type": "boolean or null",
            "description": "Whether to prevent self-service requests for this resource.",
            "example": None
        },
        "PREVENTSELFSVCTHIRDPARTY": {
            "type": "boolean",
            "description": "Whether to prevent third-party self-service requests.",
            "example": False
        },
        "ADDREQUESTINFOATTRS": {
            "type": "string",
            "description": "Additional request information attributes.",
            "example": ""
        },

        # Certification
        "ROLELASTCERTIFIEDDATE": {
            "type": "datetime (ISO 8601) or null",
            "description": "When the resource was last certified.",
            "example": None
        },
        "ROLECERTIFICATIONLOG": {
            "type": "string",
            "description": "Log of certification activities.",
            "example": ""
        },

        # Inheritance settings
        "DISABCONDINHERIT": {
            "type": "boolean",
            "description": "Whether to disable conditional inheritance.",
            "example": True
        },

        # Custom/Extended fields
        "ATTRIBVALUES": {
            "type": "array",
            "description": "Custom attribute values for extended properties.",
            "example": []
        },
        "CLT_TAGS": {
            "type": "array",
            "description": "Client-specific tags for categorization.",
            "example": []
        },
        "C_RESOURCE_CONTEXTS": {
            "type": "array",
            "description": "Custom resource context assignments.",
            "example": []
        },
        "RESOURCECONTEXTS": {
            "type": "array",
            "description": "Resource context assignments.",
            "example": []
        },

        # Other references
        "BUSINESSPROCMVREF": {
            "type": "array (references)",
            "description": "Business process references.",
            "example": []
        },
        "JOBTITLE_REF": {
            "type": "object (reference) or null",
            "description": "Job title reference for role-based access.",
            "example": None
        },
        "PASSWORDPOLICY": {
            "type": "object (reference) or null",
            "description": "Password policy reference.",
            "example": None
        },
        "USERGROUPREF": {
            "type": "object (reference) or null",
            "description": "User group reference.",
            "example": None
        },

        # Technical fields
        "CurrentVersionId": {
            "type": "integer",
            "description": "Current version ID for optimistic concurrency.",
            "example": 1048231
        },
        "ODWBUSIKEY": {
            "type": "string",
            "description": "Business key for data warehouse integration.",
            "example": "1_<id>1001362</id>"
        },
        "ODWLOGICKEY": {
            "type": "string",
            "description": "Logical key for data warehouse integration.",
            "example": ""
        },
        "OBJECTGUID": {
            "type": "string",
            "description": "External object GUID (e.g., from Active Directory).",
            "example": ""
        },
        "ATY_NAMEFORMAT": {
            "type": "string",
            "description": "Account type name format.",
            "example": ""
        }
    },
    "common_queries": {
        "get_by_id": "Use query_omada_entity with entity_type='Resource' and filter_condition=\"Id eq {id}\"",
        "get_by_uid": "Use query_omada_entity with entity_type='Resource' and filter_condition=\"UId eq '{uid}'\"",
        "get_by_name": "Use query_omada_entity with entity_type='Resource' and filter_condition=\"contains(NAME, '{name}')\"",
        "get_by_system": "Use query_omada_entity with entity_type='Resource' and expand='SYSTEMREF' and filter_condition=\"SYSTEMREF/Id eq {system_id}\"",
        "get_assignments": "Use query_calculated_assignments or get_calculated_assignments_detailed with resource_ids or resource_name parameter"
    }
}

# Identity entity schema definition based on Omada OData API
IDENTITY_SCHEMA = {
    "entity": "Identity",
    "description": "Represents a person or service account identity in Omada Identity. This is the core entity for users, employees, contractors, and service accounts.",
    "odata_endpoint": "/OData/DataObjects/Identity",
    "fields": {
        # Core identification fields
        "Id": {
            "type": "integer",
            "description": "Internal database ID (numeric). Use for OData queries with identity_id parameter.",
            "example": 1025952
        },
        "UId": {
            "type": "string (GUID)",
            "description": "Unique identifier (32-character GUID with dashes). Use for GraphQL queries with identity_ids parameter. THIS IS THE FIELD TO USE FOR get_calculated_assignments_detailed.",
            "example": "f847738e-a96f-4ddc-ba0c-e1dd408ff469"
        },
        "IDENTITYID": {
            "type": "string",
            "description": "Human-readable identity identifier (username/login). NOT for GraphQL queries - use UId instead.",
            "example": "PAUWAL"
        },
        "DisplayName": {
            "type": "string",
            "description": "Full display name of the identity.",
            "example": "Paul Walker"
        },

        # Personal information
        "FIRSTNAME": {
            "type": "string",
            "description": "First name of the identity.",
            "example": "Paul"
        },
        "LASTNAME": {
            "type": "string",
            "description": "Last name/surname of the identity.",
            "example": "Walker"
        },
        "EMAIL": {
            "type": "string",
            "description": "Primary email address.",
            "example": "pawa@omada.net"
        },
        "EMAIL2": {
            "type": "string",
            "description": "Secondary/alternate email address.",
            "example": ""
        },
        "JOBTITLE": {
            "type": "string",
            "description": "Job title as free text.",
            "example": "Software Engineer"
        },
        "JOBTITLE_REF": {
            "type": "object (reference) or null",
            "description": "Reference to job title master data.",
            "example": None
        },
        "CELLPHONE": {
            "type": "string",
            "description": "Mobile/cell phone number.",
            "example": "+1-555-123-4567"
        },
        "BIRTHDAY": {
            "type": "datetime (ISO 8601) or null",
            "description": "Date of birth.",
            "example": None
        },
        "GENDER": {
            "type": "object (reference) or null",
            "description": "Gender reference.",
            "example": None
        },

        # Address fields
        "ADDRESS1": {
            "type": "string",
            "description": "Primary address line.",
            "example": "123 Main Street"
        },
        "ADDRESS2": {
            "type": "string",
            "description": "Secondary address line.",
            "example": "Suite 100"
        },
        "CITY": {
            "type": "string",
            "description": "City name.",
            "example": "New York"
        },
        "STATE_REGION": {
            "type": "string",
            "description": "State or region.",
            "example": "NY"
        },
        "ZIPCODE": {
            "type": "string",
            "description": "Postal/ZIP code.",
            "example": "10001"
        },
        "COUNTRY": {
            "type": "object (reference) or null",
            "description": "Country reference.",
            "example": None
        },

        # Timestamps
        "CreateTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the identity was created.",
            "example": "2025-07-08T15:06:43.4174565Z"
        },
        "ChangeTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the identity was last modified.",
            "example": "2025-07-08T15:07:02.6521765Z"
        },
        "DeleteTime": {
            "type": "datetime (ISO 8601)",
            "description": "When the identity was deleted (if Deleted=true).",
            "example": "0001-01-01T00:00:00Z"
        },

        # Status and validity
        "Deleted": {
            "type": "boolean",
            "description": "Whether the identity has been soft-deleted.",
            "example": False
        },
        "IDENTITYSTATUS": {
            "type": "object (reference)",
            "description": "Current status of the identity (Active, Inactive, Terminated, etc.).",
            "example": {"Id": 551, "UId": "a4ed4124-9b94-43a0-92c0-e71fba733049", "Value": "Active"}
        },
        "VALIDFROM": {
            "type": "datetime (ISO 8601)",
            "description": "Start date when the identity becomes valid/active.",
            "example": "2025-06-30T22:00:00Z"
        },
        "VALIDTO": {
            "type": "datetime (ISO 8601)",
            "description": "End date when the identity expires/terminates.",
            "example": "9999-12-30T23:00:00Z"
        },

        # Classification
        "IDENTITYCATEGORY": {
            "type": "object (reference)",
            "description": "Category of identity (Employee, Contractor, External, Service Account, etc.).",
            "example": {"Id": 560, "UId": "ac0c67fc-5f47-4112-94e6-446bfb68326a", "Value": "Employee"}
        },
        "IDENTITYTYPE": {
            "type": "object (reference)",
            "description": "Type of identity (Primary, Secondary, Service, etc.).",
            "example": {"Id": 580, "UId": "d13624f9-905d-4bc5-a6cc-2a4589c26be4", "Value": "Primary"}
        },

        # Risk and compliance
        "RISKSCORE": {
            "type": "integer",
            "description": "Numeric risk score for the identity (higher = more risky).",
            "example": 147
        },
        "RISKLEVEL": {
            "type": "object (reference)",
            "description": "Risk level classification (Low, Medium, High, Critical).",
            "example": {"Id": 1000239, "UId": "ee65fc68-f108-4fd1-b738-715b8f6e430f", "Value": "Medium"}
        },
        "IDENTSODRECALCSURV": {
            "type": "datetime or null",
            "description": "Last SoD recalculation survey date.",
            "example": None
        },
        "IDENT_RELAUNCHSOD": {
            "type": "datetime or null",
            "description": "SoD relaunch date.",
            "example": None
        },

        # Organizational references
        "OUREF": {
            "type": "object (reference)",
            "description": "Primary organizational unit reference.",
            "example": {"Id": 1003843, "UId": "5d00d8a7-fa5d-46fe-a00b-6392a5fd12f4", "DisplayName": "Global Banking Group [GBG]"}
        },
        "PRIMARYCONTEXTTYPE": {
            "type": "object (reference)",
            "description": "Primary context type for the identity.",
            "example": {"Id": 1001389, "UId": "9b334c8b-9159-407c-ae00-7371d2d1768c", "DisplayName": "Org. units"}
        },
        "DIVISION": {
            "type": "object (reference) or null",
            "description": "Division reference.",
            "example": None
        },
        "BUSINESSUNIT": {
            "type": "object (reference) or null",
            "description": "Business unit reference.",
            "example": None
        },
        "COMPANY": {
            "type": "object (reference) or null",
            "description": "Company reference.",
            "example": None
        },
        "COSTCENTER": {
            "type": "object (reference) or null",
            "description": "Cost center reference.",
            "example": None
        },
        "LOCATION": {
            "type": "object (reference) or null",
            "description": "Location reference.",
            "example": None
        },
        "BUILDING": {
            "type": "object (reference) or null",
            "description": "Building reference.",
            "example": None
        },
        "SUBAREA": {
            "type": "object (reference) or null",
            "description": "Sub-area reference.",
            "example": None
        },

        # Relationships
        "MANAGER": {
            "type": "array (references)",
            "description": "List of manager identity references.",
            "example": []
        },
        "IDENTITYOWNER": {
            "type": "object (reference) or null",
            "description": "Owner of this identity (for service accounts, etc.).",
            "example": None
        },
        "EXPLICITOWNER": {
            "type": "array (references)",
            "description": "List of explicitly assigned owners.",
            "example": []
        },
        "EMPLOYMENTS": {
            "type": "array",
            "description": "List of employment records for this identity.",
            "example": []
        },

        # External identifiers
        "EMPLOYEEID": {
            "type": "string",
            "description": "Employee ID from HR system.",
            "example": "EMP12345"
        },
        "EXTERNALUSERID": {
            "type": "string",
            "description": "External user ID.",
            "example": ""
        },
        "OISID": {
            "type": "integer",
            "description": "Omada Identity Suite internal ID.",
            "example": 33
        },

        # Social/External login IDs
        "GOOGLEID": {
            "type": "string",
            "description": "Google account ID for SSO.",
            "example": ""
        },
        "LIVEID": {
            "type": "string",
            "description": "Microsoft Live ID for SSO.",
            "example": ""
        },
        "FACEBOOKID": {
            "type": "string",
            "description": "Facebook ID for SSO.",
            "example": ""
        },
        "LINKEDINID": {
            "type": "string",
            "description": "LinkedIn ID for SSO.",
            "example": ""
        },

        # Settings and preferences
        "LANGUAGEID": {
            "type": "string",
            "description": "Preferred language ID.",
            "example": "en-US"
        },
        "TIMEZONE": {
            "type": "object (reference) or null",
            "description": "Preferred timezone.",
            "example": None
        },
        "NEWSLETTERFREQUENCY": {
            "type": "object (reference) or null",
            "description": "Newsletter frequency preference.",
            "example": None
        },
        "PERSONALINTERESTS": {
            "type": "array",
            "description": "Personal interests for personalization.",
            "example": []
        },

        # Security
        "INITIALPASSWORD": {
            "type": "string",
            "description": "Initial password (typically empty after first login).",
            "example": ""
        },
        "PWR_LOCKOUT": {
            "type": "datetime or null",
            "description": "Password reset lockout timestamp.",
            "example": None
        },

        # Terms and compliance
        "TERMSDOCPENDINGACCEPTANCE": {
            "type": "object or null",
            "description": "Terms document pending acceptance.",
            "example": None
        },
        "TERMSDOCACCEPTANCES": {
            "type": "array",
            "description": "List of accepted terms documents.",
            "example": []
        },

        # Custom/Extended fields
        "CLT_TAGS": {
            "type": "array",
            "description": "Client-specific tags for categorization.",
            "example": []
        },

        # Technical fields
        "CurrentVersionId": {
            "type": "integer",
            "description": "Current version ID for optimistic concurrency.",
            "example": 1048876
        },
        "ODWBUSIKEY": {
            "type": "string",
            "description": "Business key for data warehouse integration.",
            "example": "1_<id>1025952</id>"
        }
    },
    "important_notes": {
        "UId_vs_Id_vs_IDENTITYID": "When using GraphQL tools like get_calculated_assignments_detailed, ALWAYS use the UId field (GUID format), NOT the Id (integer) or IDENTITYID (string username). This is a common mistake.",
        "example_workflow": "1. Query identity by email/name using query_omada_identity, 2. Extract the UId field from the result, 3. Use that UId in identity_ids parameter for get_calculated_assignments_detailed"
    },
    "common_queries": {
        "get_by_id": "Use query_omada_identity with filter_condition=\"Id eq {id}\"",
        "get_by_uid": "Use query_omada_identity with filter_condition=\"UId eq '{uid}'\"",
        "get_by_email": "Use query_omada_identity with filter_condition=\"EMAIL eq '{email}'\"",
        "get_by_name": "Use query_omada_identity with filter_condition=\"contains(LASTNAME, '{name}')\" or \"contains(DisplayName, '{name}')\"",
        "get_by_identity_id": "Use query_omada_identity with filter_condition=\"IDENTITYID eq '{identity_id}'\"",
        "get_assignments": "First get the identity's UId, then use query_calculated_assignments or get_calculated_assignments_detailed with identity_ids parameter"
    }
}


def register_schemas(mcp):
    """Register MCP resources for entity schema definitions."""

    @mcp.resource("schema://omada/resource")
    def get_resource_schema() -> str:
        """
        Schema definition for the Omada Resource entity.

        Returns the complete field definitions, types, descriptions, and examples
        for the Resource entity used in Omada Identity. Use this to understand
        the data structure when working with resources/roles/permissions.
        """
        return json.dumps(RESOURCE_SCHEMA, indent=2)

    @mcp.resource("schema://omada/identity")
    def get_identity_schema() -> str:
        """
        Schema definition for the Omada Identity entity.

        Returns the complete field definitions, types, descriptions, and examples
        for the Identity entity used in Omada Identity. Use this to understand
        the data structure when working with identities/users/people.
        """
        return json.dumps(IDENTITY_SCHEMA, indent=2)

    @mcp.resource("schema://omada/entities")
    def get_all_schemas() -> str:
        """
        List of all available Omada entity schemas.

        Returns a summary of all entity schemas available via schema://omada/{entity}.
        """
        return json.dumps({
            "available_schemas": [
                {
                    "uri": "schema://omada/resource",
                    "entity": "Resource",
                    "description": "Resources, roles, permissions that can be assigned to identities"
                },
                {
                    "uri": "schema://omada/identity",
                    "entity": "Identity",
                    "description": "People, users, service accounts in the identity system"
                }
            ],
            "usage": "Fetch a schema URI to get complete field definitions, types, and examples"
        }, indent=2)
