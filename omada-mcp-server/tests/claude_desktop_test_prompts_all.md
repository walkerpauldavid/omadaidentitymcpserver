# Omada MCP Server - Test Questions

Generated: 2026-02-25 14:41
Total questions: 53 across 9 categories

## Instructions

This file contains test questions for the Omada MCP server.
Please work through each question below **one at a time** using
the connected Omada MCP tools. For each question:

1. Read the question and the expected MCP tools listed
2. Execute the question by calling the appropriate Omada MCP tools
3. Record the result: PASS (tool returned data), FAIL (error or no data),
   or SKIP (tool not available or question not applicable)
4. Note any errors, unexpected behaviour, or observations
5. Move to the next question

After completing all questions, provide a **summary table** with:
- Total questions attempted
- PASS / FAIL / SKIP counts per category
- Any recurring errors or patterns
- Recommendations for improvement

**Important:** Do NOT stop after the first error. Continue through all
questions so we get a complete picture of what works and what doesn't.

---

## ACCESS REQUESTS (8 questions)

### Question 1: I need to request VPN access for john.smith@company.com

**Expected tools:** query_omada_identity, get_identity_contexts, get_requestable_resources, create_access_request
**MCP prompt:** request_access_workflow
**WARNING:** This question involves a WRITE operation. Execute with caution or skip if running in read-only mode.

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 2: Show me all recent access requests

**Expected tools:** get_access_requests

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 3: What resources can I request for myself?

**Expected tools:** get_requestable_resources
**MCP prompt:** request_access_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 4: Request access to the Document Management system for three new employees in my team

**Expected tools:** query_omada_identity, get_identity_contexts, get_requestable_resources, create_access_request
**MCP prompt:** bulk_access_request_workflow
**WARNING:** This question involves a WRITE operation. Execute with caution or skip if running in read-only mode.

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 5: What business contexts are available for user emma.taylor@company.com?

**Expected tools:** query_omada_identity, get_identity_contexts
**MCP prompt:** identity_context_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 6: Show me who I can request access on behalf of

**Expected tools:** get_identities_for_beneficiary

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 7: What resources are available in the Active Directory system for John Smith?

**Expected tools:** query_omada_identity, get_resources_for_beneficiary
**MCP prompt:** request_access_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 8: Check the status of access request ID 12345

**Expected tools:** get_access_requests_by_ids

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## ADMIN (6 questions)

### Question 9: What fields are available on the Identity entity?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** schema_reference_guide

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 10: Is the Omada server configured correctly?

**Expected tools:** check_omada_config
**MCP prompt:** troubleshooting_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 11: What version of the GraphQL API is available?

**Expected tools:** get_graphql_api_versions

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 12: Is the MCP server responding?

**Expected tools:** ping

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 13: What OData limitations should I know about when querying Omada?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** schema_reference_guide

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 14: My query is returning empty results, what could be wrong?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** troubleshooting_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## APPROVALS (7 questions)

### Question 15: Do I have any pending approvals?

**Expected tools:** get_pending_approvals
**MCP prompt:** approve_requests_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 16: Show me all access requests waiting for my manager approval

**Expected tools:** get_pending_approvals
**MCP prompt:** approve_requests_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 17: Approve the pending request for John Smith's VPN access

**Expected tools:** get_pending_approvals, get_approval_details, make_approval_decision
**MCP prompt:** approve_requests_workflow
**WARNING:** This question involves a WRITE operation. Execute with caution or skip if running in read-only mode.

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 18: Reject the access request for Emma Taylor with reason 'Not justified'

**Expected tools:** get_pending_approvals, get_approval_details, make_approval_decision
**MCP prompt:** approve_requests_workflow
**WARNING:** This question involves a WRITE operation. Execute with caution or skip if running in read-only mode.

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 19: How many approvals are pending at each workflow step?

**Expected tools:** get_access_approval_workflow_steps_question_count

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 20: What is the approval workflow status for request 67890?

**Expected tools:** get_approval_workflow_status

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 21: Show me the detailed approval survey questions waiting for resource owner approval

**Expected tools:** get_access_request_approval_survey_questions

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## ASSIGNMENTS (6 questions)

### Question 22: Show me all the resource assignments for john.smith@company.com

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** review_assignments_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 23: Does Robert Wolf have any compliance violations?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** review_assignments_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 24: List all assignments that are NOT APPROVED for user emma.taylor@company.com

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 25: How many total calculated assignments exist in the system?

**Expected tools:** query_calculated_assignments

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 26: Show me the assignment details including Identity and Resource for the top 50 assignments

**Expected tools:** query_calculated_assignments

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 27: Are there any users in Finance with compliance violations?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## AUTHENTICATION (2 questions)

### Question 28: How do I authenticate to use the Omada tools?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** authentication_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 29: I need a bearer token to access Omada

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** authentication_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## COMPLIANCE (3 questions)

### Question 30: Show me the compliance workbench data

**Expected tools:** get_compliance_workbench_data
**MCP prompt:** compliance_audit_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 31: What is the overall compliance status for my team?

**Expected tools:** get_compliance_workbench_survey_and_compliance_status
**MCP prompt:** compliance_audit_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 32: Are there any compliance violations in the IT department?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## IDENTITY (9 questions)

### Question 33: Find the identity for HANULR@54mv4c.onmicrosoft.com

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 34: Look up all users with the last name Wolf

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 35: Who is employee EMP12345?

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 36: How many active identities are in the Finance department?

**Expected tools:** query_omada_identity

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 37: List the first 20 identities in the system

**Expected tools:** get_all_omada_identities

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 38: Search for a user named Emma whose email contains 'onmicrosoft.com'

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 39: Find the user with login ID ROBWOL

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 40: Compare the access of John Smith and Jane Doe side by side

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compare_identities_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 41: What resources does Robert Wolf have that Emma Taylor doesn't?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compare_identities_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## ORGUNITS (7 questions)

### Question 42: Show me all organizational units

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 43: What departments exist in the organisation?

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 44: Who manages the Finance department?

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 45: Show me the org unit hierarchy - which OrgUnits are children of the root Organisation?

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 46: Find the OrgUnit with OUID 'FINANCE' and show its manager and owner

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 47: Which org units have explicit owners assigned?

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 48: What is the Active Directory OU path for the Engineering department?

**Expected tools:** query_omada_orgunits

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## RESOURCES (5 questions)

### Question 49: List all Application Roles in the system

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 50: How many resources are in the Document Management system?

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 51: Find a resource named 'Domain Admins'

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 52: Show me all active resources with a risk score above 100

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

### Question 53: What resource types exist in the system?

**Expected tools:** query_omada_entity
**MCP prompt:** resource_discovery_workflow

**Result:** _[PASS / FAIL / SKIP]_

**Response summary:**

```
(Claude: fill in the tool response or error here)
```

---

## Summary

After completing all questions above, fill in this summary:

| Category | Total | PASS | FAIL | SKIP |
|----------|-------|------|------|------|
| ACCESS REQUESTS | 8 | | | |
| ADMIN | 6 | | | |
| APPROVALS | 7 | | | |
| ASSIGNMENTS | 6 | | | |
| AUTHENTICATION | 2 | | | |
| COMPLIANCE | 3 | | | |
| IDENTITY | 9 | | | |
| ORGUNITS | 7 | | | |
| RESOURCES | 5 | | | |
| **TOTAL** | **53** | | | |

### Recurring Errors

_List any errors that appeared across multiple questions._

### Recommendations

_List any improvements or fixes suggested by the test results._

