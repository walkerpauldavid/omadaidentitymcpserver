import asyncio
import os
import sys
import argparse
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from server import query_omada_identity, query_omada_resources, _cached_token

# Import test functions from other test files
try:
    from test_operators import test_firstname_not_equals, test_other_operators
except ImportError:
    test_firstname_not_equals = test_other_operators = None
    
try:
    from test_resourceassignments import (test_resourceassignments_count, test_resourceassignments_sample, 
                                        test_resourceassignments_by_identity, test_resourceassignments_by_resource)
except ImportError:
    test_resourceassignments_count = test_resourceassignments_sample = None
    test_resourceassignments_by_identity = test_resourceassignments_by_resource = None
    
try:
    from test_system import test_system_count, test_system_sample, test_system_by_name
except ImportError:
    test_system_count = test_system_sample = test_system_by_name = None
    
try:
    from test_calculated_assignments import main as test_calculated_assignments_main
except ImportError:
    test_calculated_assignments_main = None
    
try:
    from test_errors import main as test_errors_main
except ImportError:
    test_errors_main = None

# Global variable to control output
show_output = True

def show_usage():
    """Display usage information and key features."""
    print("""
=== TEST OMADA - USAGE AND KEY FEATURES ===""")
    print("="*60)
    print("""
Key Features:

1. Import statements with error handling for:
   - test_operators.py
   - test_resourceassignments.py
   - test_system.py
   - test_calculated_assignments.py
   - test_errors.py

2. Individual test runner functions for each test suite:
   - run_operators_tests()
   - run_resourceassignments_tests()
   - run_system_tests()
   - run_calculated_assignments_tests()
   - run_errors_tests()

3. Count all functions available in relevant test files:
   - test_count_all_identities() in test_omada.py
   - test_count_application_roles() in test_omada.py
   - test_system_count() in test_system.py
   - test_count_all_calculated_assignments() in test_calculated_assignments.py
   - test_count_all_resources() in test_system_resources.py

4. New command line parameter --testsuite with options:
   - all (default) - runs all available tests
   - core - runs only the original omada tests
   - operators - runs operator tests only
   - resourceassignments - runs resource assignment tests only
   - system - runs system tests only
   - calculated - runs calculated assignments tests only
   - errors - runs error handling tests only

Usage examples:
- python test_omada.py                              # runs all tests
- python test_omada.py --testsuite all              # runs all tests (same as above)
- python test_omada.py --testsuite core             # runs only core tests
- python test_omada.py --testsuite operators        # runs operator tests only
- python test_omada.py --testsuite resourceassignments  # runs resource assignment tests only
- python test_omada.py --testsuite system           # runs system tests only
- python test_omada.py --testsuite calculated       # runs calculated assignments tests only
- python test_omada.py --testsuite errors           # runs error handling tests only
- python test_omada.py --showOutput                 # runs all tests with full JSON output
- python test_omada.py --testsuite core --showOutput    # runs core tests with full JSON output
- python test_omada.py --testsuite operators --showOutput  # runs operator tests with full output
- python test_omada.py usage                        # shows this usage information

The script gracefully handles missing test files and will skip test suites 
that aren't available, showing appropriate messages.
""")

def print_result(test_name: str, result: str):
    """Print test result based on showOutput setting."""
    if show_output:
        print(f"{test_name} Result:", result)
    else:
        try:
            # Parse the result to check if it's successful
            if isinstance(result, str):
                parsed = json.loads(result)
                if parsed.get("status") == "success":
                    print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
                else:
                    print(f"{test_name}: [FAILED] Failed")
            else:
                print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
        except (json.JSONDecodeError, AttributeError):
            # If we can't parse JSON, assume success if no error in result
            if "Error" not in str(result) and "[FAILED]" not in str(result):
                print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
            else:
                print(f"{test_name}: [FAILED] Failed")

def print_count_result(test_name: str, result: str, object_type: str):
    """Print count result with object count and type information."""
    try:
        if isinstance(result, str):
            parsed = json.loads(result)
            if parsed.get("status") == "success":
                count = parsed.get("count", 0)
                print(f"{test_name}: [SUCCESS] Success - Found {count} {object_type} objects")
                if show_output:
                    print(f"{test_name} Full Result:", result)
            else:
                print(f"{test_name}: [FAILED] Failed")
                if show_output:
                    print(f"{test_name} Error Result:", result)
        else:
            print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
    except (json.JSONDecodeError, AttributeError):
        # If we can't parse JSON, assume success if no error in result
        if "Error" not in str(result) and "[FAILED]" not in str(result):
            print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
        else:
            print(f"{test_name}: [FAILED] Failed")

