"""
Test script for get_identity_contexts function
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the current directory to the path to import server module
sys.path.insert(0, os.path.dirname(__file__))

from server import get_identity_contexts

# Load environment variables
load_dotenv()

async def test_get_identity_contexts():
    """Test the get_identity_contexts function"""

    # Test parameters - modify these as needed
    identity_id = "5da7f8fc-0119-46b0-a6b4-06e5c78edf68"  # Replace with actual identity ID
    impersonate_user = "berbla@54MV4C.ONMICROSOFT.COM"  # Replace with actual email

    print("="*80)
    print("Testing get_identity_contexts function")
    print("="*80)
    print(f"Identity ID: {identity_id}")
    print(f"Impersonate User: {impersonate_user}")
    print(f"Omada Base URL: {os.getenv('OMADA_BASE_URL')}")
    print("="*80)
    print()

    try:
        # Call the function
        result = await get_identity_contexts(
            identity_id=identity_id,
            impersonate_user=impersonate_user
        )

        print("✅ Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 Starting get_identity_contexts tests\n")

    # Run the main test
    asyncio.run(test_get_identity_contexts())

    print("\n✅ All tests completed!")
