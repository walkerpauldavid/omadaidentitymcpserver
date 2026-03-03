"""
Sample User Questions for the Omada MCP Server
================================================

These are realistic questions an end user would ask Claude Desktop
when the Omada MCP server is connected. Organised by category and
mapped to the MCP tools/prompts they exercise.

Usage:
    python tests/sample_user_questions.py              # Print all questions
    python tests/sample_user_questions.py --category identity   # Filter by category
    python tests/sample_user_questions.py --random 5            # Pick 5 random questions
    python tests/sample_user_questions.py --json                # Output as JSON

Claude Desktop integration (attach the generated file to Claude Desktop):
    python tests/sample_user_questions.py --claude-desktop > test_prompts.md
    python tests/sample_user_questions.py --claude-desktop --category identity > identity_test.md
    python tests/sample_user_questions.py --claude-desktop --safe > readonly_test.md
    python tests/sample_user_questions.py --claude-desktop --random 10 > random_10_test.md
"""

import argparse
import json
import random
import sys
from datetime import datetime

# Tools that create or modify data in Omada  --safe flag excludes these
MUTATING_TOOLS = {"create_access_request", "make_approval_decision"}

SAMPLE_QUESTIONS = [
    # =========================================================================
    # IDENTITY LOOKUP
    # Tools: query_omada_identity, query_omada_entity, get_all_omada_identities
    # Prompt: search_identity_workflow
    # =========================================================================
    {
        "category": "identity",
        "question": "Find the identity for HANULR@54mv4c.onmicrosoft.com",
        "tools": ["query_omada_identity"],
        "prompt": "search_identity_workflow",
    },
    {
        "category": "identity",
        "question": "Look up all users with the last name Wolf",
        "tools": ["query_omada_identity"],
        "prompt": "search_identity_workflow",
    },
    {
        "category": "identity",
        "question": "Who is employee EMP12345?",
        "tools": ["query_omada_identity"],
        "prompt": "search_identity_workflow",
    },
    {
        "category": "identity",
        "question": "How many active identities are in the Finance department?",
        "tools": ["query_omada_identity"],
        "prompt": None,
    },
    {
        "category": "identity",
        "question": "List the first 20 identities in the system",
        "tools": ["get_all_omada_identities"],
        "prompt": None,
    },
    {
        "category": "identity",
        "question": "Search for a user named Emma whose email contains 'onmicrosoft.com'",
        "tools": ["query_omada_identity"],
        "prompt": "search_identity_workflow",
    },
    {
        "category": "identity",
        "question": "Find the user with login ID ROBWOL",
        "tools": ["query_omada_identity"],
        "prompt": "search_identity_workflow",
    },

    # =========================================================================
    # IDENTITY COMPARISON
    # Tools: query_omada_identity, get_calculated_assignments_detailed
    # Prompt: compare_identities_workflow
    # =========================================================================
    {
        "category": "identity",
        "question": "Compare the access of John Smith and Jane Doe side by side",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "compare_identities_workflow",
    },
    {
        "category": "identity",
        "question": "What resources does Robert Wolf have that Emma Taylor doesn't?",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "compare_identities_workflow",
    },

    # =========================================================================
    # RESOURCE ASSIGNMENTS & COMPLIANCE
    # Tools: get_calculated_assignments_detailed, query_calculated_assignments
    # Prompt: review_assignments_workflow, compliance_audit_workflow
    # =========================================================================
    {
        "category": "assignments",
        "question": "Show me all the resource assignments for john.smith@company.com",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "review_assignments_workflow",
    },
    {
        "category": "assignments",
        "question": "Does Robert Wolf have any compliance violations?",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "review_assignments_workflow",
    },
    {
        "category": "assignments",
        "question": "List all assignments that are NOT APPROVED for user emma.taylor@company.com",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "compliance_audit_workflow",
    },
    {
        "category": "assignments",
        "question": "How many total calculated assignments exist in the system?",
        "tools": ["query_calculated_assignments"],
        "prompt": None,
    },
    {
        "category": "assignments",
        "question": "Show me the assignment details including Identity and Resource for the top 50 assignments",
        "tools": ["query_calculated_assignments"],
        "prompt": None,
    },
    {
        "category": "assignments",
        "question": "Are there any users in Finance with compliance violations?",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "compliance_audit_workflow",
    },

    # =========================================================================
    # ACCESS REQUESTS
    # Tools: get_access_requests, create_access_request, get_resources_for_beneficiary,
    #        get_requestable_resources, get_identities_for_beneficiary, get_identity_contexts
    # Prompt: request_access_workflow, bulk_access_request_workflow
    # =========================================================================
    {
        "category": "access_requests",
        "question": "I need to request VPN access for john.smith@company.com",
        "tools": ["query_omada_identity", "get_identity_contexts", "get_requestable_resources", "create_access_request"],
        "prompt": "request_access_workflow",
        "is_mutating": True,
    },
    {
        "category": "access_requests",
        "question": "Show me all recent access requests",
        "tools": ["get_access_requests"],
        "prompt": None,
    },
    {
        "category": "access_requests",
        "question": "What resources can I request for myself?",
        "tools": ["get_requestable_resources"],
        "prompt": "request_access_workflow",
    },
    {
        "category": "access_requests",
        "question": "Request access to the Document Management system for three new employees in my team",
        "tools": ["query_omada_identity", "get_identity_contexts", "get_requestable_resources", "create_access_request"],
        "prompt": "bulk_access_request_workflow",
        "is_mutating": True,
    },
    {
        "category": "access_requests",
        "question": "What business contexts are available for user emma.taylor@company.com?",
        "tools": ["query_omada_identity", "get_identity_contexts"],
        "prompt": "identity_context_workflow",
    },
    {
        "category": "access_requests",
        "question": "Show me who I can request access on behalf of",
        "tools": ["get_identities_for_beneficiary"],
        "prompt": None,
    },
    {
        "category": "access_requests",
        "question": "What resources are available in the Active Directory system for John Smith?",
        "tools": ["query_omada_identity", "get_resources_for_beneficiary"],
        "prompt": "request_access_workflow",
    },
    {
        "category": "access_requests",
        "question": "Check the status of access request ID 12345",
        "tools": ["get_access_requests_by_ids"],
        "prompt": None,
    },

    # =========================================================================
    # APPROVALS
    # Tools: get_pending_approvals, make_approval_decision, get_approval_details,
    #        get_approval_workflow_status, get_access_request_approval_survey_questions,
    #        get_access_approval_workflow_steps_question_count
    # Prompt: approve_requests_workflow
    # =========================================================================
    {
        "category": "approvals",
        "question": "Do I have any pending approvals?",
        "tools": ["get_pending_approvals"],
        "prompt": "approve_requests_workflow",
    },
    {
        "category": "approvals",
        "question": "Show me all access requests waiting for my manager approval",
        "tools": ["get_pending_approvals"],
        "prompt": "approve_requests_workflow",
    },
    {
        "category": "approvals",
        "question": "Approve the pending request for John Smith's VPN access",
        "tools": ["get_pending_approvals", "get_approval_details", "make_approval_decision"],
        "prompt": "approve_requests_workflow",
        "is_mutating": True,
    },
    {
        "category": "approvals",
        "question": "Reject the access request for Emma Taylor with reason 'Not justified'",
        "tools": ["get_pending_approvals", "get_approval_details", "make_approval_decision"],
        "prompt": "approve_requests_workflow",
        "is_mutating": True,
    },
    {
        "category": "approvals",
        "question": "How many approvals are pending at each workflow step?",
        "tools": ["get_access_approval_workflow_steps_question_count"],
        "prompt": None,
    },
    {
        "category": "approvals",
        "question": "What is the approval workflow status for request 67890?",
        "tools": ["get_approval_workflow_status"],
        "prompt": None,
    },
    {
        "category": "approvals",
        "question": "Show me the detailed approval survey questions waiting for resource owner approval",
        "tools": ["get_access_request_approval_survey_questions"],
        "prompt": None,
    },

    # =========================================================================
    # RESOURCES
    # Tools: query_omada_resources, query_omada_entity
    # Prompt: resource_discovery_workflow
    # =========================================================================
    {
        "category": "resources",
        "question": "List all Application Roles in the system",
        "tools": ["query_omada_resources"],
        "prompt": "resource_discovery_workflow",
    },
    {
        "category": "resources",
        "question": "How many resources are in the Document Management system?",
        "tools": ["query_omada_resources"],
        "prompt": "resource_discovery_workflow",
    },
    {
        "category": "resources",
        "question": "Find a resource named 'Domain Admins'",
        "tools": ["query_omada_resources"],
        "prompt": "resource_discovery_workflow",
    },
    {
        "category": "resources",
        "question": "Show me all active resources with a risk score above 100",
        "tools": ["query_omada_resources"],
        "prompt": "resource_discovery_workflow",
    },
    {
        "category": "resources",
        "question": "What resource types exist in the system?",
        "tools": ["query_omada_entity"],
        "prompt": "resource_discovery_workflow",
    },

    # =========================================================================
    # ORG UNITS
    # Tools: query_omada_orgunits
    # =========================================================================
    {
        "category": "orgunits",
        "question": "Show me all organizational units",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "What departments exist in the organisation?",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "Who manages the Finance department?",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "Show me the org unit hierarchy - which OrgUnits are children of the root Organisation?",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "Find the OrgUnit with OUID 'FINANCE' and show its manager and owner",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "Which org units have explicit owners assigned?",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },
    {
        "category": "orgunits",
        "question": "What is the Active Directory OU path for the Engineering department?",
        "tools": ["query_omada_orgunits"],
        "prompt": None,
    },

    # =========================================================================
    # COMPLIANCE
    # Tools: get_compliance_workbench_data, get_compliance_workbench_survey_and_compliance_status
    # Prompt: compliance_audit_workflow
    # =========================================================================
    {
        "category": "compliance",
        "question": "Show me the compliance workbench data",
        "tools": ["get_compliance_workbench_data"],
        "prompt": "compliance_audit_workflow",
    },
    {
        "category": "compliance",
        "question": "What is the overall compliance status for my team?",
        "tools": ["get_compliance_workbench_survey_and_compliance_status"],
        "prompt": "compliance_audit_workflow",
    },
    {
        "category": "compliance",
        "question": "Are there any compliance violations in the IT department?",
        "tools": ["query_omada_identity", "get_calculated_assignments_detailed"],
        "prompt": "compliance_audit_workflow",
    },

    # =========================================================================
    # AUTHENTICATION
    # Prompt: authentication_workflow
    # =========================================================================
    {
        "category": "authentication",
        "question": "How do I authenticate to use the Omada tools?",
        "tools": [],
        "prompt": "authentication_workflow",
    },
    {
        "category": "authentication",
        "question": "I need a bearer token to access Omada",
        "tools": [],
        "prompt": "authentication_workflow",
    },

    # =========================================================================
    # SCHEMA / TROUBLESHOOTING / CONFIG
    # Tools: check_omada_config, get_graphql_api_versions, ping
    # Prompts: schema_reference_guide, troubleshooting_workflow
    # =========================================================================
    {
        "category": "admin",
        "question": "What fields are available on the Identity entity?",
        "tools": [],
        "prompt": "schema_reference_guide",
    },
    {
        "category": "admin",
        "question": "Is the Omada server configured correctly?",
        "tools": ["check_omada_config"],
        "prompt": "troubleshooting_workflow",
    },
    {
        "category": "admin",
        "question": "What version of the GraphQL API is available?",
        "tools": ["get_graphql_api_versions"],
        "prompt": None,
    },
    {
        "category": "admin",
        "question": "Is the MCP server responding?",
        "tools": ["ping"],
        "prompt": None,
    },
    {
        "category": "admin",
        "question": "What OData limitations should I know about when querying Omada?",
        "tools": [],
        "prompt": "schema_reference_guide",
    },
    {
        "category": "admin",
        "question": "My query is returning empty results, what could be wrong?",
        "tools": [],
        "prompt": "troubleshooting_workflow",
    },
]

