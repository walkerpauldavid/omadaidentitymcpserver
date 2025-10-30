#!/usr/bin/env python3
"""
Test class for Omada GraphQL endpoints.
This test suite includes examples from server.py and the compliance workbench query.
"""

import os
import asyncio
import json
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import unittest


class TestOmadaGraphQL(unittest.TestCase):
    """Test class for Omada GraphQL API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Load environment variables
        load_dotenv()

        # Validate required environment variables
        cls.tenant_id = os.getenv("TENANT_ID")
        cls.client_id = os.getenv("CLIENT_ID")
        cls.client_secret = os.getenv("CLIENT_SECRET")
        cls.omada_base_url = os.getenv("OMADA_BASE_URL")
        cls.oauth2_scope = os.getenv("OAUTH2_SCOPE", "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default")

        if not all([cls.tenant_id, cls.client_id, cls.client_secret, cls.omada_base_url]):
            raise ValueError("Missing required environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET, OMADA_BASE_URL")

        # Remove trailing slash from base URL
        cls.omada_base_url = cls.omada_base_url.rstrip('/')

        # Build URLs
        cls.access_token_url = f"https://login.microsoftonline.com/{cls.tenant_id}/oauth2/v2.0/token"
        cls.graphql_url = f"{cls.omada_base_url}/api/Domain/2.6"

        # Cache for access token
        cls._cached_token = None

        print(f"✅ Test setup complete:")
        print(f"   GraphQL URL: {cls.graphql_url}")
        print(f"   OAuth2 Scope: {cls.oauth2_scope}")

    async def get_access_token(self) -> Dict[str, Any]:
        """Get OAuth2 access token using client credentials flow."""
        if self._cached_token:
            return self._cached_token

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.oauth2_scope
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.access_token_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()

                token_data = response.json()
                self._cached_token = token_data
                print(f"✅ OAuth2 token acquired successfully")
                return token_data

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text

                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")
            except Exception as e:
                raise Exception(f"Token request failed: {str(e)}")

    async def make_graphql_request(self, query: str, variables: Dict = None,
                                 impersonate_user: str = "test@domain.com") -> Dict:
        """Make a GraphQL request to Omada."""
        # Get access token
        token_info = await self.get_access_token()
        token = token_info.get('access_token')
        if not token:
            raise Exception("Failed to obtain access token")

        # Build GraphQL payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "impersonate_user": impersonate_user
        }

        # Make the GraphQL request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "json": response.json() if response.status_code == 200 else None
            }

    def test_compliance_workbench_query(self):
        """Test the compliance workbench GraphQL query from cw_graph_response.txt."""
        async def run_test():
            query = """query MyQuery {
  complianceWorkbenchData(
    filters: {showAccounts: true, isApplicationAccountsSystemVisible: false}
  ) {
    system {
      id
      name
      systemCategory {
        displayName
        policyDefinitions
      }
    }
    complianceStatus {
      explicitlyApproved
      implicitlyApproved
      implicitlyAssigned
      inViolation
      none
      notApproved
      orhpaned
      pendingDeprovisioning
    }
  }
}"""

            print("🔍 Testing Compliance Workbench Query...")
            response = await self.make_graphql_request(query)

            self.assertEqual(response["status_code"], 200,
                           f"Expected status 200, got {response['status_code']}: {response['body']}")

            json_response = response["json"]
            self.assertIn("data", json_response, "Response should contain 'data' field")

            if "complianceWorkbenchData" in json_response["data"]:
                workbench_data = json_response["data"]["complianceWorkbenchData"]
                print(f"✅ Compliance Workbench Query successful!")
                print(f"   Systems found: {len(workbench_data.get('system', []))}")

                # Print sample data
                if workbench_data.get('system'):
                    sample_system = workbench_data['system'][0]
                    print(f"   Sample system: {sample_system.get('name', 'N/A')} (ID: {sample_system.get('id', 'N/A')})")

                if workbench_data.get('complianceStatus'):
                    status = workbench_data['complianceStatus']
                    print(f"   Compliance Status: {json.dumps(status, indent=2)}")
            else:
                print(f"❌ No compliance workbench data found in response")
                print(f"   Response: {json.dumps(json_response, indent=2)}")

        # Run the async test
        asyncio.run(run_test())

    def test_access_requests_query(self):
        """Test the access requests GraphQL query from server.py."""
        async def run_test():
            query = """query GetAccessRequests {
  accessRequests {
    total
    data {
      id
      beneficiary {
        id
        identityId
        displayName
        contexts {
          id
        }
      }
      resource {
        name
      }
      status {
        approvalStatus
      }
    }
  }
}"""

            print("🔍 Testing Access Requests Query...")
            response = await self.make_graphql_request(query)

            self.assertEqual(response["status_code"], 200,
                           f"Expected status 200, got {response['status_code']}: {response['body']}")

            json_response = response["json"]
            self.assertIn("data", json_response, "Response should contain 'data' field")

            if "accessRequests" in json_response["data"]:
                access_requests = json_response["data"]["accessRequests"]
                total = access_requests.get("total", 0)
                requests = access_requests.get("data", [])

                print(f"✅ Access Requests Query successful!")
                print(f"   Total requests: {total}")
                print(f"   Requests returned: {len(requests)}")

                if requests:
                    sample_request = requests[0]
                    print(f"   Sample request ID: {sample_request.get('id', 'N/A')}")
                    if sample_request.get('beneficiary'):
                        print(f"   Beneficiary: {sample_request['beneficiary'].get('displayName', 'N/A')}")
            else:
                print(f"❌ No access requests found in response")
                print(f"   Response: {json.dumps(json_response, indent=2)}")

        # Run the async test
        asyncio.run(run_test())

    def test_access_requests_with_filter(self):
        """Test the access requests GraphQL query with filter from server.py."""
        async def run_test():
            # Using a common status filter as an example
            filter_field = "status"
            filter_value = "PENDING"

            query = f"""query GetAccessRequests {{
  accessRequests(filters: {{{filter_field}: {json.dumps(filter_value)}}}) {{
    total
    data {{
      id
      beneficiary {{
        id
        identityId
        displayName
        contexts {{
          id
        }}
      }}
      resource {{
        name
      }}
      status {{
        approvalStatus
      }}
    }}
  }}
}}"""

            print(f"🔍 Testing Access Requests Query with Filter ({filter_field}={filter_value})...")
            response = await self.make_graphql_request(query)

            self.assertEqual(response["status_code"], 200,
                           f"Expected status 200, got {response['status_code']}: {response['body']}")

            json_response = response["json"]
            self.assertIn("data", json_response, "Response should contain 'data' field")

            if "accessRequests" in json_response["data"]:
                access_requests = json_response["data"]["accessRequests"]
                total = access_requests.get("total", 0)
                requests = access_requests.get("data", [])

                print(f"✅ Filtered Access Requests Query successful!")
                print(f"   Total filtered requests: {total}")
                print(f"   Requests returned: {len(requests)}")
            else:
                print(f"❌ No filtered access requests found in response")
                print(f"   Response: {json.dumps(json_response, indent=2)}")

        # Run the async test
        asyncio.run(run_test())

    def test_identity_contexts_query(self):
        """Test the identity contexts GraphQL query from server.py."""
        async def run_test():
            # Using a sample identity ID - you may need to adjust this
            identity_id = "e3e869c4-369a-476e-a969-d57059d0b1e4"

            query = f'query accessRequest {{\\r\\n    accessRequest {{\\r\\n        contexts(identityIds:["{identity_id}"]) {{ \\r\\n            id\\r\\n            name\\r\\n         }}\\r\\n    }}\\r\\n}}'

            print(f"🔍 Testing Identity Contexts Query (Identity ID: {identity_id})...")
            response = await self.make_graphql_request(query)

            self.assertEqual(response["status_code"], 200,
                           f"Expected status 200, got {response['status_code']}: {response['body']}")

            json_response = response["json"]
            self.assertIn("data", json_response, "Response should contain 'data' field")

            if "accessRequest" in json_response["data"]:
                access_request = json_response["data"]["accessRequest"]
                contexts = access_request.get("contexts", [])

                print(f"✅ Identity Contexts Query successful!")
                print(f"   Contexts found: {len(contexts)}")

                if contexts:
                    for i, context in enumerate(contexts[:3]):  # Show first 3
                        print(f"   Context {i+1}: {context.get('name', 'N/A')} (ID: {context.get('id', 'N/A')})")
            else:
                print(f"❌ No identity contexts found in response")
                print(f"   Response: {json.dumps(json_response, indent=2)}")

        # Run the async test
        asyncio.run(run_test())

    def test_token_acquisition(self):
        """Test OAuth2 token acquisition."""
        async def run_test():
            print("🔍 Testing OAuth2 Token Acquisition...")
            token_data = await self.get_access_token()

            self.assertIn("access_token", token_data, "Token response should contain access_token")
            self.assertIn("token_type", token_data, "Token response should contain token_type")
            self.assertEqual(token_data["token_type"], "Bearer", "Token type should be Bearer")

            print(f"✅ OAuth2 Token acquired successfully!")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Expires in: {token_data.get('expires_in')} seconds")
            print(f"   Scope: {token_data.get('scope', 'N/A')}")

        # Run the async test
        asyncio.run(run_test())


if __name__ == "__main__":
    import sys

    # Check if user wants to run specific test
    if len(sys.argv) > 1 and sys.argv[1] == "compliance":
        print("🚀 Running Compliance Workbench Query Test Only...")
        print("=" * 60)

        # Run just the compliance workbench test
        suite = unittest.TestSuite()
        suite.addTest(TestOmadaGraphQL('test_token_acquisition'))
        suite.addTest(TestOmadaGraphQL('test_compliance_workbench_query'))

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    elif len(sys.argv) > 1 and sys.argv[1] == "access":
        print("🚀 Running Access Requests Query Tests Only...")
        print("=" * 60)

        # Run just the access requests tests
        suite = unittest.TestSuite()
        suite.addTest(TestOmadaGraphQL('test_token_acquisition'))
        suite.addTest(TestOmadaGraphQL('test_access_requests_query'))
        suite.addTest(TestOmadaGraphQL('test_access_requests_with_filter'))

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        print("🚀 Starting Omada GraphQL Tests...")
        print("=" * 60)

        # Create a test suite with specific test order
        suite = unittest.TestSuite()

        # Add tests in logical order
        suite.addTest(TestOmadaGraphQL('test_token_acquisition'))
        suite.addTest(TestOmadaGraphQL('test_compliance_workbench_query'))
        suite.addTest(TestOmadaGraphQL('test_access_requests_query'))
        suite.addTest(TestOmadaGraphQL('test_access_requests_with_filter'))
        suite.addTest(TestOmadaGraphQL('test_identity_contexts_query'))

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

    print("=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")

        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)

        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)