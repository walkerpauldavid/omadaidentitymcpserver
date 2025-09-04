#!/usr/bin/env python3
"""
Test script to verify RESOURCEASSIGNMENT removal and CalculatedAssignments still work
"""
import asyncio
from server import query_omada_entity, query_calculated_assignments

async def test_refactor():
    print("=== TESTING ENTITY TYPE REFACTOR ===")
    
    # Test 1: RESOURCEASSIGNMENT should be rejected
    print("\n1. Testing removed RESOURCEASSIGNMENT entity:")
    try:
        result = await query_omada_entity(entity_type='RESOURCEASSIGNMENT')
        if "Invalid entity type" in result:
            print("   [OK] RESOURCEASSIGNMENT correctly rejected")
        else:
            print("   [ERROR] RESOURCEASSIGNMENT should be rejected")
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
    
    # Test 2: CalculatedAssignments should work
    print("\n2. Testing CalculatedAssignments entity:")
    try:
        result = await query_omada_entity(
            entity_type='CalculatedAssignments', 
            identity_id=1006500, 
            top=1
        )
        if "success" in result.lower():
            print("   [OK] CalculatedAssignments works correctly")
        else:
            print("   [ERROR] CalculatedAssignments failed")
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
    
    # Test 3: Wrapper function should work
    print("\n3. Testing query_calculated_assignments wrapper:")
    try:
        result = await query_calculated_assignments(identity_id=1006500, top=1)
        if "success" in result.lower():
            print("   [OK] Wrapper function works correctly")
        else:
            print("   [ERROR] Wrapper function failed")
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
    
    # Test 4: Other entities should still work
    print("\n4. Testing other entity types still work:")
    entities_to_test = ['Identity', 'Resource', 'System']
    
    for entity in entities_to_test:
        try:
            result = await query_omada_entity(entity_type=entity, top=1)
            if "success" in result.lower():
                print(f"   [OK] {entity} works correctly")
            else:
                print(f"   [ERROR] {entity} failed")
        except Exception as e:
            print(f"   [ERROR] {entity} error: {e}")
    
    print("\n=== REFACTOR TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_refactor())