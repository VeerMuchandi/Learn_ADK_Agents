"""This module defines tools for authenticating and interacting with the Discovery Engine API."""
from google.adk.tools import tool_context as tool_context_lib
import google.auth.transport.requests
import requests
import json


ToolContext = tool_context_lib.ToolContext
default = auth.default

import dotenv
import os

dotenv.load_dotenv(override=True)

# Google Cloud project and location details, loaded from environment variables.
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ENGINE_ID = os.getenv("ENGINE_ID")

# API version and endpoint configuration for the Discovery Engine API.
VERSION = "v1alpha" # [v1alpha, v1beta, v1]
ENDPOINT = f"https://discoveryengine.googleapis.com/{VERSION}"
if LOCATION != "global":
  ENDPOINT = f"https://{LOCATION}-discoveryengine.googleapis.com/{VERSION}"

# Construct the full resource name for the assistant.
ASSISTANT_NAME = (
    f'projects/{PROJECT}/locations/{LOCATION}/collections/'
    f'default_collection/engines/{ENGINE_ID}/assistants/'
    f'default_assistant'
)


def authenticate_user(tool_context: ToolContext, key: str = "token"):  # pylint: disable=redefined-outer-name
  """Authenticates the user and updates the token in the state memory.

  This function uses the default application credentials to authenticate,
  refreshes the token to ensure it's valid, and then stores the access
  token in the tool's state for subsequent API calls.

  Args:
      tool_context (ToolContext): The context object for the current tool call,
        which provides access to state.
      key (str, optional): The key under which to store the token in the state.
        Defaults to "token".
  """
  creds, _ = default()
  auth_req = google.auth.transport.requests.Request()
  creds.refresh(auth_req)
  update_state(creds.token, tool_context, key=key)


def update_state(value: str, tool_context: ToolContext, key: str = "token") -> str:  # pylint: disable=redefined-outer-name
  """Updates the current key / value pair in the state memory.

  Args:
      key (str): The key to update.
      value (str): The value to update.
      tool_context (ToolContext): The tool context containing the state of the
          tool.

  Returns:
      str: The updated value.
  """
  tool_context.state[key] = value
  return value


def get_state(tool_context: ToolContext, key: str = "token") -> str:  # pylint: disable=redefined-outer-name
  """Gets the current key / value pair in the state memory.

  Args:
      key (str): The key to retrieve.
      tool_context (ToolContext): The tool context containing the state of the
          tool.

  Returns:
      str: The value associated with the key, or None if not found.
  """
  return tool_context.state.get(key, None)


def get_answer_results(query: str, token: str) -> str:
  """Calls the Discovery Engine's streamAssist API to get an answer for a query.

  Args:
      query (str): The user's query.
      token (str): The authentication token.

  Returns:
      str: The JSON response from the API as a string.

  Raises:
      requests.exceptions.HTTPError: If the API call returns a non-2xx status.
  """
  # The endpoint for the streamAssist API.
  response = requests.post(
      f"{ENDPOINT}/{ASSISTANT_NAME}:streamAssist",
      headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": f"{PROJECT}"
        },
        # The request payload.
        data=json.dumps({
            "query": {
              "text": query
            },
            "assistSkippingMode": "REQUEST_ASSIST",
            "answerGenerationMode": "NORMAL"
        })
    )
  # Log the API call details for debugging.
  print(f"API Call type: ASSIST, Status:Processing, Query:{query}")
  response.raise_for_status()  # Raise an HTTPError for bad responses
  return response.json()


if __name__ == "__main__":
  # Example of how to use the functions directly for testing.
  credentials, _ = default()
  credentials.refresh(google.auth.transport.requests.Request())
  print(
      get_answer_results(
          "what is agentspace?", credentials.token
      )
  )