CATEGORIES = sorted(set(q["category"] for q in SAMPLE_QUESTIONS))


def print_questions(questions: list, show_tools: bool = True):
    """Print questions grouped by category."""
    by_category = {}
    for q in questions:
        by_category.setdefault(q["category"], []).append(q)

    for cat in CATEGORIES:
        if cat not in by_category:
            continue
        items = by_category[cat]
        header = cat.upper().replace("_", " ")
        print(f"\n{'=' * 70}")
        print(f" {header} ({len(items)} questions)")
        print(f"{'=' * 70}")
        for i, q in enumerate(items, 1):
            print(f"\n  {i}. \"{q['question']}\"")
            if show_tools:
                if q["tools"]:
                    print(f"     Tools:  {', '.join(q['tools'])}")
                if q["prompt"]:
                    print(f"     Prompt: {q['prompt']}")

    print(f"\n{'=' * 70}")
    print(f" TOTAL: {len(questions)} sample questions across {len(by_category)} categories")
    print(f"{'=' * 70}")


def generate_claude_desktop_document(questions: list) -> str:
    """Generate a markdown document that Claude Desktop can process when attached.

    When this file is attached to a Claude Desktop conversation with the Omada
    MCP server connected, Claude will work through each question sequentially,
    call the appropriate MCP tools, and report a summary of results.
    """
    by_category = {}
    for q in questions:
        by_category.setdefault(q["category"], []).append(q)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(questions)
    cats = len(by_category)

    lines = []
    lines.append("# Omada MCP Server - Test Questions")
    lines.append("")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Total questions: {total} across {cats} categories")
    lines.append("")
    lines.append("## Instructions")
    lines.append("")
    lines.append("This file contains test questions for the Omada MCP server.")
    lines.append("Please work through each question below **one at a time** using")
    lines.append("the connected Omada MCP tools. For each question:")
    lines.append("")
    lines.append("1. Read the question and the expected MCP tools listed")
    lines.append("2. Execute the question by calling the appropriate Omada MCP tools")
    lines.append("3. Record the result: PASS (tool returned data), FAIL (error or no data),")
    lines.append("   or SKIP (tool not available or question not applicable)")
    lines.append("4. Note any errors, unexpected behaviour, or observations")
    lines.append("5. Move to the next question")
    lines.append("")
    lines.append("After completing all questions, provide a **summary table** with:")
    lines.append("- Total questions attempted")
    lines.append("- PASS / FAIL / SKIP counts per category")
    lines.append("- Any recurring errors or patterns")
    lines.append("- Recommendations for improvement")
    lines.append("")
    lines.append("**Important:** Do NOT stop after the first error. Continue through all")
    lines.append("questions so we get a complete picture of what works and what doesn't.")
    lines.append("")
    lines.append("---")
    lines.append("")

    question_num = 0
    for cat in CATEGORIES:
        if cat not in by_category:
            continue
        items = by_category[cat]
        header = cat.upper().replace("_", " ")
        lines.append(f"## {header} ({len(items)} questions)")
        lines.append("")

        for q in items:
            question_num += 1
            lines.append(f"### Question {question_num}: {q['question']}")
            lines.append("")
            if q["tools"]:
                lines.append(f"**Expected tools:** {', '.join(q['tools'])}")
            else:
                lines.append("**Expected tools:** None (prompt/guidance only)")
            if q.get("prompt"):
                lines.append(f"**MCP prompt:** {q['prompt']}")
            if q.get("is_mutating"):
                lines.append("**WARNING:** This question involves a WRITE operation. "
                             "Execute with caution or skip if running in read-only mode.")
            lines.append("")
            lines.append("**Result:** _[PASS / FAIL / SKIP]_")
            lines.append("")
            lines.append("**Response summary:**")
            lines.append("")
            lines.append("```")
            lines.append("(Claude: fill in the tool response or error here)")
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("After completing all questions above, fill in this summary:")
    lines.append("")
    lines.append("| Category | Total | PASS | FAIL | SKIP |")
    lines.append("|----------|-------|------|------|------|")
    for cat in CATEGORIES:
        if cat not in by_category:
            continue
        header = cat.upper().replace("_", " ")
        count = len(by_category[cat])
        lines.append(f"| {header} | {count} | | | |")
    lines.append(f"| **TOTAL** | **{total}** | | | |")
    lines.append("")
    lines.append("### Recurring Errors")
    lines.append("")
    lines.append("_List any errors that appeared across multiple questions._")
    lines.append("")
    lines.append("### Recommendations")
    lines.append("")
    lines.append("_List any improvements or fixes suggested by the test results._")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sample user questions for Omada MCP Server")
    parser.add_argument("--category", "-c", choices=CATEGORIES, help="Filter by category")
    parser.add_argument("--random", "-r", type=int, metavar="N", help="Pick N random questions")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--questions-only", "-q", action="store_true", help="Print only the question text, one per line")
    parser.add_argument("--claude-desktop", action="store_true",
                        help="Generate a markdown document to attach to Claude Desktop")
    parser.add_argument("--safe", action="store_true",
                        help="Exclude questions that create or modify data (use with --claude-desktop)")
    args = parser.parse_args()

    questions = SAMPLE_QUESTIONS
    if args.category:
        questions = [q for q in questions if q["category"] == args.category]

    if args.safe:
        questions = [q for q in questions if not q.get("is_mutating")]

    if args.random:
        questions = random.sample(questions, min(args.random, len(questions)))

    if args.claude_desktop:
        print(generate_claude_desktop_document(questions))
    elif args.json:
        print(json.dumps(questions, indent=2))
    elif args.questions_only:
        for q in questions:
            print(q["question"])
    else:
        print_questions(questions)


if __name__ == "__main__":
    main()
