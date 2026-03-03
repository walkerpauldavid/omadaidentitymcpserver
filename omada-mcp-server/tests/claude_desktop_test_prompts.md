# Omada MCP Server - Test Questions

Generated: 2026-02-25 14:40
Total questions: 47 across 9 categories

## Instructions

This file contains test questions for the Omada MCP server.
Please work through each question below **one at a time** using
the connected Omada MCP tools. For each question:

1. Echo the question text and expected tools to the screen
2. Call the MCP tool(s) to answer the question
3. Echo the HTTP request URL and response status code to the screen
4. Record the result as PASS, FAIL, or SKIP
5. Move to the next question

Each question below includes these steps explicitly. Follow them exactly.

After completing all questions, provide a **summary table** with:
- Total questions attempted
- PASS / FAIL / SKIP counts per category
- Any recurring errors or patterns
- Recommendations for improvement

**Important:** Do NOT stop after the first error. Continue through all
questions so we get a complete picture of what works and what doesn't.

---

## ACCESS REQUESTS (6 questions)

### Question 1: Show me all recent access requests

**Expected tools:** get_access_requests

**Steps for this test:**
1. Echo to screen: **Question 1:** "Show me all recent access requests"
2. Echo to screen: **Expected tools:** get_access_requests
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 2: What resources can I request for myself?

**Expected tools:** get_requestable_resources
**MCP prompt:** request_access_workflow

**Steps for this test:**
1. Echo to screen: **Question 2:** "What resources can I request for myself?"
2. Echo to screen: **Expected tools:** get_requestable_resources
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 3: What business contexts are available for user emma.taylor@company.com?

**Expected tools:** query_omada_identity, get_identity_contexts
**MCP prompt:** identity_context_workflow

**Steps for this test:**
1. Echo to screen: **Question 3:** "What business contexts are available for user emma.taylor@company.com?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_identity_contexts
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 4: Show me who I can request access on behalf of

**Expected tools:** get_identities_for_beneficiary

**Steps for this test:**
1. Echo to screen: **Question 4:** "Show me who I can request access on behalf of"
2. Echo to screen: **Expected tools:** get_identities_for_beneficiary
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 5: What resources are available in the Active Directory system for John Smith?

**Expected tools:** query_omada_identity, get_resources_for_beneficiary
**MCP prompt:** request_access_workflow

**Steps for this test:**
1. Echo to screen: **Question 5:** "What resources are available in the Active Directory system for John Smith?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_resources_for_beneficiary
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 6: Check the status of access request ID 12345

**Expected tools:** get_access_requests_by_ids

**Steps for this test:**
1. Echo to screen: **Question 6:** "Check the status of access request ID 12345"
2. Echo to screen: **Expected tools:** get_access_requests_by_ids
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## ADMIN (4 questions)

### Question 7: What fields are available on the Identity entity?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** schema_reference_guide

**Steps for this test:**
1. Echo to screen: **Question 7:** "What fields are available on the Identity entity?"
2. Echo to screen: **Expected tools:** None (prompt/guidance only)
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 8: What version of the GraphQL API is available?

**Expected tools:** get_graphql_api_versions

**Steps for this test:**
1. Echo to screen: **Question 8:** "What version of the GraphQL API is available?"
2. Echo to screen: **Expected tools:** get_graphql_api_versions
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 9: Is the MCP server responding?

**Expected tools:** ping

**Steps for this test:**
1. Echo to screen: **Question 9:** "Is the MCP server responding?"
2. Echo to screen: **Expected tools:** ping
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 10: What OData limitations should I know about when querying Omada?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** schema_reference_guide

**Steps for this test:**
1. Echo to screen: **Question 10:** "What OData limitations should I know about when querying Omada?"
2. Echo to screen: **Expected tools:** None (prompt/guidance only)
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## APPROVALS (5 questions)

### Question 11: Do I have any pending approvals?

**Expected tools:** get_pending_approvals
**MCP prompt:** approve_requests_workflow

**Steps for this test:**
1. Echo to screen: **Question 11:** "Do I have any pending approvals?"
2. Echo to screen: **Expected tools:** get_pending_approvals
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 12: Show me all access requests waiting for my manager approval

**Expected tools:** get_pending_approvals
**MCP prompt:** approve_requests_workflow

**Steps for this test:**
1. Echo to screen: **Question 12:** "Show me all access requests waiting for my manager approval"
2. Echo to screen: **Expected tools:** get_pending_approvals
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 13: How many approvals are pending at each workflow step?

**Expected tools:** get_access_approval_workflow_steps_question_count

