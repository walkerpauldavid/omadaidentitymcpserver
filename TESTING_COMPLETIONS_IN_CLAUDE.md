# Testing Completions in Claude Desktop

## Quick Test Guide

Here's how to test the autocompletion feature for systems and other parameters in Claude Desktop.

---

## Prerequisites

1. ✅ omada_mcp_server is running
2. ✅ Server is registered in Claude Desktop's MCP settings
3. ✅ Completions are registered (check logs for "Registered MCP completions...")

---

## Test 1: System ID Completion

### Step 1: Start a conversation
Open Claude Desktop and start typing:

```
"Query resources from system"
```

### Step 2: Watch for parameter prompts
Claude will ask you for parameters. When it asks for `system_id`, you should see autocomplete suggestions:

**Expected behavior:**
```
Claude: Which system would you like to query?
[Autocomplete suggestions appear:]
  • active-directory-system
  • azure-ad-system
  • salesforce-system
  • sap-system
  • workday-system
  • servicenow-system
  • google-workspace-system
  • okta-system
```

### Step 3: Select or type
- **Option A:** Click on one of the suggestions
- **Option B:** Start typing and the list filters (e.g., type "azure" to see "azure-ad-system")

---

## Test 2: Resource Type Name Completion

### Trigger the completion
```
"Show me assignments filtered by resource type"
```

**Expected behavior:**
```
Claude: Which resource type?
[Autocomplete suggestions appear:]
  • Active Directory - Security Group
  • Active Directory - Distribution List
  • Azure AD - Security Group
  • SAP - Role
  • Salesforce - Permission Set
  [... and 15 more]
```

---

## Test 3: Identity Field Name Completion

### Trigger the completion
```
"Search for an identity by field"
```

**Expected behavior:**
```
Claude: Which field would you like to search by?
[Autocomplete suggestions appear:]
  • EMAIL
  • FIRSTNAME
  • LASTNAME
  • DISPLAYNAME
  • EMPLOYEEID
  • DEPARTMENT
  [... and 16 more]
```

---

## Test 4: OData Operator Completion

### Trigger the completion
```
"Find users where LASTNAME [operator] Smith"
```

**Expected behavior:**
```
Claude: Which operator?
[Autocomplete suggestions appear:]
  • eq (equals)
  • ne (not equals)
  • contains
  • startswith
  • endswith
  [... and 4 more]
```

---

## Test 5: Full Workflow Test

### Complete scenario
Try this complete conversation to test multiple completions:

```
User: I need to search for identities

Claude: I can help with that. What field would you like to search by?
[Autocomplete shows: EMAIL, FIRSTNAME, LASTNAME, etc.]

User: EMAIL

Claude: What operator would you like to use?
[Autocomplete shows: eq, contains, startswith, etc.]

User: eq

Claude: What value should I search for?

User: hanulr@54mv4c.onmicrosoft.com

Claude: [Executes query and shows results]
```

---

## Troubleshooting

### Completions Not Appearing

#### Check 1: Server is Running
```bash
# Check if server is running
ps aux | grep server.py

# Or check logs
tail -f /path/to/omada_mcp_server.log
```

#### Check 2: Completions are Registered
Look for this in the log file:
```
Registered MCP completions for: system_id, resource_type_name, field names, operators, compliance_status, workflow_step, status
```

#### Check 3: Restart Claude Desktop
1. Quit Claude Desktop completely
2. Restart it
3. Try again

#### Check 4: Claude Desktop Version
Completions require Claude Desktop version with MCP completion support. Update if necessary.

---

## Alternative Testing Methods

### Method A: Direct Python Test (Always Works)

```bash
cd /c/Users/demoadm/Documents/Code/omada_mcp_server
python test_completions_direct.py
```

This will show all completions without needing Claude Desktop.

**Output:**
```
================================================================================
Testing MCP Completions
================================================================================

System IDs (argument: 'system_id')
--------------------------------------------------------------------------------
   1. active-directory-system
   2. azure-ad-system
   3. salesforce-system
   [...]
```

### Method B: Test Specific Parameter

```bash
python test_completions_direct.py
# Then when prompted, enter the argument name you want to test
```

Or modify the script to test specific completion:

```python
import asyncio
from completions import register_completions
from mcp.server.fastmcp.server import FastMCP

async def test():
    mcp = FastMCP("Test")
    register_completions(mcp)

    # Get the completion function
    from completions import complete_arguments

    # Test system_id
    results = await complete_arguments("system_id", "")
    print("System ID completions:")
    for r in results:
        print(f"  - {r}")

asyncio.run(test())
```

### Method C: Interactive Test

```bash
python -i test_completions_direct.py

# In the Python shell:
>>> import asyncio
>>> asyncio.run(complete_arguments("resource_type_name", ""))
['Active Directory - Security Group', 'Azure AD - Security Group', ...]
```

---

## Expected Completion Counts

| Parameter | Count | Category |
|-----------|-------|----------|
| system_id | 8 | Systems |
| resource_type_name | 20 | Resource Types |
| field | 22 | Identity Fields |
| operator | 9 | OData Operators |
| compliance_status | 5 | Compliance |
| workflow_step | 5 | Workflows |
| status | 6 | Status Values |

---

## What Success Looks Like

### ✅ Working Completions
- Suggestions appear as you type
- List filters based on partial input
- Clicking a suggestion inserts the value
- Reduces typing and prevents errors

### ❌ Not Working
- No suggestions appear
- You must type everything manually
- No filtering of options
- No visual autocomplete popup

---

## Debug Mode

To see detailed logging of completion requests:

1. Add to `.env`:
```bash
LOG_LEVEL_complete_arguments=DEBUG
```

2. Restart server

3. Check logs for completion requests:
```bash
grep "completion" /path/to/omada_mcp_server.log
```

---

## Real-World Usage Example

### Scenario: Find users in a specific department

**Without completions:**
```
User: Search for users in Engineering department

Claude: I'll search. What field name?
User: [types] DEPAR... wait is it DEPARTMENT or DEPT?
[Has to guess or look up documentation]
```

**With completions:**
```
User: Search for users in Engineering department

Claude: What field name?
[Autocomplete shows: EMAIL, FIRSTNAME, LASTNAME, DEPARTMENT, ...]
User: [sees DEPARTMENT in list, clicks it]

Claude: What operator?
[Autocomplete shows: eq, contains, startswith, ...]
User: [clicks "contains"]

Claude: What value?
User: Engineering
[Executes: field=DEPARTMENT, operator=contains, value=Engineering]
```

### Benefits Demonstrated
- ✅ No need to memorize field names
- ✅ No typos (DEPARTEMENT vs DEPARTMENT)
- ✅ Faster input (click instead of type)
- ✅ Discover available operators
- ✅ Consistent field name usage

---

## Summary

**To test completions:**
1. **Easiest:** Use Claude Desktop and watch for autocomplete popups
2. **Reliable:** Run `python test_completions_direct.py`
3. **Advanced:** Use MCP protocol testing (if SDK supports it)

**Completion triggers:**
- Typing function parameters
- Field selection prompts
- Operator selection
- System/resource type selection

**Success indicators:**
- Autocomplete popup appears
- List of suggestions shown
- Filtering works as you type
- Selection inserts correct value

Happy testing! 🚀
