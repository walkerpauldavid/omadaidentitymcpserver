import asyncio
import json
from server import query_omada_resources, query_omada_entity

def display_result(result_json, test_name):
    """Display test results"""
    try:
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Total Count: {data.get('total_count', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')}")
        
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            print(f"\nSample Resources (showing first 3):")
            print("-" * 40)
            for i, resource in enumerate(data['data']['value'][:3], 1):
                resource_id = resource.get('Id', 'N/A')
                display_name = resource.get('DISPLAYNAME', 'N/A')
                resource_type = resource.get('RESOURCETYPE', {}).get('Value', 'N/A') if isinstance(resource.get('RESOURCETYPE'), dict) else 'N/A'
                
                print(f"{i}. ID: {resource_id}")
                print(f"   Display Name: {display_name}")
                print(f"   Resource Type: {resource_type}")
                print()
        else:
            print("\nNo resources found for this system")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 60)
        print("Error parsing JSON result:")
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:400] + "..." if len(clean_result) > 400 else clean_result)
        except:
            print("Unable to display error response")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Error: {repr(e)}")

async def test_resources_by_system_wrapper():
    """Test querying resources by system using the wrapper function"""
    result = await query_omada_resources(
        system_id=1011066,
        top=5,
        include_count=True
    )
    display_result(result, "Test 1: Resources for System 1011066 (via wrapper)")

async def test_resources_by_system_direct():
    """Test querying resources by system using the generic function"""
    result = await query_omada_entity(
        entity_type="Resource",
        system_id=1011066,
        top=5,
        include_count=True
    )
    display_result(result, "Test 2: Resources for System 1011066 (via generic function)")

async def test_resources_by_system_custom_filter():
    """Test querying resources by system using custom filter"""
    result = await query_omada_entity(
        entity_type="Resource",
        filter_condition="Systemref/Id eq 1011066",
        top=5,
        include_count=True
    )
    display_result(result, "Test 3: Resources for System 1011066 (via custom filter)")

async def test_combined_system_and_type():
    """Test querying resources by both system and resource type"""
    result = await query_omada_resources(
        resource_type_name="APPLICATION_ROLES",
        system_id=1011066,
        top=5,
        include_count=True
    )
    display_result(result, "Test 4: Application Roles for System 1011066 (combined filters)")

async def test_different_system():
    """Test querying resources for a different system"""
    # Let's try system ID from our earlier System tests
    result = await query_omada_resources(
        system_id=1001361,  # The Omada Identity System from our earlier test
        top=5,
        include_count=True
    )
    display_result(result, "Test 5: Resources for System 1001361 (Omada Identity System)")

async def main():
    print("=== TESTING SYSTEM-BASED RESOURCE QUERIES ===")
    print("Testing the new system_id parameter functionality")
    
    await test_resources_by_system_wrapper()
    await test_resources_by_system_direct()
    await test_resources_by_system_custom_filter()
    await test_combined_system_and_type()
    await test_different_system()

if __name__ == "__main__":
    asyncio.run(main())