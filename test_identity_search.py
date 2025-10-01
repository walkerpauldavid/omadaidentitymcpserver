#!/usr/bin/env python3
"""
Test script for query_omada_identity function examples.
Comprehensive tests for various operators and field combinations.
"""

import asyncio
import sys
import os
import json

# Add the current directory to Python path so we can import from server.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import query_omada_identity


def display_filtered_result(result_json, test_name, show_fields=None):
    """Extract and display specific fields from the JSON result"""
    if show_fields is None:
        show_fields = ['Id', 'DISPLAYNAME']
        
    try:
        # Parse the JSON string
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        
        # Extract specified fields from data.value array
        if 'data' in data and 'value' in data['data']:
            print("\nIdentities:")
            print("-" * 40)
            for i, item in enumerate(data['data']['value'], 1):
                result_line = f"{i}."
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
        else:
            print("\nNo identity data found")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 60)
        print("Error parsing JSON result:")
        # Handle Unicode encoding issues by removing non-ASCII characters
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:200] + "..." if len(clean_result) > 200 else clean_result)
        except:
            print("Unable to display error response due to encoding issues")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Error processing result: {repr(e)}")


async def test_basic_examples():
    """Test basic examples of identity searches."""
    
    print("🔍 BASIC IDENTITY SEARCH EXAMPLES")
    print("=" * 60)
    
    # Example 1: Search for exact matches
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "John", "operator": "eq"},
        {"field": "LASTNAME", "value": "Doe", "operator": "eq"}
    ])
    display_filtered_result(result, "Basic Example 1: Exact firstname and lastname match", ['Id', 'FIRSTNAME', 'LASTNAME'])
    
    # Example 2: Search with partial matches
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "John", "operator": "startswith"},
        {"field": "LASTNAME", "value": "Smith", "operator": "contains"}
    ])
    display_filtered_result(result, "Basic Example 2: Partial matches (startswith + contains)", ['Id', 'FIRSTNAME', 'LASTNAME'])
    
    # Example 3: Search with just firstname
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Basic Example 3: Search by firstname only", ['Id', 'FIRSTNAME'])
    
    # Example 4: Count-only search
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "A", "operator": "startswith"}
    ], count_only=True)
    display_filtered_result(result, "Basic Example 4: Count-only search (firstname starts with 'A')", ['Id', 'FIRSTNAME'])

    # Example 5: Search by exact email address
    result = await query_omada_identity([
        {"field": "EMAIL", "value": "berbla@54MV4C.ONMICROSOFT.COM", "operator": "eq"}
    ], select_fields="Id,EMAIL,DISPLAYNAME,FIRSTNAME,LASTNAME")
    display_filtered_result(result, "Basic Example 5: Search by exact email address", ['Id', 'EMAIL', 'DISPLAYNAME'])

    # Example 6: Search by email domain
    result = await query_omada_identity([
        {"field": "EMAIL", "value": "@54MV4C.ONMICROSOFT.COM", "operator": "endswith"}
    ], top=5, select_fields="Id,EMAIL,DISPLAYNAME")
    display_filtered_result(result, "Basic Example 6: Search by email domain", ['Id', 'EMAIL', 'DISPLAYNAME'])

    # Example 7: Search by email contains pattern
    result = await query_omada_identity([
        {"field": "EMAIL", "value": "robwol", "operator": "contains"}
    ], top=3, select_fields="Id,EMAIL,DISPLAYNAME")
    display_filtered_result(result, "Basic Example 7: Search by email contains pattern", ['Id', 'EMAIL', 'DISPLAYNAME'])

    # Example 8: Combined email and name search
    result = await query_omada_identity([
        {"field": "EMAIL", "value": "@54MV4C.ONMICROSOFT.COM", "operator": "endswith"},
        {"field": "FIRSTNAME", "value": "Rob", "operator": "startswith"}
    ], top=3, select_fields="Id,EMAIL,FIRSTNAME,LASTNAME,DISPLAYNAME")
    display_filtered_result(result, "Basic Example 8: Combined email domain and firstname search", ['Id', 'EMAIL', 'FIRSTNAME', 'DISPLAYNAME'])