def print_identity_result(test_name: str, result: str, show_fields=None):
    """Print identity result showing specified fields."""
    if show_fields is None:
        show_fields = ['Id', 'FIRSTNAME', 'LASTNAME']
        
    if show_output:
        print(f"{test_name} Result:", result)
    else:
        try:
            if isinstance(result, str):
                parsed = json.loads(result)
                if parsed.get("status") == "success":
                    print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
                    
                    # Show identity details if available
                    if 'data' in parsed and 'value' in parsed['data'] and parsed['data']['value']:
                        print(f"  Found {len(parsed['data']['value'])} identities:")
                        for i, item in enumerate(parsed['data']['value'][:3], 1):  # Show first 3
                            result_line = f"    {i}."
                            for field in show_fields:
                                value = item.get(field, 'N/A')
                                if field == 'Id':
                                    result_line += f" ID: {value}"
                                elif field == 'FIRSTNAME':
                                    result_line += f", FirstName: {value}"
                                elif field == 'LASTNAME':
                                    result_line += f", LastName: {value}"
                                elif field == 'DISPLAYNAME':
                                    result_line += f", DisplayName: {value}"
                            print(result_line)
                        if len(parsed['data']['value']) > 3:
                            print(f"    ... and {len(parsed['data']['value']) - 3} more")
                else:
                    print(f"{test_name}: [FAILED] Failed")
            else:
                print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
        except (json.JSONDecodeError, AttributeError):
            if "Error" not in str(result) and "[FAILED]" not in str(result):
                print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
            else:
                print(f"{test_name}: [FAILED] Failed")

async def test_identity_query():
    print("=== TESTING IDENTITY QUERIES ===""")
    global _cached_token
    # Clear cached token to ensure fresh request
    _cached_token = None
    
    try:
        result = await query_omada_identity(
            firstname="Emma", 
            lastname="Taylor", 
            omada_base_url=os.getenv("OMADA_BASE_URL"),
            select_fields="Id,FIRSTNAME,LASTNAME"
        )
        print_identity_result("Identity Query", result, ['Id', 'FIRSTNAME', 'LASTNAME'])
    except Exception as e:
        print(f"Identity Query Error: {str(e)}")
        print("Identity Query: [FAILED] Failed")

async def test_count_application_roles():
    print("\n=== TESTING APPLICATION ROLES COUNT ===""")
    try:
        result = await query_omada_resources(
            resource_type_name="APPLICATION_ROLES",
            count_only=True
        )
        print_count_result("Application Roles Count", result, "Application Role")
    except Exception as e:
        print(f"Application Roles Count Error: {str(e)}")
        print("Application Roles Count: [FAILED] Failed")

async def test_get_all_application_roles():
    print("\n=== TESTING GET ALL APPLICATION ROLES ===""")
    try:
        result = await query_omada_resources(
            resource_type_name="APPLICATION_ROLES",
            top=10,
            include_count=True,
            select_fields="Id,DISPLAYNAME"
        )
        print_result("Get All Application Roles", result)
    except Exception as e:
        print(f"Get All Application Roles Error: {str(e)}")
        print("Get All Application Roles: [FAILED] Failed")

async def test_get_application_roles_by_name():
    print("\n=== TESTING APPLICATION ROLES FILTERED BY NAME ===""")
    try:
        result = await query_omada_resources(
            resource_type_name="APPLICATION_ROLES",
            filter_condition="contains(DISPLAYNAME, 'Admin')",
            top=5,
            select_fields="Id,DISPLAYNAME"
        )
        print_result("Get Application Roles by Name", result)
    except Exception as e:
        print(f"Get Application Roles by Name Error: {str(e)}")
        print("Get Application Roles by Name: [FAILED] Failed")

async def test_application_roles_with_id():
    print("\n=== TESTING APPLICATION ROLES WITH NUMERIC ID ===""")
    try:
        result = await query_omada_resources(
            resource_type_id=1011066,
            top=5,
            select_fields="Id,DISPLAYNAME"
        )
        print_result("Get Application Roles with ID", result)
    except Exception as e:
        print(f"Get Application Roles with ID Error: {str(e)}")
        print("Get Application Roles with ID: [FAILED] Failed")

async def test_count_all_identities():
    """Count all identities in Omada system"""
    print("\n=== TESTING COUNT ALL IDENTITIES ===")
    try:
        result = await query_omada_identity(
            count_only=True,
            include_count=True
        )
        print_count_result("Count All Identities", result, "Identity")
    except Exception as e:
        print(f"Count All Identities Error: {str(e)}")
        print("Count All Identities: [FAILED] Failed")

