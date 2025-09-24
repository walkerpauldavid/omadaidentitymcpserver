# NOTE: The tests in this file have been migrated to test_identity_search.py
# The new tests use the updated field_filters format instead of the deprecated
# firstname/lastname parameters. Please use test_identity_search.py going forward.

import asyncio
import json
from server import query_omada_identity, query_omada_entity

def display_filtered_result(result_json, test_name, show_fields=None):
    """Extract and display specific fields from the JSON result"""
    if show_fields is None:
        show_fields = ['Id', 'DISPLAYNAME']
        
    try:
        # Parse the JSON string
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 50)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')}")
        
        # Extract specified fields from data.value array
        if 'data' in data and 'value' in data['data']:
            print("\nIdentities:")
            print("-" * 30)
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
        print("=" * 50)
        print("Error parsing JSON result:")
        # Handle Unicode encoding issues by removing non-ASCII characters
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:200] + "..." if len(clean_result) > 200 else clean_result)
        except:
            print("Unable to display error response due to encoding issues")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 50)
        print(f"Error processing result: {repr(e)}")

# DEPRECATED: These tests have been migrated to test_identity_search.py with field_filters format
# 
# async def test_firstname_not_equals():
#     # Test 1: Using wrapper function
#     result = await query_omada_identity(
#         firstname="Emma",
#         firstname_operator="ne",
#         top=5,
#         select_fields="Id,FIRSTNAME"
#     )
#     display_filtered_result(result, "Test 1: Firstname NOT EQUALS 'Emma'", ['Id', 'FIRSTNAME'])
#     
#     # Test 2: Combined operators - firstname ne and lastname startswith
#     result = await query_omada_identity(
#         firstname="Emma",
#         firstname_operator="ne",
#         lastname="T",
#         lastname_operator="startswith",
#         top=3,
#         select_fields="Id,FIRSTNAME,LASTNAME"
#     )
#     display_filtered_result(result, "Test 2: Combined Operators (firstname ne 'Emma' AND lastname startswith 'T')", ['Id', 'FIRSTNAME', 'LASTNAME'])

async def test_firstname_not_equals():
    """Updated test using new field_filters format"""
    # Test 1: Using wrapper function
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"}
    ], top=5, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Test 1: Firstname NOT EQUALS 'Emma'", ['Id', 'FIRSTNAME'])
    
    # Test 2: Combined operators - firstname ne and lastname startswith
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"},
        {"field": "LASTNAME", "value": "T", "operator": "startswith"}
    ], top=3, select_fields="Id,FIRSTNAME,LASTNAME")
    display_filtered_result(result, "Test 2: Combined Operators (firstname ne 'Emma' AND lastname startswith 'T')", ['Id', 'FIRSTNAME', 'LASTNAME'])

async def test_other_operators():
    """Updated test using new field_filters format"""
    # Test contains (may not be supported by Omada)
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "mm", "operator": "contains"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Test 3: Contains Operator (firstname contains 'mm')", ['Id', 'FIRSTNAME'])
    
    # Test startswith
    result = await query_omada_identity([
        {"field": "LASTNAME", "value": "Tay", "operator": "startswith"}
    ], top=3, select_fields="Id,LASTNAME")
    display_filtered_result(result, "Test 4: Starts With Operator (lastname startswith 'Tay')", ['Id', 'LASTNAME'])
    
    # Test Like operator - appears to have syntax issues in OData
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Em%", "operator": "like"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Test 5: Like Operator (firstname like 'Em%') - May not be supported", ['Id', 'FIRSTNAME'])
    
    # Test working equals operator for comparison
    result = await query_omada_identity([
        {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
    ], top=3, select_fields="Id,FIRSTNAME")
    display_filtered_result(result, "Test 6: Equals Operator (firstname eq 'Emma') - Reference working test", ['Id', 'FIRSTNAME'])

async def main():
    print("⚠️  DEPRECATION WARNING:")
    print("This file contains updated tests but test_identity_search.py is now the recommended test file.")
    print("The tests below use the new field_filters format for compatibility.\n")
    
    await test_firstname_not_equals()
    await test_other_operators()
    
    print("\n💡 TIP: For the most comprehensive identity search tests, run:")
    print("python test_identity_search.py")

if __name__ == "__main__":
    asyncio.run(main())