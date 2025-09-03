import asyncio
import json
from server import query_omada_entity

def display_system_result(result_json, test_name):
    """Extract and display specific fields from System JSON result"""
    try:
        # Parse the JSON string
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Total Count: {data.get('total_count', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')}")
        
        # Extract system data from the response
        if 'data' in data and 'value' in data['data']:
            print("\nSystems Found:")
            print("-" * 40)
            for i, system in enumerate(data['data']['value'], 1):
                system_id = system.get('Id', 'N/A')
                display_name = system.get('DISPLAYNAME', 'N/A')
                system_name = system.get('SYSTEMNAME', 'N/A')
                system_type = system.get('SYSTEMTYPE', {}).get('Value', 'N/A') if isinstance(system.get('SYSTEMTYPE'), dict) else system.get('SYSTEMTYPE', 'N/A')
                description = system.get('DESCRIPTION', 'N/A')
                
                print(f"{i}. ID: {system_id}")
                print(f"   Display Name: {display_name}")
                print(f"   System Name: {system_name}")
                print(f"   System Type: {system_type}")
                print(f"   Description: {description}")
                print()
                
        else:
            print("\nNo system data found")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 60)
        print("Error parsing JSON result:")
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:400] + "..." if len(clean_result) > 400 else clean_result)
        except:
            print("Unable to display error response due to encoding issues")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Error processing result: {repr(e)}")

async def test_system_count():
    """Test getting total count of systems"""
    result = await query_omada_entity(
        entity_type="System",
        count_only=True,
        include_count=True
    )
    display_system_result(result, "Test 1: Count All Systems")

async def test_system_sample():
    """Test getting a sample of systems"""
    result = await query_omada_entity(
        entity_type="System",
        top=10,
        include_count=True
    )
    display_system_result(result, "Test 2: Sample Systems (Top 10)")

async def test_system_by_name():
    """Test filtering systems by name"""
    result = await query_omada_entity(
        entity_type="System",
        filter_condition="contains(DISPLAYNAME, 'AD')",
        top=5
    )
    display_system_result(result, "Test 3: Systems containing 'AD' in display name")

async def test_system_by_type():
    """Test filtering systems by type"""
    result = await query_omada_entity(
        entity_type="System",
        filter_condition="SYSTEMTYPE/Value eq 'Active Directory'",
        top=5
    )
    display_system_result(result, "Test 4: Active Directory Systems")

async def test_system_structure():
    """Test to explore the structure of a single system"""
    result = await query_omada_entity(
        entity_type="System",
        top=1
    )
    
    try:
        data = json.loads(result)
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            print("\nTest 5: System Structure Analysis")
            print("=" * 60)
            system = data['data']['value'][0]
            print("Available fields in System:")
            print("-" * 40)
            for key, value in system.items():
                if isinstance(value, dict) and 'Value' in value:
                    print(f"{key}: {value.get('Value', 'N/A')} (lookup field)")
                elif isinstance(value, dict):
                    print(f"{key}: {type(value).__name__} with keys: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"{key}: {type(value).__name__} with {len(value)} items")
                else:
                    value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"{key}: {type(value).__name__} = {value_str}")
    except Exception as e:
        print(f"Error analyzing structure: {e}")

async def test_system_field_discovery():
    """Test different field names to discover the schema"""
    test_fields = [
        "SYSTEMNAME",
        "SYSTEMTYPE", 
        "DESCRIPTION",
        "STATUS",
        "CONNECTIONSTRING",
        "HOSTNAME",
        "PORT",
        "ENABLED",
        "Id",
        "DISPLAYNAME"
    ]
    
    print("\n\nTest 6: System Field Discovery")
    print("=" * 60)
    
    for field in test_fields:
        try:
            result = await query_omada_entity(
                entity_type="System",
                filter_condition=f"{field} ne null",
                top=1
            )
            
            data = json.loads(result)
            if data.get('status') == 'success':
                print(f"[OK] {field}: EXISTS")
            else:
                print(f"[ERR] {field}: ERROR - {data.get('status', 'unknown')}")
                
        except Exception as e:
            if "Could not find a property named" in str(e):
                print(f"[NO] {field}: NOT FOUND")
            else:
                print(f"[ERR] {field}: ERROR - {str(e)[:50]}")

async def main():
    print("=== TESTING SYSTEM ENDPOINT ===")
    await test_system_count()
    await test_system_sample()
    await test_system_by_name()
    await test_system_by_type()
    await test_system_structure()
    await test_system_field_discovery()

if __name__ == "__main__":
    asyncio.run(main())