from google import auth
from google.adk.tools import tool_context as tool_context_lib
import google.auth.transport.requests
import requests
import json


ToolContext = tool_context_lib.ToolContext
default = auth.default

import dotenv
import os

dotenv.load_dotenv(override=True)

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
ENGINE_ID = os.getenv("ENGINE_ID")

VERSION = "v1alpha" # [v1alpha, v1beta, v1]
ENDPOINT = f"https://discoveryengine.googleapis.com/{VERSION}"
if LOCATION != "global":
  ENDPOINT = f"https://{LOCATION}-discoveryengine.googleapis.com/{VERSION}"

# Search API call vars
#ENDPOINT = "https://discoveryengine.googleapis.com"
#STAGING_ENDPOINT = "https://staging-discoveryengine-googleapis.sandbox.google.com"
#ANSWER_API = f"{ENDPOINT}/v1alpha/projects/{PROJECT}/locations/global/collections/default_collection/engines/{ENGINE_ID}/servingConfigs/default_search:answer"

ASSISTANT_NAME = (
    f'projects/{PROJECT}/locations/{LOCATION}/collections/'
    f'default_collection/engines/{ENGINE_ID}/assistants/'
    f'default_assistant'
)


def authenticate_user(tool_context: ToolContext, key: str="token"):  # pylint: disable=redefined-outer-name
  """Authenticates the user and updates the token in the state memory."""
  creds, _ = default()
  auth_req = google.auth.transport.requests.Request()
  creds.refresh(auth_req)
  update_state(creds.token, tool_context, key=key)


def update_state(value: str, tool_context: ToolContext, key: str="token") -> str:  # pylint: disable=redefined-outer-name
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


def get_state(tool_context: ToolContext, key: str="token") -> str:  # pylint: disable=redefined-outer-name
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
  """Calls the Agentspace search API to retrieve relevant information.

  Args:
      query (str): The user's query.
      token (str): The authentication token.
  Returns:
      str: The search response from the API.
  """
  
#   response = requests.post(
#       ANSWER_API,
#       headers={
#           "Content-Type": "application/json",
#           "Authorization": "Bearer " + token,
#       },
#       json={
#           "query": {"text": query},
#           "answerGenerationSpec": {"includeCitations": True},
#       },
#   )
#   return response.json()

  response = requests.post(
      f"{ENDPOINT}/{ASSISTANT_NAME}:streamAssist",
      headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": f"{PROJECT}"
        },
        data=json.dumps({
            "query": {
              "text": query
            },
            "assistSkippingMode": "REQUEST_ASSIST",
            "answerGenerationMode": "NORMAL"
        })
    )
  print(f"API Call type: ASSIST, Status:Processing, Query:{query}")
  response.raise_for_status()  # Raise an HTTPError for bad responses
  return response.json()


if __name__ == "__main__":
  credentials, _ = default()
  credentials.refresh(google.auth.transport.requests.Request())
  print(
      get_answer_results(
          "what is agentspace?", credentials.token
      )
  )