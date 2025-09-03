import asyncio
import json
from server import query_omada_entity

def display_resource_assignment_result(result_json, test_name):
    """Extract and display specific fields from RESOURCEASSIGNMENTS JSON result"""
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
        
        # Extract data from the response
        if 'data' in data and 'value' in data['data']:
            print("\nResource Assignments Sample:")
            print("-" * 40)
            # Show first 3 assignments with key fields
            for i, item in enumerate(data['data']['value'][:3], 1):
                assignment_id = item.get('Id', 'N/A')
                display_name = item.get('DISPLAYNAME', 'N/A')
                resource_name = item.get('RESOURCENAME', 'N/A')
                identity_name = item.get('IDENTITYNAME', 'N/A')
                assignment_type = item.get('ASSIGNMENTTYPE', {}).get('Value', 'N/A')
                status = item.get('ASSIGNMENTSTATUS', {}).get('Value', 'N/A')
                
                print(f"{i}. ID: {assignment_id}")
                print(f"   Display Name: {display_name}")
                print(f"   Resource: {resource_name}")
                print(f"   Identity: {identity_name}")
                print(f"   Type: {assignment_type}")
                print(f"   Status: {status}")
                print()
                
            if len(data['data']['value']) > 3:
                print(f"... and {len(data['data']['value']) - 3} more assignments")
        else:
            print("\nNo resource assignment data found")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 60)
        print("Error parsing JSON result:")
        # Handle Unicode encoding issues
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:300] + "..." if len(clean_result) > 300 else clean_result)
        except:
            print("Unable to display error response due to encoding issues")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Error processing result: {repr(e)}")

async def test_resourceassignments_count():
    """Test getting total count of resource assignments"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        count_only=True,
        include_count=True
    )
    display_resource_assignment_result(result, "Test 1: Count All Resource Assignments")

async def test_resourceassignments_sample():
    """Test getting a sample of resource assignments"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        top=5,
        include_count=True
    )
    display_resource_assignment_result(result, "Test 2: Sample Resource Assignments (Top 5)")

async def test_resourceassignments_by_identity():
    """Test filtering resource assignments by identity name"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        filter_condition="contains(IDENTITYNAME, 'Emma')",
        top=10
    )
    display_resource_assignment_result(result, "Test 3: Resource Assignments for Identities containing 'Emma'")

async def test_resourceassignments_by_resource():
    """Test filtering resource assignments by resource name"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        filter_condition="contains(RESOURCENAME, 'Admin')",
        top=10
    )
    display_resource_assignment_result(result, "Test 4: Resource Assignments containing 'Admin' in resource name")

async def test_resourceassignments_by_status():
    """Test filtering resource assignments by assignment status"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        filter_condition="ASSIGNMENTSTATUS/Value eq 'Assigned'",
        top=10
    )
    display_resource_assignment_result(result, "Test 5: Active Resource Assignments (Status = 'Assigned')")

async def test_resourceassignments_structure():
    """Test to explore the structure of a single resource assignment"""
    result = await query_omada_entity(
        entity_type="RESOURCEASSIGNMENT",
        top=1
    )
    
    try:
        data = json.loads(result)
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            print("\nTest 6: Resource Assignment Structure Analysis")
            print("=" * 60)
            assignment = data['data']['value'][0]
            print("Available fields in RESOURCEASSIGNMENTS:")
            print("-" * 40)
            for key, value in assignment.items():
                if isinstance(value, dict) and 'Value' in value:
                    print(f"{key}: {value.get('Value', 'N/A')} (lookup field)")
                elif isinstance(value, dict):
                    print(f"{key}: {type(value).__name__} with keys: {list(value.keys())}")
                else:
                    print(f"{key}: {type(value).__name__}")
    except Exception as e:
        print(f"Error analyzing structure: {e}")

async def main():
    print("=== TESTING RESOURCEASSIGNMENTS ENDPOINT ===")
    await test_resourceassignments_count()
    await test_resourceassignments_sample()
    await test_resourceassignments_by_identity()
    await test_resourceassignments_by_resource()
    await test_resourceassignments_by_status()
    await test_resourceassignments_structure()

if __name__ == "__main__":
    asyncio.run(main())