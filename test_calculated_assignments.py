import asyncio
import json
from server import query_calculated_assignments, query_omada_entity

def display_assignments_result(result_json, test_name):
    """Display calculated assignments test results"""
    try:
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 70)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Total Count: {data.get('total_count', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')}")
        
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            print(f"\nCalculated Assignments Found:")
            print("-" * 50)
            for i, assignment in enumerate(data['data']['value'][:5], 1):  # Show first 5
                # Basic assignment info
                assignment_key = assignment.get('AssignmentKey', 'N/A')
                account_name = assignment.get('AccountName', 'N/A')
                
                # Expanded Identity info
                identity_info = assignment.get('Identity', {})
                identity_name = identity_info.get('DISPLAYNAME', 'N/A') if identity_info else 'N/A'
                identity_id = identity_info.get('Id', 'N/A') if identity_info else 'N/A'
                
                # Expanded Resource info
                resource_info = assignment.get('Resource', {})
                resource_name = resource_info.get('DISPLAYNAME', 'N/A') if resource_info else 'N/A'
                resource_id = resource_info.get('Id', 'N/A') if resource_info else 'N/A'
                
                # Expanded ResourceType info
                resource_type_info = assignment.get('ResourceType', {})
                resource_type_name = resource_type_info.get('DISPLAYNAME', 'N/A') if resource_type_info else 'N/A'
                
                print(f"{i}. Assignment Key: {assignment_key}")
                print(f"   Account Name: {account_name}")
                print(f"   Identity: {identity_name} (ID: {identity_id})")
                print(f"   Resource: {resource_name} (ID: {resource_id})")
                print(f"   Resource Type: {resource_type_name}")
                print()
                
            if len(data['data']['value']) > 5:
                print(f"... and {len(data['data']['value']) - 5} more assignments")
        else:
            print("\nNo calculated assignments found for this identity")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 70)
        print("Error parsing JSON result:")
        try:
            clean_result = result_json.encode('ascii', 'ignore').decode('ascii')
            print(clean_result[:500] + "..." if len(clean_result) > 500 else clean_result)
        except:
            print("Unable to display error response")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 70)
        print(f"Error: {repr(e)}")

def print_assignments_count_result(result_json, test_name, object_type):
    """Print calculated assignments count result with object count and type information."""
    try:
        data = json.loads(result_json)
        if data.get("status") == "success":
            count = data.get("count", 0)
            print(f"{test_name}: [SUCCESS] Success - Found {count} {object_type} objects")
        else:
            print(f"{test_name}: [FAILED] Failed")
            display_assignments_result(result_json, test_name)
    except (json.JSONDecodeError, AttributeError):
        if "Error" not in str(result_json) and "[FAILED]" not in str(result_json):
            print(f"{test_name}: [SUCCESS] Success (HTTP 200)")
        else:
            print(f"{test_name}: [FAILED] Failed")

async def test_count_all_calculated_assignments():
    """Count all calculated assignments in Omada system"""
    result = await query_omada_entity(
        entity_type="CalculatedAssignments",
        count_only=True,
        include_count=True
    )
    print_assignments_count_result(result, "Test 1: Count All Calculated Assignments", "Calculated Assignment")

async def test_calculated_assignments_wrapper():
    """Test the query_calculated_assignments wrapper function"""
    result = await query_calculated_assignments(
        identity_id=1006500,
        top=5,
        include_count=True
    )
    display_assignments_result(result, "Test 2: Calculated Assignments via Wrapper Function")

async def test_calculated_assignments_generic():
    """Test calculated assignments using generic function"""
    result = await query_omada_entity(
        entity_type="CalculatedAssignments",
        identity_id=1006500,
        select_fields="AssignmentKey,AccountName",
        expand="Identity,Resource,ResourceType",
        top=5,
        include_count=True
    )
    display_assignments_result(result, "Test 3: Calculated Assignments via Generic Function")

async def test_calculated_assignments_custom_select():
    """Test with custom select fields"""
    result = await query_calculated_assignments(
        identity_id=1006500,
        select_fields="AssignmentKey,AccountName,Status",
        expand="Identity,Resource",
        top=3
    )
    display_assignments_result(result, "Test 4: Custom Select Fields (AssignmentKey,AccountName,Status)")

async def test_calculated_assignments_no_expand():
    """Test without expand to see basic structure"""
    result = await query_calculated_assignments(
        identity_id=1006500,
        expand="",  # No expand
        top=3
    )
    display_assignments_result(result, "Test 5: No Expand - Basic Assignment Data Only")

async def test_calculated_assignments_different_identity():
    """Test with different identity ID"""
    result = await query_calculated_assignments(
        identity_id=1006715,  # Emma Taylor from our earlier tests
        top=5,
        include_count=True
    )
    display_assignments_result(result, "Test 6: Assignments for Identity 1006715 (Emma Taylor)")

async def test_calculated_assignments_custom_filter():
    """Test with custom filter condition"""
    result = await query_omada_entity(
        entity_type="CalculatedAssignments",
        filter_condition="Identity/Id eq 1006500",
        select_fields="AssignmentKey,AccountName",
        expand="Identity,Resource,ResourceType",
        top=3
    )
    display_assignments_result(result, "Test 7: Custom Filter (Identity/Id eq 1006500)")

async def test_endpoint_structure():
    """Test to show the endpoint structure"""
    result = await query_calculated_assignments(
        identity_id=1006500,
        top=1
    )
    
    try:
        data = json.loads(result)
        print("\n\nTest 8: Endpoint Structure Analysis")
        print("=" * 70)
        print(f"Endpoint URL Pattern: {data.get('endpoint', 'N/A')}")
        print("Expected URL Components:")
        print("- Base: /OData/BuiltIn/CalculatedAssignments")
        print("- Filter: Identity/Id eq 1006500")
        print("- Select: AssignmentKey,AccountName")
        print("- Expand: Identity,Resource,ResourceType")
        
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            assignment = data['data']['value'][0]
            print("\nSample Assignment Structure:")
            print("-" * 30)
            for key, value in assignment.items():
                if isinstance(value, dict):
                    print(f"{key}: {type(value).__name__} with {len(value)} properties")
                elif isinstance(value, list):
                    print(f"{key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"{key}: {type(value).__name__}")
                    
    except Exception as e:
        print(f"Structure analysis error: {e}")

async def main():
    print("=== TESTING CALCULATED ASSIGNMENTS ENDPOINT ===")
    print("Testing the new CalculatedAssignments functionality")
    print("Endpoint: /OData/BuiltIn/CalculatedAssignments")
    
    await test_count_all_calculated_assignments()
    await test_calculated_assignments_wrapper()
    await test_calculated_assignments_generic()
    await test_calculated_assignments_custom_select()
    await test_calculated_assignments_no_expand()
    await test_calculated_assignments_different_identity()
    await test_calculated_assignments_custom_filter()
    await test_endpoint_structure()

if __name__ == "__main__":
    asyncio.run(main())