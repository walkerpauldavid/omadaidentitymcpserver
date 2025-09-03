import asyncio
import json
from server import query_omada_identity, query_omada_entity

def display_filtered_result(result_json, test_name):
    """Extract and display only specific fields from the JSON result"""
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
        
        # Extract ID and DisplayName from data.value array
        if 'data' in data and 'value' in data['data']:
            print("\nIdentities:")
            print("-" * 30)
            for i, item in enumerate(data['data']['value'], 1):
                item_id = item.get('Id', 'N/A')
                display_name = item.get('DISPLAYNAME', 'N/A')
                print(f"{i}. ID: {item_id}, DisplayName: {display_name}")
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

async def test_firstname_not_equals():
    # Test 1: Using wrapper function
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="ne",
        top=5
    )
    display_filtered_result(result, "Test 1: Firstname NOT EQUALS 'Emma'")
    
    # Test 2: Using direct entity function
    result = await query_omada_entity(
        entity_type="Identity",
        firstname="Emma",
        firstname_operator="ne",
        top=5,
        include_count=True
    )
    display_filtered_result(result, "Test 2: Direct Entity Query (firstname ne 'Emma')")
    
    # Test 3: Combined operators - firstname ne and lastname startswith
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="ne",
        lastname="T",
        lastname_operator="startswith",
        top=3
    )
    display_filtered_result(result, "Test 3: Combined Operators (firstname ne 'Emma' AND lastname startswith 'T')")

async def test_other_operators():
    # Test contains (may not be supported by Omada)
    result = await query_omada_identity(
        firstname="mm",
        firstname_operator="contains",
        top=3
    )
    display_filtered_result(result, "Test 4: Contains Operator (firstname contains 'mm')")
    
    # Test startswith
    result = await query_omada_identity(
        lastname="Tay",
        lastname_operator="startswith",
        top=3
    )
    display_filtered_result(result, "Test 5: Starts With Operator (lastname startswith 'Tay')")
    
    # Test Like operator - appears to have syntax issues in OData
    result = await query_omada_identity(
        firstname="Em%",
        firstname_operator="like",
        top=3
    )
    display_filtered_result(result, "Test 6: Like Operator (firstname like 'Em%') - May not be supported")
    
    # Test working equals operator for comparison
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="eq",
        top=3
    )
    display_filtered_result(result, "Test 7: Equals Operator (firstname eq 'Emma') - Reference working test")

async def main():
    await test_firstname_not_equals()
    await test_other_operators()

if __name__ == "__main__":
    asyncio.run(main())