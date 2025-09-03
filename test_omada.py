import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from server import query_omada_identity, query_omada_resources, _cached_token

async def test_identity_query():
    print("=== TESTING IDENTITY QUERIES ===")
    global _cached_token
    # Clear cached token to ensure fresh request
    _cached_token = None
    
    try:
        result = await query_omada_identity("Emma", "Taylor", "https://pawa-poc2.omada.cloud")
        print("Identity Query Result:", result)
    except Exception as e:
        print(f"Identity Query Error: {str(e)}")

async def test_count_application_roles():
    print("\n=== TESTING APPLICATION ROLES COUNT ===")
    result = await query_omada_resources(
        resource_type_name="APPLICATION_ROLES",
        count_only=True
    )
    print("Count Result:", result)

async def test_get_all_application_roles():
    print("\n=== TESTING GET ALL APPLICATION ROLES ===")
    result = await query_omada_resources(
        resource_type_name="APPLICATION_ROLES",
        top=10,
        include_count=True
    )
    print("All Roles Result:", result)

async def test_get_application_roles_by_name():
    print("\n=== TESTING APPLICATION ROLES FILTERED BY NAME ===")
    result = await query_omada_resources(
        resource_type_name="APPLICATION_ROLES",
        filter_condition="contains(DISPLAYNAME, 'Admin')",
        top=5
    )
    print("Filtered Roles Result:", result)

async def test_application_roles_with_id():
    print("\n=== TESTING APPLICATION ROLES WITH NUMERIC ID ===")
    result = await query_omada_resources(
        resource_type_id=1011066,
        top=5
    )
    print("Numeric ID Result:", result)

async def main():
    await test_identity_query()
    await test_count_application_roles()
    await test_get_all_application_roles()
    await test_get_application_roles_by_name()
    await test_application_roles_with_id()

if __name__ == "__main__":
    asyncio.run(main())