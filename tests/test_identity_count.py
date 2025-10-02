import asyncio
from server import query_omada_identity

async def main():
    print("=== TESTING IDENTITY COUNT ===")
    result = await query_omada_identity(count_only=True, include_count=True)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())