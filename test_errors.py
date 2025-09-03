import asyncio
from server import query_omada_identity

async def test_bad_query():
    print("Testing bad OData query...")
    result = await query_omada_identity(
        filter_condition="INVALID_FIELD eq 'test' and MALFORMED SYNTAX"
    )
    print("Result:", result)

async def test_invalid_endpoint():
    print("\nTesting invalid endpoint...")
    result = await query_omada_identity(
        firstname="Emma",
        omada_base_url="https://pawa-poc2.omada.cloud/WRONG_PATH"
    )
    print("Result:", result)

async def test_network_error():
    print("\nTesting network error...")
    result = await query_omada_identity(
        firstname="Emma", 
        omada_base_url="https://nonexistent-server-12345.com"
    )
    print("Result:", result)

async def main():
    print("=== ERROR HANDLING TESTS ===")
    await test_bad_query()
    await test_invalid_endpoint() 
    await test_network_error()

if __name__ == "__main__":
    asyncio.run(main())