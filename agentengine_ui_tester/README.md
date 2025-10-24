# Agent Engine UI Tester

This document provides a guide on how to use and understand the Agent Engine UI Tester application, a Flask-based web application for interacting with ADK agents and testing the OAuth2 flow.

## Overview

The Agent Engine UI Tester is a simple web application that provides a chat interface for interacting with a deployed Reasoning Engine. It demonstrates how a custom application can authenticate with a Reasoning Engine and handle the user-centric OAuth2 flow required by agents that use tools protected by OAuth.

## How to Run the Application

### 1. Install Dependencies

Install the necessary Python packages using pip:

```bash
pip install -r requirements.txt
```

### 2. Configure the Environment

Create a `.env` file in the `agentengine_ui_tester` directory and add the following line:

```
DEFAULT_AGENT_URL=<your_agent_url>
```

Replace `<your_agent_url>` with the URL of your deployed Reasoning Engine.

### 3. Run the Application

Start the Flask web server:

```bash
python main.py
```

The application will be available at `http://127.0.0.1:8080`.

## How it Works

The application consists of a simple HTML frontend and a Flask backend that communicates with the Reasoning Engine. The backend handles session management, authentication, and the OAuth2 flow.

### Authentication and OAuth2 Flow

The application demonstrates the following flow to authenticate with the agent and authorize access to protected tools:

1.  **Session Creation:** The user creates a session with the agent.
2.  **Initial Chat:** The user sends a message to the agent.
3.  **OAuth Trigger:** If the agent needs to use a tool that requires authentication, it responds with a request for credentials, including an `authUri`.
4.  **User Authentication:** The frontend opens the `authUri` in a popup window, where the user can sign in and grant consent.
5.  **OAuth Callback:** After authentication, the user is redirected to the `/oauth_callback` endpoint, which captures the authorization code.
6.  **Code Exchange:** The frontend sends the authorization code back to the backend, which then sends it to the agent to complete the authentication process.

### Example Agent Backend Calls

Here is an example of the requests and responses exchanged between the Agent Engine UI Tester and the Reasoning Engine during the OAuth2 flow.

**Initial Chat Request**

The user sends a message to the agent.

```
--- Chat Request (Initial) ---
URL: https://us-central1-aiplatform.googleapis.com/v1/projects/muchandi-proj1/locations/us-central1/reasoningEngines/3292892189654253568:streamQuery?alt=sse
Headers: {"Content-Type": "application/json", "Authorization": "Bearer <masked>", "Connection": "close"}
Body: {
  "class_method": "async_stream_query",
  "input": {
    "user_id": "user-from-custom-ae-tester",
    "session_id": "1200381099386077184",
    "message": {
      "role": "user",
      "parts": [
        {
          "text": "route from atlanta ga to apex nc by car"
        }
      ]
    }
  }
}
--------------------------
```

**Agent Response with Auth URI**

The agent responds with a request for credentials, including the `authUri`.

```
SSE Data: {"content": {"parts": [{"function_call": {"id": "adk-0478ad02-ed00-4416-b932-d6ed032c62ae", "args": {"functionCallId": "adk-a1431b9b-1951-4639-8db8-1c20145f989c", "authConfig": {"authScheme": {"type": "oauth2", "flows": {"authorizationCode": {"scopes": {"https://www.googleapis.com/auth/cloud-platform": "", "https://www.googleapis.com/auth/user.addresses.read": "", "https://www.googleapis.com/auth/userinfo.profile": ""}}, "authorizationUrl": "https://accounts.google.com/o/oauth2/auth", "tokenUrl": "https://oauth2.googleapis.com/token"}}}, "rawAuthCredential": {"authType": "oauth2", "oauth2": {"clientId": "796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com", "clientSecret": "<masked>", "redirectUri": "http://127.0.0.1:8080/oauth_callback"}}, "exchangedAuthCredential": {"authType": "oauth2", "oauth2": {"clientId": "796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com", "clientSecret": "<masked>", "authUri": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2Foauth_callback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuser.addresses.read+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile&state=MIIfNCOI9CfkaFVSJIhLsiPDUSXiDg&access_type=offline&prompt=consent", "state": "MIIfNCOI9CfkaFVSJIhLsiPDUSXiDg", "redirectUri": "http://127.0.0.1:8080/oauth_callback"}}, "credentialKey": "adk_oauth2_3119459921658935125_oauth2_-568389594588614771"}}, "name": "adk_request_credential"}], "role": "user"}, "invocation_id": "e-43128e19-237f-4c0e-8fef-b50d0f09e717", "author": "route_planning_agent", "actions": {"state_delta": {}, "artifact_delta": {}, "requested_auth_configs": {}, "requested_tool_confirmations": {}}, "long_running_tool_ids": ["adk-0478ad02-ed00-4416-b932-d6ed032c62ae"], "id": "773f0f85-821b-4e52-8af6-0e361b34fe00", "timestamp": 1761321818.405722}
```

**Chat Request with Auth Code**

After the user authenticates, the authorization code is sent back to the agent.

