"""
MCP Test Harness - Tests prompts, resources, and tools via the MCP protocol.

Connects to the Omada MCP server the same way Claude Desktop does (stdio transport)
and exercises the ListPrompts, GetPrompt, ListResources, ReadResource, and ListTools endpoints.

Usage:
    python tests/test_mcp_harness.py
    python tests/test_mcp_harness.py --prompts-only
    python tests/test_mcp_harness.py --resources-only
    python tests/test_mcp_harness.py --tools-only
    python tests/test_mcp_harness.py --verbose
"""

import argparse
import asyncio
import json
import os
import sys
import textwrap
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Path to the MCP server
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
PYTHON_EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "Scripts", "python.exe")

# Fall back to system python if venv not found
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable


def separator(title: str, char: str = "=", width: int = 80):
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")


def print_pass(msg: str):
    print(f"  PASS  {msg}")


def print_fail(msg: str):
    print(f"  FAIL  {msg}")


def print_info(msg: str):
    print(f"  INFO  {msg}")


def truncate(text: str, max_len: int = 200) -> str:
    if not text:
        return "(empty)"
    text = text.replace("\n", " ").strip()
    # Strip non-ASCII characters (emojis, etc.) to avoid encoding errors on Windows console
    text = text.encode("ascii", errors="replace").decode("ascii")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


async def test_list_prompts(session: ClientSession, verbose: bool = False) -> dict:
    """Test listing all available prompts."""
    separator("TEST: List Prompts")
    results = {"passed": 0, "failed": 0, "prompts": []}

    try:
        response = await session.list_prompts()
        prompts = response.prompts
        print_pass(f"list_prompts returned {len(prompts)} prompts")
        results["passed"] += 1

        if len(prompts) == 0:
            print_fail("No prompts registered — expected at least 1")
            results["failed"] += 1
            return results

        for prompt in prompts:
            results["prompts"].append(prompt.name)
            if verbose:
                desc = truncate(prompt.description or "(no description)")
                print_info(f"  {prompt.name}: {desc}")

    except Exception as e:
        print_fail(f"list_prompts raised: {e}")
        results["failed"] += 1

    return results


async def test_get_each_prompt(session: ClientSession, prompt_names: list, verbose: bool = False) -> dict:
    """Test getting each prompt by name."""
    separator("TEST: Get Each Prompt")
    results = {"passed": 0, "failed": 0, "details": []}

    for name in prompt_names:
        try:
            response = await session.get_prompt(name)
            messages = response.messages

            if messages and len(messages) > 0:
                content = messages[0].content
                # content can be TextContent or other types
                if hasattr(content, "text"):
                    text = content.text
                elif isinstance(content, str):
                    text = content
                else:
                    text = str(content)

                text_len = len(text)
                print_pass(f"{name} -> {len(messages)} message(s), {text_len} chars")
                results["passed"] += 1

                if verbose:
                    # Show first few lines
                    preview = truncate(text, 300)
                    print_info(f"    Preview: {preview}")

                results["details"].append({
                    "name": name,
                    "status": "pass",
                    "messages": len(messages),
                    "chars": text_len,
                })
            else:
                print_fail(f"{name} -> returned empty/no messages")
                results["failed"] += 1
                results["details"].append({"name": name, "status": "fail", "reason": "empty"})

        except Exception as e:
            print_fail(f"{name} -> error: {e}")
            results["failed"] += 1
            results["details"].append({"name": name, "status": "fail", "reason": str(e)})

    return results


async def test_list_resources(session: ClientSession, verbose: bool = False) -> dict:
    """Test listing all available resources (schemas)."""
    separator("TEST: List Resources")
    results = {"passed": 0, "failed": 0, "resources": []}

    try:
        response = await session.list_resources()
        resources = response.resources
        print_pass(f"list_resources returned {len(resources)} resources")
        results["passed"] += 1

        for resource in resources:
            results["resources"].append(str(resource.uri))
            if verbose:
                desc = truncate(resource.description or "(no description)")
                print_info(f"  {resource.uri}: {desc}")

    except Exception as e:
        print_fail(f"list_resources raised: {e}")
        results["failed"] += 1

    return results


