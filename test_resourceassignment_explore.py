import asyncio
import json
from server import query_omada_entity

def display_exploration_result(result_json, test_name):
    """Display results from RESOURCEASSIGNMENT endpoint exploration"""
    try:
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Total Count: {data.get('total_count', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')}")
        
        if 'data' in data:
            context = data['data'].get('@odata.context', 'N/A')
            print(f"OData Context: {context}")
            
            if 'value' in data['data'] and len(data['data']['value']) > 0:
                print(f"\nFound {len(data['data']['value'])} resource assignments")
                # Display first assignment structure
                assignment = data['data']['value'][0]
                print("\nSample Resource Assignment Structure:")
                print("-" * 40)
                for key, value in assignment.items():
                    print(f"{key}: {type(value).__name__}")
            else:
                print("\nNo resource assignments found in the system")
        
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

async def test_resourceassignment_basic_access():
    """Test basic access to RESOURCEASSIGNMENT endpoint"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        top=10,
        include_count=True
    )
    display_exploration_result(result, "Test 1: Basic RESOURCEASSIGNMENT Access")

async def test_resourceassignment_count():
    """Test getting total count of resource assignments"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        count_only=True
    )
    display_exploration_result(result, "Test 2: Total RESOURCEASSIGNMENT Count")

async def test_resourceassignment_field_exploration():
    """Test different field names to discover the schema"""
    test_fields = [
        "IDENTITYREF",
        "RESOURCEREF", 
        "ASSIGNEDBY",
        "ASSIGNEDDATE",
        "STATUS",
        "Id",
        "DISPLAYNAME"
    ]
    
    print("\n\nTest 3: Field Discovery Tests")
    print("=" * 60)
    
    for field in test_fields:
        try:
            result = await query_omada_entity(
                entity_type="RESOURCEASSIGNMENT",
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

async def test_resourceassignment_metadata_info():
    """Display information about the RESOURCEASSIGNMENT endpoint"""
    print("\n\nTest 4: RESOURCEASSIGNMENT Endpoint Summary")
    print("=" * 60)
    print("Endpoint Name: RESOURCEASSIGNMENT")
    print("Purpose: Manages assignments of resources to identities")
    print("Current Status: Endpoint accessible but contains no data")
    print("OData Context: Resourceassignment (lowercase 'r' in metadata)")
    print("\nUseful for:")
    print("- Tracking which resources are assigned to which users")
    print("- Managing resource allocation")
    print("- Auditing resource assignments")
    print("- Bulk resource assignment operations")

async def main():
    print("=== RESOURCEASSIGNMENT ENDPOINT EXPLORATION ===")
    await test_resourceassignment_basic_access()
    await test_resourceassignment_count()
    await test_resourceassignment_field_exploration()
    await test_resourceassignment_metadata_info()

if __name__ == "__main__":
    asyncio.run(main())