#!/usr/bin/env python3
"""
Demonstrate the improved generic API vs the old hardcoded approach
"""
import asyncio
import json
from server import query_omada_entity, query_omada_entities

async def demo_old_vs_new():
    """Compare old hardcoded approach with new generic approach"""
    
    print("=== API IMPROVEMENT DEMONSTRATION ===\n")
    
    # Example 1: Identity queries
    print("[EXAMPLE 1] Identity Queries")
    print("-" * 50)
    
    print("\n[OLD] APPROACH (hardcoded, limited):")
    print("query_omada_entity(firstname='Emma', firstname_operator='eq')")
    
    print("\n[NEW] APPROACH (generic, flexible):")
    print("query_omada_entities(")
    print("    entity_type='Identity',")
    print("    field_filters=[{'field': 'FIRSTNAME', 'value': 'Emma', 'operator': 'eq'}]")
    print(")")
    
    # Example 2: Multiple fields  
    print("\n[EXAMPLE 2] Multiple Field Filtering")
    print("-" * 50)
    
    print("\n[OLD] APPROACH (only firstname + lastname):")
    print("query_omada_entity(")
    print("    firstname='Emma', firstname_operator='eq',")
    print("    lastname='Taylor', lastname_operator='eq'")
    print(")")
    
    print("\n[NEW] APPROACH (any fields, any entity):")
    print("query_omada_entities(")
    print("    entity_type='Identity',")
    print("    field_filters=[")
    print("        {'field': 'FIRSTNAME', 'value': 'Emma', 'operator': 'eq'},")
    print("        {'field': 'LASTNAME', 'value': 'Taylor', 'operator': 'eq'},")
    print("        {'field': 'EMAIL', 'value': '@company.com', 'operator': 'endswith'}")
    print("    ]")
    print(")")
    
    # Example 3: Different entities
    print("\n[EXAMPLE 3] Different Entity Types")
    print("-" * 50)
    
    print("\n[OLD] APPROACH (only worked for Identity with firstname/lastname):")
    print("query_omada_entity(entity_type='System', firstname='test')  # Makes no sense!")
    
    print("\n[NEW] APPROACH (works with any entity, any fields):")
    print("query_omada_entities(")
    print("    entity_type='System',")
    print("    field_filters=[")
    print("        {'field': 'DESCRIPTION', 'value': 'Identity System', 'operator': 'contains'},")
    print("        {'field': 'SYSTEMSTATUS', 'value': 'Active', 'operator': 'eq'}")
    print("    ]")
    print(")")
    
    # Example 4: Complex scenarios
    print("\n[EXAMPLE 4] Complex Filtering Scenarios")
    print("-" * 50)
    
    print("\n[OLD] APPROACH (impossible with hardcoded parameters):")
    print("# Can't filter Resources by DISPLAYNAME, can't filter by custom fields")
    
    print("\n[NEW] APPROACH (unlimited flexibility):")
    print("# Filter Resources by display name containing 'Admin'")
    print("query_omada_entities(")
    print("    entity_type='Resource',")
    print("    field_filters=[")
    print("        {'field': 'DISPLAYNAME', 'value': 'Admin', 'operator': 'contains'}")
    print("    ]")
    print(")")
    
    print("\n# Filter Systems by multiple criteria")
    print("query_omada_entities(")
    print("    entity_type='System',")
    print("    field_filters=[")
    print("        {'field': 'SYSTEMSTATUS', 'value': 'Active', 'operator': 'eq'},")
    print("        {'field': 'DESCRIPTION', 'value': 'AD', 'operator': 'contains'}")
    print("    ]")
    print(")")

async def demo_real_queries():
    """Show actual working queries"""
    
    print("\n\n=== REAL WORKING EXAMPLES ===\n")
    
    # Test 1: New generic approach
    print("[TEST 1] New Generic API")
    result = await query_omada_entities(
        entity_type="Identity",
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "eq"}
        ],
        top=1
    )
    
    data = json.loads(result)
    if data.get('status') == 'success':
        print(f"[SUCCESS] Found {data.get('entities_returned', 0)} identities")
        print(f"   Filter: {data.get('filter', 'N/A')}")
    else:
        print(f"[ERROR] {data.get('status', 'Unknown')}")
    
    # Test 2: Multiple fields
    print("\n[TEST 2] Multiple Field Filters")
    result = await query_omada_entities(
        entity_type="Identity",
        field_filters=[
            {"field": "FIRSTNAME", "value": "Emma", "operator": "ne"}
        ],
        top=3
    )
    
    data = json.loads(result)
    if data.get('status') == 'success':
        print(f"[SUCCESS] Found {data.get('entities_returned', 0)} identities (not Emma)")
        print(f"   Filter: {data.get('filter', 'N/A')}")
    else:
        print(f"[ERROR] {data.get('status', 'Unknown')}")
    
    # Test 3: Different entity type
    print("\n[TEST 3] System Entity with Generic Filtering")
    result = await query_omada_entities(
        entity_type="System",
        field_filters=[
            {"field": "DESCRIPTION", "value": "Identity", "operator": "contains"}
        ],
        top=2
    )
    
    data = json.loads(result)
    if data.get('status') == 'success':
        print(f"[SUCCESS] Found {data.get('entities_returned', 0)} systems")
        print(f"   Filter: {data.get('filter', 'N/A')}")
    else:
        print(f"[ERROR] {data.get('status', 'Unknown')}")

async def main():
    await demo_old_vs_new()
    await demo_real_queries()
    
    print(f"\n{'='*80}")
    print("KEY IMPROVEMENTS:")
    print("- Generic: Works with ANY field on ANY entity type")
    print("- Flexible: Multiple fields with different operators")
    print("- Extensible: Add new entities/fields without code changes")
    print("- Clean: No hardcoded parameter names")
    print("- Backward Compatible: Old functions still work")
    print("- Future Proof: Easy to extend with new functionality")
    print("="*80)
    
    print(f"\nRECOMMENDED USAGE:")
    print("- Use query_omada_entities() for new code (modern API)")
    print("- Use query_omada_entity() for backward compatibility")
    print("- Use specific wrappers like query_calculated_assignments() for convenience")

if __name__ == "__main__":
    asyncio.run(main())