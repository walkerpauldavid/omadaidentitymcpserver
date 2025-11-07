import asyncio

from server import query_omada_identity


async def test_bad_query():
    print("Testing bad OData query...")
    result = await query_omada_identity(
        filter_condition="INVALID_FIELD eq 'test' and MALFORMED SYNTAX"
    )
    print("Result:", result)


async def main():
    print("=== ERROR HANDLING TESTS ===")
    await test_bad_query()
    await test_invalid_endpoint()
    await test_network_error()


if __name__ == "__main__":
    asyncio.run(main())