async def run_operators_tests():
    """Run operator tests if available"""
    if test_firstname_not_equals and test_other_operators:
        print("\n" + "=" * 60)
        print("RUNNING OPERATOR TESTS")
        print("=" * 60)
        try:
            await test_firstname_not_equals()
            await test_other_operators()
        except Exception as e:
            print(f"Operator Tests Error: {str(e)}")
            print("Operator Tests: [FAILED] Failed")
    else:
        print("\nOperator tests not available (test_operators.py not found)")

async def run_resourceassignments_tests():
    """Run resource assignment tests if available"""
    if test_resourceassignments_count:
        print("\n" + "=" * 60)
        print("RUNNING RESOURCE ASSIGNMENT TESTS")
        print("=" * 60)
        try:
            await test_resourceassignments_count()
            if test_resourceassignments_sample:
                await test_resourceassignments_sample()
            if test_resourceassignments_by_identity:
                await test_resourceassignments_by_identity()
            if test_resourceassignments_by_resource:
                await test_resourceassignments_by_resource()
        except Exception as e:
            print(f"Resource Assignment Tests Error: {str(e)}")
            print("Resource Assignment Tests: [FAILED] Failed")
    else:
        print("\nResource assignment tests not available (test_resourceassignments.py not found)")

async def run_system_tests():
    """Run system tests if available"""
    if test_system_count:
        print("\n" + "=" * 60)
        print("RUNNING SYSTEM TESTS")
        print("=" * 60)
        try:
            await test_system_count()
            if test_system_sample:
                await test_system_sample()
            if test_system_by_name:
                await test_system_by_name()
        except Exception as e:
            print(f"System Tests Error: {str(e)}")
            print("System Tests: [FAILED] Failed")
    else:
        print("\nSystem tests not available (test_system.py not found)")

async def run_calculated_assignments_tests():
    """Run calculated assignments tests if available"""
    if test_calculated_assignments_main:
        print("\n" + "=" * 60)
        print("RUNNING CALCULATED ASSIGNMENTS TESTS")
        print("=" * 60)
        try:
            await test_calculated_assignments_main()
        except Exception as e:
            print(f"Calculated Assignments Tests Error: {str(e)}")
            print("Calculated Assignments Tests: [FAILED] Failed")
    else:
        print("\nCalculated assignments tests not available (test_calculated_assignments.py not found)")

async def run_errors_tests():
    """Run error handling tests if available"""
    if test_errors_main:
        print("\n" + "=" * 60)
        print("RUNNING ERROR HANDLING TESTS")
        print("=" * 60)
        try:
            await test_errors_main()
        except Exception as e:
            print(f"Error Handling Tests Error: {str(e)}")
            print("Error Handling Tests: [FAILED] Failed")
    else:
        print("\nError handling tests not available (test_errors.py not found)")

async def main():
    print("=" * 60)
    print("RUNNING CORE OMADA TESTS")
    print("=" * 60)
    await test_identity_query()
    await test_count_all_identities()
    await test_count_application_roles()
    await test_get_all_application_roles()
    await test_get_application_roles_by_name()
    await test_application_roles_with_id()
    
    # Run additional test suites
    await run_operators_tests()
    await run_resourceassignments_tests()
    await run_system_tests()
    await run_calculated_assignments_tests()
    await run_errors_tests()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    # Check for usage parameter first
    if len(sys.argv) > 1 and sys.argv[1] == 'usage':
        show_usage()
        sys.exit(0)
    
    parser = argparse.ArgumentParser(description='Test Omada API endpoints')
    parser.add_argument('--showOutput', action='store_true', default=False,
                       help='Show full JSON output (default: False, shows only status)')
    parser.add_argument('--testsuite', choices=['all', 'core', 'operators', 'resourceassignments', 'system', 'calculated', 'errors'],
                       default='all', help='Select which test suite to run (default: all)')
    
    args = parser.parse_args()
    show_output = args.showOutput
    
    # Run specific test suite based on argument
    if args.testsuite == 'core':
        async def run_core_only():
            print("=" * 60)
            print("RUNNING CORE OMADA TESTS ONLY")
            print("=" * 60)
            await test_identity_query()
            await test_count_all_identities()
            await test_count_application_roles()
            await test_get_all_application_roles()
            await test_get_application_roles_by_name()
            await test_application_roles_with_id()
        asyncio.run(run_core_only())
    elif args.testsuite == 'operators':
        asyncio.run(run_operators_tests())
    elif args.testsuite == 'resourceassignments':
        asyncio.run(run_resourceassignments_tests())
    elif args.testsuite == 'system':
        asyncio.run(run_system_tests())
    elif args.testsuite == 'calculated':
        asyncio.run(run_calculated_assignments_tests())
    elif args.testsuite == 'errors':
        asyncio.run(run_errors_tests())
    else:  # 'all' or default
        asyncio.run(main())