async def test_operator_variations():
    """Test various operators from the original test_operators.py."""
    
    print("\n🧪 OPERATOR VARIATION TESTS (from test_operators.py)")
    print("=" * 60)
    
    # Test 1: NOT EQUALS operator
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"}
    ], top=5, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Operator Test 1: Firstname NOT EQUALS 'Emma'", ['Id', 'FIRSTNAME'])
    
    # Test 2: Combined operators - firstname ne and lastname startswith
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"},
        {"field": "LASTNAME", "value": "T", "operator": "startswith"}
    ], top=3, select_fields="Id,FIRSTNAME,LASTNAME")
    display_filtered_result(result, "Operator Test 2: Combined (firstname ne 'Emma' AND lastname startswith 'T')", ['Id', 'FIRSTNAME', 'LASTNAME'])

    # Test 3: Contains operator
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "mm", "operator": "contains"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Operator Test 3: Contains operator (firstname contains 'mm')", ['Id', 'FIRSTNAME'])
    
    # Test 4: Startswith operator
    result = await query_omada_identity([
        {"field": "LASTNAME", "value": "Tay", "operator": "startswith"}
    ], top=3, select_fields="Id,LASTNAME")
    display_filtered_result(result, "Operator Test 4: Startswith operator (lastname startswith 'Tay')", ['Id', 'LASTNAME'])
    
    # Test 5: Like operator (may have syntax issues in OData)
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Em%", "operator": "like"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Operator Test 5: Like operator (firstname like 'Em%') - May not be supported", ['Id', 'FIRSTNAME'])
    
    # Test 6: Reference equals test
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Operator Test 6: Equals operator (firstname eq 'Emma') - Reference working test", ['Id', 'FIRSTNAME'])


async def run_individual_basic_test(test_number):
    """Run a specific basic test example by number."""
    if test_number == 1:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "John", "operator": "eq"},
            {"field": "LASTNAME", "value": "Doe", "operator": "eq"}
        ])
        display_filtered_result(result, "Basic Example 1: Exact firstname and lastname match", ['Id', 'FIRSTNAME', 'LASTNAME'])

    elif test_number == 2:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "John", "operator": "startswith"},
            {"field": "LASTNAME", "value": "Smith", "operator": "contains"}
        ])
        display_filtered_result(result, "Basic Example 2: Partial matches (startswith + contains)", ['Id', 'FIRSTNAME', 'LASTNAME'])

    elif test_number == 3:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
        ], top=3, select_fields="Id,FIRSTNAME")
        display_filtered_result(result, "Basic Example 3: Search by firstname only", ['Id', 'FIRSTNAME'])

    elif test_number == 4:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "A", "operator": "startswith"}
        ], count_only=True)
        display_filtered_result(result, "Basic Example 4: Count-only search (firstname starts with 'A')", ['Id', 'FIRSTNAME'])

    elif test_number == 5:
        result = await query_omada_identity([
            {"field": "EMAIL", "value": "berbla@54MV4C.ONMICROSOFT.COM", "operator": "eq"}
        ], select_fields="Id,EMAIL,DISPLAYNAME,FIRSTNAME,LASTNAME")
        display_filtered_result(result, "Basic Example 5: Search by exact email address", ['Id', 'EMAIL', 'DISPLAYNAME'])

    elif test_number == 6:
        result = await query_omada_identity([
            {"field": "EMAIL", "value": "@54MV4C.ONMICROSOFT.COM", "operator": "endswith"}
        ], top=5, select_fields="Id,EMAIL,DISPLAYNAME")
        display_filtered_result(result, "Basic Example 6: Search by email domain", ['Id', 'EMAIL', 'DISPLAYNAME'])

    elif test_number == 7:
        result = await query_omada_identity([
            {"field": "EMAIL", "value": "robwol", "operator": "contains"}
        ], top=3, select_fields="Id,EMAIL,DISPLAYNAME")
        display_filtered_result(result, "Basic Example 7: Search by email contains pattern", ['Id', 'EMAIL', 'DISPLAYNAME'])

    elif test_number == 8:
        result = await query_omada_identity([
            {"field": "EMAIL", "value": "@54MV4C.ONMICROSOFT.COM", "operator": "endswith"},
            {"field": "FIRSTNAME", "value": "Rob", "operator": "startswith"}
        ], top=3, select_fields="Id,EMAIL,FIRSTNAME,LASTNAME,DISPLAYNAME")
        display_filtered_result(result, "Basic Example 8: Combined email domain and firstname search", ['Id', 'EMAIL', 'FIRSTNAME', 'DISPLAYNAME'])


