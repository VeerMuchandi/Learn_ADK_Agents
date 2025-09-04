import json
import logging
import os

import requests
from dotenv import load_dotenv # Keep this import
from google.adk.tools.tool_context import ToolContext

from oauth_helper import get_user_credentials

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

# The endpoint for the People API
PEOPLE_API_URL = "https://people.googleapis.com/v1/people/me"

# Scopes define the level of access you are requesting.
SCOPES = [
    "https://www.googleapis.com/auth/user.addresses.read",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def test_get_user_address(tool_context: ToolContext) -> str:
  """
  Tests fetching a user's home and work addresses from the People API.

  This function handles the OAuth 2.0 flow and makes a request to the
  People API to retrieve the user's addresses.

  Args:
      tool_context: The context of the tool run, provided by the ADK.

  Returns:
      A string containing the user's addresses or an error message.
  """
  logging.info("Tool called: Testing getting user address.")
  client_id = os.getenv("GOOGLE_CLIENT_ID")
  client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
  # For local testing, we override the redirect URI to use a simple
  # loopback address that is configured in the Google Cloud OAuth client.
  redirect_uri = "http://localhost:8080"

  if not all([client_id, client_secret, redirect_uri]):
    return "Error: OAuth Client ID, Secret, or Redirect URI is not configured in the .env file."

  creds = get_user_credentials(
      tool_context=tool_context,
      client_id=client_id,
      client_secret=client_secret,
      redirect_uri=redirect_uri,
      scopes=SCOPES,
      credential_cache_key="people_api_test_creds",
  )

  if not creds:
    return "To get your address, I need you to sign in with your Google account first. Please follow the link to authorize me."

  # At this point, we have valid credentials. Make the API call.
  try:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
      return "Error: GOOGLE_CLOUD_PROJECT_ID is not set in the environment."

    people_headers = {
        "Authorization": f"Bearer {creds.token}",
        "X-Goog-User-Project": project_id,
    }
    # Request both addresses and names for better context
    params = {"personFields": "addresses,names"}

    people_response = requests.get(
        PEOPLE_API_URL, headers=people_headers, params=params
    )
    people_response.raise_for_status()
    profile_data = people_response.json()

    logging.info(f"People API response: {json.dumps(profile_data, indent=2)}")

    if "addresses" in profile_data:
      return f"Successfully retrieved addresses:\n{json.dumps(profile_data['addresses'], indent=2)}"
    else:
      return "Could not find any addresses in your Google profile."

  except requests.exceptions.HTTPError as e:
    logging.error(f"HTTP Error during People API call: {e}")
    return f"I encountered an API error while trying to get your profile address: {e.response.text}"
  except Exception as e:
    logging.error(
        "An unexpected error occurred in test_get_user_address: %s", e, exc_info=True
    )
    return "Sorry, an unexpected error occurred while trying to get your profile address."


# Define simple mock classes for AuthResponse and OAuth2AuthResponse
# as they are likely internal ADK types not meant for direct import.
class _MockOAuth2AuthResponse:
    def __init__(self, access_token: str, refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token

class _MockAuthResponse:
    def __init__(self, oauth2: _MockOAuth2AuthResponse):
        self.oauth2 = oauth2

class MockToolContext(ToolContext):
    """A mock ToolContext for running the test script locally."""

    # The real InvocationContext is complex, so we create a minimal mock
    # that satisfies the ToolContext constructor's type requirements.
    class _MockInvocationContext:
        def __init__(self) -> None:
            # The ToolContext expects invocation_context.session to be a Session object
            # with at least a 'state' attribute.
            class _MockSession:
                def __init__(self) -> None:
                    self.state = {}

            self.session = _MockSession()

    def __init__(self) -> None:
        # Pass a mock invocation context to the parent constructor.
        super().__init__(invocation_context=self._MockInvocationContext())
        self._auth_response: _MockAuthResponse | None = None

    def refresh(self, request: requests.Request) -> None:
        """Simulates refreshing an expired credential."""
        logging.info("Attempting to refresh credentials...")
        creds_json = self.state.get("people_api_test_creds")
        if not creds_json:
            logging.error("No cached credentials found in state to refresh.")
            return

        creds_data = json.loads(creds_json)
        refresh_token = creds_data.get("refresh_token")

        if not refresh_token:
            logging.warning("No refresh token found in cached credentials. Cannot refresh.")
            return

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        token_response.raise_for_status()
        creds_data["token"] = token_json["access_token"]
        self.state["people_api_test_creds"] = json.dumps(creds_data)

    def get_auth_response(self, auth_config) -> _MockAuthResponse | None:
        """Returns the stored auth response."""
        return self._auth_response

    def request_credential(self, auth_config):
        """Simulates requesting a credential by printing the auth URL."""
        auth_url = auth_config.auth_scheme.flows.authorizationCode.authorizationUrl
        client_id = auth_config.raw_auth_credential.oauth2.client_id
        redirect_uri = auth_config.raw_auth_credential.oauth2.redirect_uri
        scopes = " ".join(auth_config.auth_scheme.flows.authorizationCode.scopes)

        # Construct the full authorization URL
        full_auth_url = (
            f"{auth_url}?response_type=code&client_id={client_id}"
            f"&redirect_uri={redirect_uri}&scope={scopes}"
            f"&access_type=offline&prompt=consent"
        )

        print("\n--- PLEASE AUTHENTICATE ---")
        print("1. Open the following URL in your browser:")
        print(f"   {full_auth_url}")
        print("\n2. After authorizing, you will be redirected to a URL.")
        print("   Copy the full redirect URL and paste it below.")

        redirect_url_with_code = input("Enter the full redirect URL: ")

        # Extract the authorization code from the redirect URL
        from urllib.parse import urlparse, parse_qs

        query_params = parse_qs(urlparse(redirect_url_with_code).query)
        auth_code = query_params.get("code", [None])[0]

        if not auth_code:
            print("Could not find 'code' in the redirect URL. Aborting.")
            return

        # Exchange authorization code for an access token
        token_url = auth_config.auth_scheme.flows.authorizationCode.tokenUrl
        token_data = {
            "code": auth_code,
            "client_id": client_id,
            "client_secret": auth_config.raw_auth_credential.oauth2.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        self._auth_response = _MockAuthResponse(
            oauth2=_MockOAuth2AuthResponse(
                access_token=token_json["access_token"],
                refresh_token=token_json.get("refresh_token"),
            )
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mock_context = MockToolContext()

    # First call will likely trigger the auth flow
    result = test_get_user_address(mock_context)
    print(f"\nInitial call result:\n{result}")

    # If the first call required auth, the context now has a token.
    # A second call should succeed using the cached credentials.
    if "authorize me" in result:
        print("\n--- RETRYING WITH NEW CREDENTIALS ---")
        second_result = test_get_user_address(mock_context)
        print(f"\nSecond call result:\n{second_result}")
