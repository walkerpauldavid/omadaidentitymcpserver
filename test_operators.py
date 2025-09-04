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

async def test_firstname_not_equals():
    # Test 1: Using wrapper function
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="ne",
        top=5,
        select_fields="Id,FIRSTNAME"
    )
    display_filtered_result(result, "Test 1: Firstname NOT EQUALS 'Emma'", ['Id', 'FIRSTNAME'])
    
    # Test 2: Combined operators - firstname ne and lastname startswith
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="ne",
        lastname="T",
        lastname_operator="startswith",
        top=3,
        select_fields="Id,FIRSTNAME,LASTNAME"
    )
    display_filtered_result(result, "Test 2: Combined Operators (firstname ne 'Emma' AND lastname startswith 'T')", ['Id', 'FIRSTNAME', 'LASTNAME'])

async def test_other_operators():
    # Test contains (may not be supported by Omada)
    result = await query_omada_identity(
        firstname="mm",
        firstname_operator="contains",
        top=3,
        select_fields="Id,FIRSTNAME"
    )
    display_filtered_result(result, "Test 3: Contains Operator (firstname contains 'mm')", ['Id', 'FIRSTNAME'])
    
    # Test startswith
    result = await query_omada_identity(
        lastname="Tay",
        lastname_operator="startswith",
        top=3,
        select_fields="Id,LASTNAME"
    )
    display_filtered_result(result, "Test 4: Starts With Operator (lastname startswith 'Tay')", ['Id', 'LASTNAME'])
    
    # Test Like operator - appears to have syntax issues in OData
    result = await query_omada_identity(
        firstname="Em%",
        firstname_operator="like",
        top=3,
        select_fields="Id,FIRSTNAME"
    )
    display_filtered_result(result, "Test 5: Like Operator (firstname like 'Em%') - May not be supported", ['Id', 'FIRSTNAME'])
    
    # Test working equals operator for comparison
    result = await query_omada_identity(
        firstname="Emma",
        firstname_operator="eq",
        top=3,
        select_fields="Id,FIRSTNAME"
    )
    display_filtered_result(result, "Test 6: Equals Operator (firstname eq 'Emma') - Reference working test", ['Id', 'FIRSTNAME'])

async def main():
    await test_firstname_not_equals()
    await test_other_operators()

if __name__ == "__main__":
    asyncio.run(main())