async def test_read_each_resource(session: ClientSession, resource_uris: list, verbose: bool = False) -> dict:
    """Test reading each resource by URI."""
    separator("TEST: Read Each Resource")
    results = {"passed": 0, "failed": 0, "details": []}

    for uri in resource_uris:
        try:
            response = await session.read_resource(uri)
            contents = response.contents

            if contents and len(contents) > 0:
                content = contents[0]
                if hasattr(content, "text"):
                    text = content.text
                elif isinstance(content, str):
                    text = content
                else:
                    text = str(content)

                # Try to parse as JSON to validate schema structure
                try:
                    parsed = json.loads(text)
                    is_valid_json = True
                    if isinstance(parsed, dict):
                        keys = list(parsed.keys())[:5]
                        key_info = f"keys: {keys}"
                    else:
                        key_info = f"type: {type(parsed).__name__}"
                except json.JSONDecodeError:
                    is_valid_json = False
                    key_info = "not JSON"

                print_pass(f"{uri} -> {len(text)} chars, valid_json={is_valid_json}, {key_info}")
                results["passed"] += 1

                if verbose and is_valid_json:
                    # For schema resources, show field count
                    if isinstance(parsed, dict) and "fields" in parsed:
                        print_info(f"    Entity: {parsed.get('entity', '?')}, Fields: {len(parsed['fields'])}")
                        if "important_notes" in parsed:
                            for note_key in parsed["important_notes"]:
                                print_info(f"    Note [{note_key}]: {truncate(parsed['important_notes'][note_key], 120)}")
                    elif isinstance(parsed, dict) and "available_schemas" in parsed:
                        for schema in parsed["available_schemas"]:
                            print_info(f"    Schema: {schema.get('uri')} -> {schema.get('entity')}")

                results["details"].append({
                    "uri": uri,
                    "status": "pass",
                    "chars": len(text),
                    "valid_json": is_valid_json,
                })
            else:
                print_fail(f"{uri} -> returned empty content")
                results["failed"] += 1
                results["details"].append({"uri": uri, "status": "fail", "reason": "empty"})

        except Exception as e:
            print_fail(f"{uri} -> error: {e}")
            results["failed"] += 1
            results["details"].append({"uri": uri, "status": "fail", "reason": str(e)})

    return results


async def test_list_tools(session: ClientSession, verbose: bool = False) -> dict:
    """Test listing all available tools."""
    separator("TEST: List Tools")
    results = {"passed": 0, "failed": 0, "tools": []}

    try:
        response = await session.list_tools()
        tools = response.tools
        print_pass(f"list_tools returned {len(tools)} tools")
        results["passed"] += 1

        if len(tools) == 0:
            print_fail("No tools registered — expected at least 1")
            results["failed"] += 1
            return results

        for tool in tools:
            results["tools"].append(tool.name)
            if verbose:
                desc = truncate(tool.description or "(no description)")
                params = tool.inputSchema.get("properties", {}).keys() if tool.inputSchema else []
                param_list = ", ".join(params) if params else "(none)"
                print_info(f"  {tool.name}({param_list})")
                print_info(f"    {desc}")

    except Exception as e:
        print_fail(f"list_tools raised: {e}")
        results["failed"] += 1

    return results