```
--- Chat Request (Auth Code) ---
URL: https://us-central1-aiplatform.googleapis.com/v1/projects/muchandi-proj1/locations/us-central1/reasoningEngines/3292892189654253568:streamQuery?alt=sse
Headers: {"Content-Type": "application/json", "Authorization": "Bearer <masked>", "Connection": "close"}
Body: {
  "class_method": "async_stream_query",
  "input": {
    "user_id": "user-from-custom-ae-tester",
    "session_id": "1200381099386077184",
    "message": {
      "role": "user",
      "parts": [
        {
          "function_response": {
            "name": "adk_request_credential",
            "id": "adk-0478ad02-ed00-4416-b932-d6ed032c62ae",
            "response": {
              "authScheme": {
                "flows": {
                  "authorizationCode": {
                    "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                    "scopes": {
                      "https://www.googleapis.com/auth/cloud-platform": "",
                      "https://www.googleapis.com/auth/user.addresses.read": "",
                      "https://www.googleapis.com/auth/userinfo.profile": ""
                    },
                    "tokenUrl": "https://oauth2.googleapis.com/token"
                  }
                },
                "type": "oauth2"
              },
              "credentialKey": "adk_oauth2_3119459921658935125_oauth2_-568389594588614771",
              "exchangedAuthCredential": {
                "authType": "oauth2",
                "oauth2": {
                  "authUri": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2Foauth_callback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuser.addresses.read+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile&state=MIIfNCOI9CfkaFVSJIhLsiPDUSXiDg&access_type=offline&prompt=consent",
                  "clientId": "796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com",
                  "clientSecret": "<masked>",
                  "redirectUri": "http://127.0.0.1:8080/oauth_callback",
                  "state": "MIIfNCOI9CfkaFVSJIhLsiPDUSXiDg",
                  "authResponseUri": "http://127.0.0.1:8080/oauth_callback?state=MIIfNCOI9CfkaFVSJIhLsiPDUSXiDg&code=4/0Ab32j91pWYx_s-7rOrfXoqLTQQYJ0cp-c_cw-3Co7_JGG2nYHBgs6TbLvILanrdEr96BUg"
                }
              },
              "rawAuthCredential": {
                "authType": "oauth2",
                "oauth2": {
                  "clientId": "796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com",
                  "clientSecret": "<masked>",
                  "redirectUri": "http://127.0.0.1:8080/oauth_callback"
                }
              }
            }
          }
        }
      ]
    }
  }
}
--------------------------
```

**Final Agent Response**

The agent uses the authorization code to obtain an access token, executes the tool, and returns the final response.

```
Auth Code Stream Data: {"content": {"parts": [{"function_response": {"id": "adk-a1431b9b-1951-4639-8db8-1c20145f989c", "name": "get_directions", "response": {"result": "Directions from 'atlanta ga' to 'apex nc' by drive:\n  - Total Distance: 635.2 km\n  - Estimated Duration: about 362 minutes.\n  - Steps:\n    1. Head southwest toward Capitol Sq SW\n    2. Turn left onto Capitol Sq SW\n    3. Turn left onto Capitol Ave SW\n    4. Turn right onto M.L.K. Jr Dr SE\n    5. Turn left to merge onto I-75 N/I-85 N\n    6. Take exit 251B on the left for I-85 N toward GA-400/Greenville\n    7. Continue onto I-85 N\n    8. Keep right to stay on I-85 N, follow signs for Greenville\nEntering South Carolina\n    9. Continue straight to stay on I-85 N\nEntering North Carolina\n    10. Take exit 30 for I-485 toward I-77/Pineville/Huntersville\n    11. Take the I-485 Inner N ramp to I-77 N/Statesville\n    12. Merge onto I-485/I-485 Inner\n    13. Take exit 30 to merge onto I-85 N toward Greensboro\n    14. Keep left to stay on I-85 N, follow signs for US 421 S/Durham Sanford\n    15. Take exit 126A-126B to merge onto US-421 S toward Sanford\n    16. Slight right\n    17. Merge onto US-421 S\n    18. Take exit 171 for US-64 E toward Pittsboro\n    19. Turn left onto US-64 E\nPass by Wendy's (on the right in 0.4 mi)\n    20. Take the exit toward Apex/Downtown\n    21. Turn right onto N Salem St\n    22. Continue straight to stay on N Salem St"}}}], "role": "user"}, "invocation_id": "e-fb1e8cda-73ed-4a70-8a7c-b25dacaf11bf", "author": "route_planning_agent", "actions": {"state_delta": {"route_planner_creds": "{\"token\": \"<masked>\", \"refresh_token\": \"<masked>\", \"token_uri\": \"https://oauth2.googleapis.com/token\", \"client_id\": \"796714221495-6j24hddcq4a5h59ish09k1f3knet2ou9.apps.googleusercontent.com\", \"client_secret\": \"<masked>\", \"universe_domain\": \"googleapis.com\", \"account\": \""}"}, "artifact_delta": {}, "requested_auth_configs": {}, "requested_tool_confirmations": {}}, "id": "a66f97e7-6565-4af3-b5d2-8d2e7602997f", "timestamp": 1761321844.451273}
```

## API Endpoints

-   `GET /`: Renders the main chat interface.
-   `GET /agent-url`: Returns the configured agent URL.
-   `GET /list-agents`: Lists available Reasoning Engines.
-   `GET /session`: Returns the current session ID.
-   `POST /session`: Creates a new session.
-   `DELETE /session`: Deletes the current session.
-   `POST /chat`: Handles the chat logic and OAuth flow.
-   `GET /oauth_callback`: Handles the OAuth2 callback.