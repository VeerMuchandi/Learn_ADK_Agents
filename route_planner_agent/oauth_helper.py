# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A helper module for handling user-centric OAuth 2.0 flow within ADK tools."""

import json
import logging
from typing import List, Optional

from google.adk.auth import AuthConfig, AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools import ToolContext
from google.auth import exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows


def get_user_credentials(
    tool_context: ToolContext,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scopes: List[str],
    credential_cache_key: str,
) -> Optional[Credentials]:
  """
  Handles the OAuth 2.0 flow to get valid user credentials.

  This function checks for cached credentials, refreshes them if necessary,
  and initiates a new OAuth flow if no valid credentials are found.

  NOTE TO LEARNERS: This function is written from the perspective of an
  application seeking valid credentials in the most efficient way possible.
  It checks for credentials in the following order:
  1. Valid cached credentials.
  2. Expired credentials that can be refreshed.
  3. A pending authorization response from the user having been redirected back.
  4. Finally, initiating a new authorization request.
  To understand the beginning of the user-facing flow, start by looking at
  step #5 (`tool_context.request_credential`), which is where the user is
  prompted to log in and grant consent.

  Args:
      tool_context: The context of the tool run, provided by the ADK.
      client_id: The OAuth client ID.
      client_secret: The OAuth client secret.
      redirect_uri: The redirect URI for the OAuth flow.
      scopes: A list of required OAuth scopes.
      credential_cache_key: The key to use for caching credentials in the
        session state.

  Returns:
      A valid `google.oauth2.credentials.Credentials` object if authentication
      is successful, or `None` if the authentication flow has been initiated
      and is pending user action.
  """
  # 1. Define the authentication configuration for the tool.
  auth_config = AuthConfig(
      auth_scheme=OAuth2(
          flows=OAuthFlows(
              authorizationCode=OAuthFlowAuthorizationCode(
                  authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                  tokenUrl="https://oauth2.googleapis.com/token",
                  scopes={scope: "" for scope in scopes},
              )
          )
      ),
      raw_auth_credential=AuthCredential(
          auth_type=AuthCredentialTypes.OAUTH2,
          oauth2=OAuth2Auth(
              client_id=client_id,
              client_secret=client_secret,
              redirect_uri=redirect_uri,
          ),
      ),
  )

  # 2. Check for an existing credential in the session state.
  creds_json = tool_context.state.get(credential_cache_key)
  creds = (
      Credentials.from_authorized_user_info(json.loads(creds_json))
      if creds_json
      else None
  )

  # 3. If we have credentials, check if they are still valid or need refreshing.
  if creds and not creds.valid and creds.refresh_token:
    logging.info("Refreshing expired credentials.")
    try:
      # The google-auth library's refresh method will use a new
      # `google.auth.transport.requests.Request` object to make the HTTP call.
      creds.refresh(Request())
      tool_context.state[credential_cache_key] = creds.to_json()
    except exceptions.RefreshError as e:
      logging.warning("Token refresh failed: %s. Requesting new credentials.", e)
      creds = None  # Force re-authentication
      del tool_context.state[credential_cache_key]

  # 4. If we still don't have valid credentials, check for an auth response.
  if not creds or not creds.valid:
    # The ADK abstracts the OAuth 2.0 flow. `get_auth_response` checks
    # if the user has been redirected back from the authorization server with
    # an authorization code. If so, the ADK automatically exchanges the code
    # for an access token and returns the token response.
    auth_response = tool_context.get_auth_response(auth_config)
    if auth_response:
      logging.info("Received new auth response. Fetching token.")
      # Create a `Credentials` object using the tokens from the auth response.
      # This object can then be used to make authenticated API calls.
      creds = Credentials(
          token=auth_response.oauth2.access_token,
          refresh_token=auth_response.oauth2.refresh_token,
          token_uri=auth_config.auth_scheme.flows.authorizationCode.tokenUrl,
          client_id=client_id,
          client_secret=client_secret,
          scopes=scopes,
      )
      # Cache the new credentials in the session state for future use.
      tool_context.state[credential_cache_key] = creds.to_json()
    else:
      # 5. If no valid credentials could be found or refreshed, and there is no
      #    pending authorization response, this is the final step.
      #    `request_credential` initiates the OAuth 2.0 authorization code flow,
      #    prompting the user to log in and grant consent via the provider's UI.
      logging.info("No valid credentials. Requesting user authentication.")
      tool_context.request_credential(auth_config)
      return None

  return creds
