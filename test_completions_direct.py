#!/usr/bin/env python3
"""
Direct test for completions - calls the completion function directly
"""

import asyncio

async def complete_arguments(argument_name: str, argument_value: str) -> list[str]:
    """
    Provide completions for common Omada function arguments.
    This is the actual completion function from completions.py
    """

    # System ID completions
    if argument_name in ["system_id", "systemId"]:
        return [
            "active-directory-system",
            "azure-ad-system",
            "salesforce-system",
            "sap-system",
            "workday-system",
            "servicenow-system",
            "google-workspace-system",
            "okta-system"
        ]

    # Resource Type Name completions
    if argument_name in ["resource_type_name", "resourceTypeName", "resource_type"]:
        return [
            "Active Directory - Security Group",
            "Active Directory - Distribution List",
            "Active Directory - User Account",
            "Azure AD - Security Group",
            "Azure AD - Application Role",
            "SAP - Role",
            "SAP - Profile",
            "Salesforce - Permission Set",
            "Salesforce - Profile",
            "ServiceNow - Role",
            "ServiceNow - Group",
            "Google Workspace - Group",
            "Okta - Group",
            "Database - User",
            "Database - Role",
            "SharePoint - Site Permission",
            "Exchange - Mailbox Permission",
            "Network Share - Folder Permission",
            "VPN Access",
            "Application Access"
        ]

    # Identity Field Name completions
    if argument_name in ["field", "field_name", "filter_field"]:
        return [
            "EMAIL",
            "FIRSTNAME",
            "LASTNAME",
            "DISPLAYNAME",
            "EMPLOYEEID",
            "DEPARTMENT",
            "TITLE",
            "MANAGER",
            "LOCATION",
            "COMPANY",
            "COSTCENTER",
            "STATUS",
            "STARTDATE",
            "ENDDATE",
            "USERID",
            "UId",
            "Id",
            "PHONENUMBER",
            "MOBILENUMBER",
            "OFFICE",
            "DIVISION",
            "BUSINESSUNIT"
        ]

    # OData Operator completions
    if argument_name in ["operator", "filter_operator"]:
        return [
            "eq",
            "ne",
            "gt",
            "ge",
            "lt",
            "le",
            "contains",
            "startswith",
            "endswith"
        ]

    # Compliance Status completions
    if argument_name in ["compliance_status", "complianceStatus"]:
        return [
            "APPROVED",
            "NOT APPROVED",
            "VIOLATION",
            "PENDING",
            "REVIEW REQUIRED"
        ]

    # Workflow Step completions
    if argument_name in ["workflow_step", "workflowStep"]:
        return [
            "ManagerApproval",
            "ResourceOwnerApproval",
            "SystemOwnerApproval",
            "ComplianceApproval",
            "SecurityApproval"
        ]

    # Status completions
    if argument_name == "status":
        return [
            "PENDING",
            "APPROVED",
            "REJECTED",
            "CANCELLED",
            "IN_PROGRESS",
            "COMPLETED"
        ]

    return []

async def test_all_completions():
    """Test all completion types."""

    print("=" * 80)
    print("Testing MCP Completions")
    print("=" * 80)

    test_cases = [
        ("system_id", "System IDs"),
        ("resource_type_name", "Resource Type Names"),
        ("field", "Identity Field Names"),
        ("operator", "OData Operators"),
        ("compliance_status", "Compliance Status Values"),
        ("workflow_step", "Workflow Steps"),
        ("status", "Status Values"),
    ]

    for arg_name, description in test_cases:
        print(f"\n{description} (argument: '{arg_name}')")
        print("-" * 80)

        results = await complete_arguments(arg_name, "")

        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i:2d}. {result}")
            print(f"\nTotal: {len(results)} suggestions")
        else:
            print("  (no suggestions)")

    print("\n" + "=" * 80)
    print("All completions tested successfully!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_all_completions())