async def test_tool_hints(session: ClientSession, verbose: bool = False) -> dict:
    """Verify key OData limitation hints are present in tool descriptions."""
    separator("TEST: Verify OData Limitation Hints in Tools")
    results = {"passed": 0, "failed": 0}

    try:
        response = await session.list_tools()
        tools = {t.name: t for t in response.tools}

        # Tools that should mention $expand limitation
        expand_tools = [
            "query_omada_entity",
            "query_omada_orgunits",
            "query_omada_identity",
            "query_omada_resources",
            "query_omada_entities",
        ]

        for tool_name in expand_tools:
            if tool_name not in tools:
                print_fail(f"{tool_name} not found in tools list")
                results["failed"] += 1
                continue

            desc = tools[tool_name].description or ""

            # Check $expand hint
            if "expand" in desc.lower() and "not supported" in desc.lower():
                print_pass(f"{tool_name} -> has $expand limitation hint")
                results["passed"] += 1
            else:
                print_fail(f"{tool_name} -> MISSING $expand limitation hint")
                results["failed"] += 1

            # Check $select with reference fields hint
            if "select" in desc.lower() and ("empty" in desc.lower() or "reference" in desc.lower()):
                print_pass(f"{tool_name} -> has $select reference fields hint")
                results["passed"] += 1
            else:
                print_fail(f"{tool_name} -> MISSING $select reference fields hint")
                results["failed"] += 1

            # Check any()/all() lambda hint
            if "any()" in desc.lower() or "lambda" in desc.lower():
                print_pass(f"{tool_name} -> has any()/all() lambda hint")
                results["passed"] += 1
            else:
                print_fail(f"{tool_name} -> MISSING any()/all() lambda hint")
                results["failed"] += 1

        # CalculatedAssignments should have expand as SUPPORTED
        if "query_calculated_assignments" in tools:
            desc = tools["query_calculated_assignments"].description or ""
            if "only" in desc.lower() and "expand" in desc.lower():
                print_pass("query_calculated_assignments -> correctly documents $expand support")
                results["passed"] += 1
            else:
                print_fail("query_calculated_assignments -> MISSING $expand support documentation")
                results["failed"] += 1

        # Check query_omada_orgunits has summary_mode parameter
        if "query_omada_orgunits" in tools:
            schema = tools["query_omada_orgunits"].inputSchema or {}
            props = schema.get("properties", {})
            if "summary_mode" in props:
                print_pass("query_omada_orgunits -> has summary_mode parameter")
                results["passed"] += 1
            else:
                print_fail("query_omada_orgunits -> MISSING summary_mode parameter")
                results["failed"] += 1

            # Should NOT have expand parameter
            if "expand" not in props:
                print_pass("query_omada_orgunits -> correctly excludes expand parameter")
                results["passed"] += 1
            else:
                print_fail("query_omada_orgunits -> should NOT have expand parameter")
                results["failed"] += 1

    except Exception as e:
        print_fail(f"Tool hints verification raised: {e}")
        results["failed"] += 1

    return results


async def test_schema_hints(session: ClientSession, verbose: bool = False) -> dict:
    """Verify OData limitation notes are present in schema resources."""
    separator("TEST: Verify OData Limitation Hints in Schemas")
    results = {"passed": 0, "failed": 0}

    schema_uris = [
        "schema://omada/identity",
        "schema://omada/resource",
        "schema://omada/orgunit",
    ]

    for uri in schema_uris:
        try:
            response = await session.read_resource(uri)
            text = response.contents[0].text if response.contents else ""
            parsed = json.loads(text)
            notes = parsed.get("important_notes", {})

            entity = parsed.get("entity", uri)

            # Check no_expand
            if "no_expand" in notes:
                print_pass(f"{entity} schema -> has no_expand note")
                results["passed"] += 1
            else:
                print_fail(f"{entity} schema -> MISSING no_expand note")
                results["failed"] += 1

            # Check no_select_with_references
            if "no_select_with_references" in notes:
                print_pass(f"{entity} schema -> has no_select_with_references note")
                results["passed"] += 1
            else:
                print_fail(f"{entity} schema -> MISSING no_select_with_references note")
                results["failed"] += 1

            # Check no_any_lambda
            if "no_any_lambda" in notes:
                print_pass(f"{entity} schema -> has no_any_lambda note")
                results["passed"] += 1
            else:
                print_fail(f"{entity} schema -> MISSING no_any_lambda note")
                results["failed"] += 1

        except Exception as e:
            print_fail(f"{uri} -> error reading schema: {e}")
            results["failed"] += 1

    # Check entities index includes orgunit
    try:
        response = await session.read_resource("schema://omada/entities")
        text = response.contents[0].text if response.contents else ""
        parsed = json.loads(text)
        schemas = parsed.get("available_schemas", [])
        entity_names = [s.get("entity") for s in schemas]

        if "Orgunit" in entity_names:
            print_pass("schema://omada/entities -> includes Orgunit")
            results["passed"] += 1
        else:
            print_fail(f"schema://omada/entities -> MISSING Orgunit (found: {entity_names})")
            results["failed"] += 1

    except Exception as e:
        print_fail(f"schema://omada/entities -> error: {e}")
        results["failed"] += 1

    return results