**Steps for this test:**
1. Echo to screen: **Question 13:** "How many approvals are pending at each workflow step?"
2. Echo to screen: **Expected tools:** get_access_approval_workflow_steps_question_count
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 14: What is the approval workflow status for request 67890?

**Expected tools:** get_approval_workflow_status

**Steps for this test:**
1. Echo to screen: **Question 14:** "What is the approval workflow status for request 67890?"
2. Echo to screen: **Expected tools:** get_approval_workflow_status
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 15: Show me the detailed approval survey questions waiting for resource owner approval

**Expected tools:** get_access_request_approval_survey_questions

**Steps for this test:**
1. Echo to screen: **Question 15:** "Show me the detailed approval survey questions waiting for resource owner approval"
2. Echo to screen: **Expected tools:** get_access_request_approval_survey_questions
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## ASSIGNMENTS (6 questions)

### Question 16: Show me all the resource assignments for john.smith@company.com

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** review_assignments_workflow

**Steps for this test:**
1. Echo to screen: **Question 16:** "Show me all the resource assignments for john.smith@company.com"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 17: Does Robert Wolf have any compliance violations?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** review_assignments_workflow

**Steps for this test:**
1. Echo to screen: **Question 17:** "Does Robert Wolf have any compliance violations?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 18: List all assignments that are NOT APPROVED for user emma.taylor@company.com

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Steps for this test:**
1. Echo to screen: **Question 18:** "List all assignments that are NOT APPROVED for user emma.taylor@company.com"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 19: How many total calculated assignments exist in the system?

**Expected tools:** query_calculated_assignments

**Steps for this test:**
1. Echo to screen: **Question 19:** "How many total calculated assignments exist in the system?"
2. Echo to screen: **Expected tools:** query_calculated_assignments
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 20: Show me the assignment details including Identity and Resource for the top 50 assignments

**Expected tools:** query_calculated_assignments

**Steps for this test:**
1. Echo to screen: **Question 20:** "Show me the assignment details including Identity and Resource for the top 50 assignments"
2. Echo to screen: **Expected tools:** query_calculated_assignments
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 21: Are there any users in Finance with compliance violations?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Steps for this test:**
1. Echo to screen: **Question 21:** "Are there any users in Finance with compliance violations?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## AUTHENTICATION (2 questions)

### Question 22: How do I authenticate to use the Omada tools?

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** authentication_workflow

**Steps for this test:**
1. Echo to screen: **Question 22:** "How do I authenticate to use the Omada tools?"
2. Echo to screen: **Expected tools:** None (prompt/guidance only)
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 23: I need a bearer token to access Omada

**Expected tools:** None (prompt/guidance only)
**MCP prompt:** authentication_workflow

**Steps for this test:**
1. Echo to screen: **Question 23:** "I need a bearer token to access Omada"
2. Echo to screen: **Expected tools:** None (prompt/guidance only)
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## COMPLIANCE (3 questions)

### Question 24: Show me the compliance workbench data

**Expected tools:** get_compliance_workbench_data
**MCP prompt:** compliance_audit_workflow

**Steps for this test:**
1. Echo to screen: **Question 24:** "Show me the compliance workbench data"
2. Echo to screen: **Expected tools:** get_compliance_workbench_data
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 25: What is the overall compliance status for my team?

**Expected tools:** get_compliance_workbench_survey_and_compliance_status
**MCP prompt:** compliance_audit_workflow

**Steps for this test:**
1. Echo to screen: **Question 25:** "What is the overall compliance status for my team?"
2. Echo to screen: **Expected tools:** get_compliance_workbench_survey_and_compliance_status
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 26: Are there any compliance violations in the IT department?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compliance_audit_workflow

**Steps for this test:**
1. Echo to screen: **Question 26:** "Are there any compliance violations in the IT department?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## IDENTITY (9 questions)

### Question 27: Find the identity for HANULR@54mv4c.onmicrosoft.com

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Steps for this test:**
1. Echo to screen: **Question 27:** "Find the identity for HANULR@54mv4c.onmicrosoft.com"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 28: Look up all users with the last name Wolf

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Steps for this test:**
1. Echo to screen: **Question 28:** "Look up all users with the last name Wolf"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 29: Who is employee EMP12345?

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Steps for this test:**
1. Echo to screen: **Question 29:** "Who is employee EMP12345?"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 30: How many active identities are in the Finance department?

**Expected tools:** query_omada_identity

**Steps for this test:**
1. Echo to screen: **Question 30:** "How many active identities are in the Finance department?"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 31: List the first 20 identities in the system

**Expected tools:** get_all_omada_identities

