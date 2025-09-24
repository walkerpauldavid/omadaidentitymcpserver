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


async def test_identity_searches():
    """Run all identity search tests."""
    print("🚀 Starting Comprehensive Identity Search Tests\n")
    
    await test_basic_examples()
    await test_operator_variations()
    
    print("\n✅ All identity search tests completed!")
    print("\nAvailable operators: eq, ne, gt, ge, lt, le, like, startswith, endswith, contains, substringof")
    print("Note: Some operators like 'like' may not be fully supported by the Omada OData API.")


if __name__ == "__main__":
    print("Starting identity search tests...")
    asyncio.run(test_identity_searches())