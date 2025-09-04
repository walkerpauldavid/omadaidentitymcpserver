#!/usr/bin/env python3
"""
Quick terminal test for Calculated Assignments
Usage: python quick_test_assignments.py [identity_id]
"""
import asyncio
import sys
import json
from server import query_calculated_assignments

async def test_assignments(identity_id=1006500):
    """Test calculated assignments for a given identity"""
    print(f"\n[TEST] Testing Calculated Assignments for Identity ID: {identity_id}")
    print("=" * 60)
    
    try:
        # Get assignments
        result = await query_calculated_assignments(
            identity_id=identity_id,
            top=10,
            include_count=True
        )
        
        data = json.loads(result)
        
        if data.get('status') == 'success':
            total = data.get('total_count', 'Unknown')
            returned = data.get('entities_returned', 0)
            
            print(f"[OK] Status: Success")
            print(f"[COUNT] Total Assignments: {total}")
            print(f"[RETURNED] Returned: {returned}")
            print(f"[URL] Endpoint: {data.get('endpoint', 'N/A')[:80]}...")
            
            if 'data' in data and 'value' in data['data'] and len(data['data']['value']) > 0:
                print(f"\n[ASSIGNMENTS] Assignment Details:")
                print("-" * 40)
                
                for i, assignment in enumerate(data['data']['value'], 1):
                    key = assignment.get('AssignmentKey', 'N/A')[:8] + "..."  # Short key
                    account = assignment.get('AccountName', 'N/A')
                    
                    # Get expanded data with better handling
                    identity_data = assignment.get('Identity', {})
                    resource_data = assignment.get('Resource', {})
                    resource_type_data = assignment.get('ResourceType', {})
                    
                    # Extract names with correct field names
                    identity_name = identity_data.get('DisplayName', 'N/A') if identity_data else 'N/A'
                    resource_name = resource_data.get('DisplayName', 'N/A') if resource_data else 'N/A'
                    resource_id = resource_data.get('Id', 'N/A') if resource_data else 'N/A'
                    resource_type_name = resource_type_data.get('DisplayName', 'N/A') if resource_type_data else 'N/A'
                    
                    print(f"{i:2}. Key: {key} | Account: {account}")
                    print(f"    Identity: {identity_name}")
                    print(f"    Resource: {resource_name} (ID: {resource_id})")
                    print(f"    Type: {resource_type_name}")
                    print()
            else:
                print("[EMPTY] No assignments found for this identity")
                
        else:
            print(f"[ERROR] Error: {data.get('status', 'Unknown error')}")
            
    except Exception as e:
        print(f"[EXCEPTION] Exception: {str(e)}")

def main():
    """Main function with command line argument support"""
    # Default identity ID
    identity_id = 1006500
    
    # Check for command line argument
    if len(sys.argv) > 1:
        try:
            identity_id = int(sys.argv[1])
        except ValueError:
            print("[ERROR] Invalid identity ID. Using default: 1006500")
    
    # Run the test
    asyncio.run(test_assignments(identity_id))

if __name__ == "__main__":
    main()