**Steps for this test:**
1. Echo to screen: **Question 31:** "List the first 20 identities in the system"
2. Echo to screen: **Expected tools:** get_all_omada_identities
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 32: Search for a user named Emma whose email contains 'onmicrosoft.com'

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Steps for this test:**
1. Echo to screen: **Question 32:** "Search for a user named Emma whose email contains 'onmicrosoft.com'"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 33: Find the user with login ID ROBWOL

**Expected tools:** query_omada_identity
**MCP prompt:** search_identity_workflow

**Steps for this test:**
1. Echo to screen: **Question 33:** "Find the user with login ID ROBWOL"
2. Echo to screen: **Expected tools:** query_omada_identity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 34: Compare the access of John Smith and Jane Doe side by side

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compare_identities_workflow

**Steps for this test:**
1. Echo to screen: **Question 34:** "Compare the access of John Smith and Jane Doe side by side"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 35: What resources does Robert Wolf have that Emma Taylor doesn't?

**Expected tools:** query_omada_identity, get_calculated_assignments_detailed
**MCP prompt:** compare_identities_workflow

**Steps for this test:**
1. Echo to screen: **Question 35:** "What resources does Robert Wolf have that Emma Taylor doesn't?"
2. Echo to screen: **Expected tools:** query_omada_identity, get_calculated_assignments_detailed
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## ORGUNITS (7 questions)

### Question 36: Show me all organizational units

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 36:** "Show me all organizational units"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 37: What departments exist in the organisation?

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 37:** "What departments exist in the organisation?"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 38: Who manages the Finance department?

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 38:** "Who manages the Finance department?"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 39: Show me the org unit hierarchy - which OrgUnits are children of the root Organisation?

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 39:** "Show me the org unit hierarchy - which OrgUnits are children of the root Organisation?"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 40: Find the OrgUnit with OUID 'FINANCE' and show its manager and owner

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 40:** "Find the OrgUnit with OUID 'FINANCE' and show its manager and owner"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 41: Which org units have explicit owners assigned?

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 41:** "Which org units have explicit owners assigned?"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 42: What is the Active Directory OU path for the Engineering department?

**Expected tools:** query_omada_orgunits

**Steps for this test:**
1. Echo to screen: **Question 42:** "What is the Active Directory OU path for the Engineering department?"
2. Echo to screen: **Expected tools:** query_omada_orgunits
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## RESOURCES (5 questions)

### Question 43: List all Application Roles in the system

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Steps for this test:**
1. Echo to screen: **Question 43:** "List all Application Roles in the system"
2. Echo to screen: **Expected tools:** query_omada_resources
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 44: How many resources are in the Document Management system?

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Steps for this test:**
1. Echo to screen: **Question 44:** "How many resources are in the Document Management system?"
2. Echo to screen: **Expected tools:** query_omada_resources
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 45: Find a resource named 'Domain Admins'

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Steps for this test:**
1. Echo to screen: **Question 45:** "Find a resource named 'Domain Admins'"
2. Echo to screen: **Expected tools:** query_omada_resources
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 46: Show me all active resources with a risk score above 100

**Expected tools:** query_omada_resources
**MCP prompt:** resource_discovery_workflow

**Steps for this test:**
1. Echo to screen: **Question 46:** "Show me all active resources with a risk score above 100"
2. Echo to screen: **Expected tools:** query_omada_resources
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---
### Question 47: What resource types exist in the system?

**Expected tools:** query_omada_entity
**MCP prompt:** resource_discovery_workflow

**Steps for this test:**
1. Echo to screen: **Question 47:** "What resource types exist in the system?"
2. Echo to screen: **Expected tools:** query_omada_entity
3. Call the MCP tool(s) listed above to answer the question
4. Echo to screen the HTTP request(s) made, e.g.: **HTTP:** GET https://host/odata/... -> 200 OK
5. If multiple HTTP calls were made, list each request URL and response code
6. Record: **Result:** PASS / FAIL / SKIP

---

## Summary

After completing all questions above, fill in this summary:

| Category | Total | PASS | FAIL | SKIP |
|----------|-------|------|------|------|
| ACCESS REQUESTS | 6 | | | |
| ADMIN | 4 | | | |
| APPROVALS | 5 | | | |
| ASSIGNMENTS | 6 | | | |
| AUTHENTICATION | 2 | | | |
| COMPLIANCE | 3 | | | |
| IDENTITY | 9 | | | |
| ORGUNITS | 7 | | | |
| RESOURCES | 5 | | | |
| **TOTAL** | **47** | | | |

### Recurring Errors

_List any errors that appeared across multiple questions._

### Recommendations

_List any improvements or fixes suggested by the test results._