async def run_individual_operator_test(test_number):
    """Run a specific operator test by number."""
    if test_number == 9:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"}
        ], top=5, select_fields="Id,FIRSTNAME")
        display_filtered_result(result, "Operator Test 1: Firstname NOT EQUALS 'Emma'", ['Id', 'FIRSTNAME'])

    elif test_number == 10:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"},
            {"field": "LASTNAME", "value": "T", "operator": "startswith"}
        ], top=3, select_fields="Id,FIRSTNAME,LASTNAME")
        display_filtered_result(result, "Operator Test 2: Combined (firstname ne 'Emma' AND lastname startswith 'T')", ['Id', 'FIRSTNAME', 'LASTNAME'])

    elif test_number == 11:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "mm", "operator": "contains"}
        ], top=3, select_fields="Id,FIRSTNAME")
        display_filtered_result(result, "Operator Test 3: Contains operator (firstname contains 'mm')", ['Id', 'FIRSTNAME'])

    elif test_number == 12:
        result = await query_omada_identity([
            {"field": "LASTNAME", "value": "Tay", "operator": "startswith"}
        ], top=3, select_fields="Id,LASTNAME")
        display_filtered_result(result, "Operator Test 4: Startswith operator (lastname startswith 'Tay')", ['Id', 'LASTNAME'])

    elif test_number == 13:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Em%", "operator": "like"}
        ], top=3, select_fields="Id,FIRSTNAME")
        display_filtered_result(result, "Operator Test 5: Like operator (firstname like 'Em%') - May not be supported", ['Id', 'FIRSTNAME'])

    elif test_number == 14:
        result = await query_omada_identity([
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
        ], top=3, select_fields="Id,FIRSTNAME")
        display_filtered_result(result, "Operator Test 6: Equals operator (firstname eq 'Emma') - Reference working test", ['Id', 'FIRSTNAME'])


def display_test_menu():
    """Display the test selection menu."""
    print("🔍 OMADA IDENTITY SEARCH TEST SUITE")
    print("=" * 60)
    print("Select which tests to run (enter numbers separated by commas):")
    print("\nBASIC EXAMPLES:")
    print("  1. Exact firstname and lastname match")
    print("  2. Partial matches (startswith + contains)")
    print("  3. Search by firstname only")
    print("  4. Count-only search (firstname starts with 'A')")
    print("  5. Search by exact email address")
    print("  6. Search by email domain")
    print("  7. Search by email contains pattern")
    print("  8. Combined email domain and firstname search")
    print("\nOPERATOR VARIATIONS:")
    print("  9. Firstname NOT EQUALS 'Emma'")
    print(" 10. Combined ne and startswith operators")
    print(" 11. Contains operator")
    print(" 12. Startswith operator")
    print(" 13. Like operator (may not be supported)")
    print(" 14. Equals operator (reference test)")
    print("\nSPECIAL OPTIONS:")
    print(" 15. Run all basic examples (1-8)")
    print(" 16. Run all operator variations (9-14)")
    print(" 17. Run ALL tests (1-14)")
    print("=" * 60)


async def run_selected_tests():
    """Interactive test runner with user selection."""
    display_test_menu()

    try:
        user_input = input("\nEnter test numbers (e.g., 1,3,5 or 15 for all basic): ").strip()

        if not user_input:
            print("No tests selected. Exiting.")
            return

        # Parse user input
        selected_tests = []
        for item in user_input.split(','):
            try:
                test_num = int(item.strip())
                selected_tests.append(test_num)
            except ValueError:
                print(f"Invalid test number: {item.strip()}")
                return

        print(f"\n🚀 Running selected tests: {selected_tests}")
        print("=" * 60)

        # Execute selected tests
        for test_num in selected_tests:
            if test_num == 15:
                # Run all basic examples
                print("\n📋 Running all basic examples (1-8):")
                await test_basic_examples()
            elif test_num == 16:
                # Run all operator variations
                print("\n🧪 Running all operator variations (9-14):")
                await test_operator_variations()
            elif test_num == 17:
                # Run all tests
                print("\n🎯 Running ALL tests (1-14):")
                await test_basic_examples()
                await test_operator_variations()
            elif 1 <= test_num <= 8:
                # Individual basic test
                await run_individual_basic_test(test_num)
            elif 9 <= test_num <= 14:
                # Individual operator test
                await run_individual_operator_test(test_num)
            else:
                print(f"❌ Invalid test number: {test_num}")

        print("\n✅ Selected tests completed!")
        print("\nAvailable operators: eq, ne, gt, ge, lt, le, like, startswith, endswith, contains, substringof")
        print("Note: Some operators like 'like' may not be fully supported by the Omada OData API.")

    except KeyboardInterrupt:
        print("\n\n❌ Test execution interrupted by user.")
    except Exception as e:
        print(f"❌ Error during test execution: {e}")


async def test_identity_searches():
    """Run all identity search tests."""
    print("🚀 Starting Comprehensive Identity Search Tests\n")

    await test_basic_examples()
    await test_operator_variations()

    print("\n✅ All identity search tests completed!")
    print("\nAvailable operators: eq, ne, gt, ge, lt, le, like, startswith, endswith, contains, substringof")
    print("Note: Some operators like 'like' may not be fully supported by the Omada OData API.")


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Interactive test selection")
    print("2. Run all tests")

    try:
        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":
            asyncio.run(run_selected_tests())
        else:
            print("Running all identity search tests...")
            asyncio.run(test_identity_searches())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Error: {e}")