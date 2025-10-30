import asyncio
import sys
sys.path.append(".")
from server import query_omada_entity

async def test_count():
    print("Testing query_omada_entity with count_only=True...")

    # Test 1: Count all identities
    result1 = await query_omada_entity(entity_type="Identity", count_only=True)
    print("All identities count:")
    print(result1)
    print()

    # Test 2: Count with filter
    result2 = await query_omada_entity(
        entity_type="Identity",
        filters={"custom_filter": "FIRSTNAME eq 'Emma'"},
        count_only=True
    )
    print("Emma count:")
    print(result2)
    print()

    # Test 3: Count systems (demonstrating flexibility)
    result3 = await query_omada_entity(entity_type="System", count_only=True)
    print("All systems count:")
    print(result3)

if __name__ == "__main__":
    asyncio.run(test_count())