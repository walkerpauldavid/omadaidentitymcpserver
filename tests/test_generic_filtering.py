#!/usr/bin/env python3
"""
Test the new generic field filtering functionality
"""
import asyncio
import json
from server import query_omada_entity

def display_test_result(result_json, test_name):
    """Display test results"""
    try:
        data = json.loads(result_json)
        
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Entity Type: {data.get('entity_type', 'N/A')}")
        print(f"Entities Returned: {data.get('entities_returned', 'N/A')}")
        print(f"Filter: {data.get('filter', 'N/A')}")
        print(f"Endpoint: {data.get('endpoint', 'N/A')[:100]}...")
        
        if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
            print(f"\nSample Results:")
            print("-" * 30)
            for i, item in enumerate(data['data']['value'][:3], 1):
                item_id = item.get('Id', 'N/A')
                display_name = item.get('DISPLAYNAME') or item.get('DisplayName', 'N/A')
                print(f"{i}. ID: {item_id}, Name: {display_name}")
        else:
            print("No data returned")
            
    except json.JSONDecodeError:
        print(f"\n{test_name}")
        print("=" * 60)
        print("Error parsing JSON result")
    except Exception as e:
        print(f"\n{test_name}")
        print("=" * 60)
        print(f"Error: {repr(e)}")

async def test_new_field_filters():
    """Test the new field_filters parameter"""
    
    # Test 1: Single field filter
    print("Testing new generic field filtering approach...")
    
    result = await query_omada_entity(
        entity_type="Identity",
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
        ],
        top=3
    )
    display_test_result(result, "Test 1: New Generic Field Filter (FIRSTNAME eq 'Emma')")
    
    # Test 2: Multiple field filters
    result = await query_omada_entity(
        entity_type="Identity", 
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
            {"field": "LASTNAME", "value": "T", "operator": "startswith"}
        ],
        top=3
    )
    display_test_result(result, "Test 2: Multiple Field Filters (FIRSTNAME eq 'Emma' AND LASTNAME startswith 'T')")
    
    # Test 3: Different operators
    result = await query_omada_entity(
        entity_type="Identity",
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"}
        ],
        top=5
    )
    display_test_result(result, "Test 3: Different Operator (FIRSTNAME ne 'Emma')")
    
    # Test 4: Generic field filtering on System entities
    result = await query_omada_entity(
        entity_type="System",
        field_filters=[
            {"field": "DESCRIPTION", "value": "The Omada Identity System", "operator": "eq"}
        ],
        top=2
    )
    display_test_result(result, "Test 4: Generic Filtering on System Entity")

async def test_backward_compatibility():
    """Test that old firstname/lastname parameters still work"""
    
    # Test 5: Backward compatibility - old parameters
    result = await query_omada_entity(
        entity_type="Identity",
        firstname="Emma",
        firstname_operator="eq",
        top=3
    )
    display_test_result(result, "Test 5: Backward Compatibility (firstname='Emma')")

async def test_comparison():
    """Compare old vs new approach"""
    
    print("\n" + "="*80)
    print("COMPARISON: OLD vs NEW APPROACH")
    print("="*80)
    
    # Old approach
    result_old = await query_omada_entity(
        entity_type="Identity",
        firstname="Emma",
        lastname="Taylor",
        firstname_operator="eq",
        lastname_operator="eq",
        top=1
    )
    
    # New approach
    result_new = await query_omada_entity(
        entity_type="Identity",
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"},
            {"field": "LASTNAME", "value": "Taylor", "operator": "eq"}
        ],
        top=1
    )
    
    display_test_result(result_old, "OLD APPROACH: firstname + lastname parameters")
    display_test_result(result_new, "NEW APPROACH: field_filters parameter")
    
    # Compare results
    try:
        data_old = json.loads(result_old)
        data_new = json.loads(result_new)
        
        print(f"\nRESULT COMPARISON:")
        print(f"Old approach entities: {data_old.get('entities_returned', 0)}")
        print(f"New approach entities: {data_new.get('entities_returned', 0)}")
        print(f"Results match: {data_old.get('entities_returned') == data_new.get('entities_returned')}")
        
    except Exception as e:
        print(f"Comparison error: {e}")

async def main():
    print("=== TESTING GENERIC FIELD FILTERING ===")
    await test_new_field_filters()
    await test_backward_compatibility()
    await test_comparison()
    
    print(f"\n{'='*80}")
    print("NEW APPROACH BENEFITS:")
    print("- Generic: Works with any field on any entity type")
    print("- Flexible: Multiple fields with different operators")
    print("- Clean: No hardcoded parameter names")
    print("- Extensible: Easy to add new fields without code changes")
    print("- Backward Compatible: Old parameters still work")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())