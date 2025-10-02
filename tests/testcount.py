import asyncio
import sys
sys.path.append(".")
from server import count_omada_identities

async def test_count():
    print("Testing count_omada_identities...")

    # Test 1: Count all identities
    result1 = await count_omada_identities()
    print("All identities count:")
    print(result1)
    print()

    # Test 2: Count with filter
    result2 = await count_omada_identities(filter_condition="FIRSTNAME eq 'Emma'")
    print("Emma count:")
    print(result2)

if __name__ == "__main__":
    asyncio.run(test_count())