async def run_all_tests(args):
    """Connect to the MCP server and run all test suites."""
    separator("MCP Test Harness - Omada MCP Server", "=", 80)
    print_info(f"Server: {SERVER_SCRIPT}")
    print_info(f"Python: {PYTHON_EXE}")
    print_info(f"Verbose: {args.verbose}")

    server_params = StdioServerParameters(
        command=PYTHON_EXE,
        args=[SERVER_SCRIPT],
        env={
            **os.environ,
            "PYTHONPATH": os.path.dirname(SERVER_SCRIPT),
        },
    )

    total_passed = 0
    total_failed = 0
    start_time = time.time()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the MCP session
            await session.initialize()
            print_pass("MCP session initialized successfully")
            total_passed += 1

            # --- Prompts ---
            if not args.resources_only and not args.tools_only:
                list_result = await test_list_prompts(session, args.verbose)
                total_passed += list_result["passed"]
                total_failed += list_result["failed"]

                if list_result["prompts"]:
                    get_result = await test_get_each_prompt(session, list_result["prompts"], args.verbose)
                    total_passed += get_result["passed"]
                    total_failed += get_result["failed"]

            # --- Resources ---
            if not args.prompts_only and not args.tools_only:
                res_result = await test_list_resources(session, args.verbose)
                total_passed += res_result["passed"]
                total_failed += res_result["failed"]

                if res_result["resources"]:
                    read_result = await test_read_each_resource(session, res_result["resources"], args.verbose)
                    total_passed += read_result["passed"]
                    total_failed += read_result["failed"]

                # Schema hint verification
                schema_result = await test_schema_hints(session, args.verbose)
                total_passed += schema_result["passed"]
                total_failed += schema_result["failed"]

            # --- Tools ---
            if not args.prompts_only and not args.resources_only:
                tools_result = await test_list_tools(session, args.verbose)
                total_passed += tools_result["passed"]
                total_failed += tools_result["failed"]

                # Tool hints verification
                hints_result = await test_tool_hints(session, args.verbose)
                total_passed += hints_result["passed"]
                total_failed += hints_result["failed"]

    elapsed = time.time() - start_time

    # --- Summary ---
    separator("TEST SUMMARY", "=", 80)
    total = total_passed + total_failed
    print(f"  Total:  {total} tests")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Time:   {elapsed:.1f}s")

    if total_failed == 0:
        print(f"\n  ALL TESTS PASSED")
    else:
        print(f"\n  {total_failed} TEST(S) FAILED")

    print("=" * 80)
    return total_failed


def main():
    parser = argparse.ArgumentParser(description="MCP Test Harness for Omada MCP Server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output for each test")
    parser.add_argument("--prompts-only", action="store_true", help="Only test prompts")
    parser.add_argument("--resources-only", action="store_true", help="Only test resources/schemas")
    parser.add_argument("--tools-only", action="store_true", help="Only test tools listing")
    args = parser.parse_args()

    failures = asyncio.run(run_all_tests(args))
    sys.exit(1 if failures > 0 else 0)


if __name__ == "__main__":
    main()
