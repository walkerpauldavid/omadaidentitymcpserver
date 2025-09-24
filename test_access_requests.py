import asyncio
from server import get_access_requests

async def test_access_requests():
    """Test the get_access_requests function with robwol@54mvc.onmicrosoft.com"""
    
    print("=== TESTING ACCESS REQUESTS GRAPHQL FUNCTION ===")
    print("Testing with email: robwol@54mvc.onmicrosoft.com")
    print()
    
    result = await get_access_requests("robwol@54mv4c.onmicrosoft.com")
    print("Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_access_requests())