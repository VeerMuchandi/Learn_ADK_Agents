import os
import json
import subprocess
import sys
from flask import Flask, request, jsonify, session, render_template_string
import requests
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv

# Load environment variables from a .env file.
load_dotenv()

app = Flask(__name__)
# Secret key for session management.
app.secret_key = os.urandom(24)

# The URL of the deployed agent, loaded from the environment.
DEFAULT_AGENT_URL = os.getenv("DEFAULT_AGENT_URL")

def get_auth_headers():
    """
    Generates Google Cloud authentication headers.

    This function uses the default application credentials to obtain an OAuth 2.0 access token, which is then included in the returned headers. This is necessary for authenticating requests to the Reasoning Engine.

    Returns:
        dict: A dictionary containing the 'Content-Type', 'Authorization', and 'Connection' headers.
    """
    credentials, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.token}',
        'Connection': 'close'
    }

@app.route('/')
def index():
    """
    Renders the main chat interface.

    Returns:
        str: The HTML content of the chat interface.
    """
    with open("templates/index.html") as f:
        return f.read()

@app.route('/agent-url')
def get_agent_url():
    """
    Returns the configured agent URL.

    This allows the frontend to know which agent to communicate with.

    Returns:
        Response: A JSON response containing the agent URL.
    """
    return jsonify({'agent_url': DEFAULT_AGENT_URL})

@app.route('/list-agents')
def list_agents():
    """
    Lists available Reasoning Engines in the user's Google Cloud project.

    This function uses the gcloud CLI to fetch the list of agents. The user must have the gcloud CLI installed and authenticated for this to work.

    Returns:
        Response: A JSON response containing a list of agents, or an error if the command fails.
    """
    try:
        # Ensure you have the gcloud CLI installed and authenticated
        command = ["gcloud", "alpha", "reasoning-engines", "list", "--format=json"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        agents = json.loads(result.stdout)
        return jsonify(agents)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return jsonify({"error": f"Failed to list agents. Make sure gcloud CLI is installed and authenticated. Error: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse gcloud output: {str(e)}"}), 500

@app.route('/session', methods=['GET', 'POST', 'DELETE'])
def session_manager():
    """
    Manages the user's session with the agent.

    - GET: Returns the current session ID.
    - POST: Creates a new session with the agent.
    - DELETE: Clears the current session.

    Returns:
        Response: A JSON response containing the session ID or a status message.
    """
    if request.method == 'GET':
        return jsonify({'session_id': session.get('session_id')})

    if request.method == 'DELETE':
        session.pop('session_id', None)
        session.pop('appName', None)
        return jsonify({'status': 'ok'})

    # POST method for creating a session
    if session.get('session_id'):
        return jsonify({'session_id': session.get('session_id')})

    agent_url = request.json.get('agent_url')
    if not agent_url:
        return jsonify({'error': 'agent_url is required to create a session'}), 400

    headers = get_auth_headers()
    user_id = "user-from-agentengine-ui-tester"
    session_url = f'{agent_url}:query'
    create_data = {
        "class_method": "create_session",
        "input": {"user_id": user_id}
    }
    try:
        with requests.Session() as s:
            response = s.post(session_url, headers=headers, json=create_data, timeout=60)
            response.raise_for_status()
            session_data = response.json()
            session['session_id'] = session_data['output']['id']
            return jsonify({'session_id': session['session_id']})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Failed to create session: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles the main chat logic, including the OAuth 2.0 flow.

    This function is the core of the application. It receives messages from the user, sends them to the agent, and processes the agent's response.

    The chat flow is as follows:
    1.  The user sends a message.
    2.  The message is sent to the agent's `async_stream_query` method.
    3.  The agent's response is parsed as a stream of Server-Sent Events (SSE).
    4.  If the agent requires authentication, it will return a function call to `adk_request_credential` with an `authUri`.
    5.  The `authUri` is sent back to the frontend, which opens a popup window for the user to sign in.
    6.  After the user signs in, they are redirected to the `/oauth_callback` endpoint, which captures the authorization code.
    7.  The frontend sends the authorization code back to this `/chat` endpoint.
    8.  The authorization code is sent back to the agent in a `function_response` to complete the OAuth flow.
    9.  The agent processes the request and returns the final response.

    Returns:
        Response: A JSON response containing either the agent's text response, an authorization URL, or an error message.
    """
    if 'session_id' not in session:
        return jsonify({'error': 'No active session. Please create a session first.'}), 400

    req_data = request.json
    agent_url = req_data.get('agent_url', DEFAULT_AGENT_URL)
    user_id = "user-from-agentengine-ui-tester"
    session_id = session['session_id']
    headers = get_auth_headers()

    # This branch handles the initial user message and the start of the OAuth flow.
    if 'message' in req_data:
        # Prepare the payload for the agent's `async_stream_query` method.
        payload_input = {
            "user_id": user_id,
            "session_id": session_id,
            "message": {
                "role": "user",
                "parts": [
                    {
                        "text": req_data['message']
                    }
                ]
            }
        }
        data = {"class_method": "async_stream_query", "input": payload_input}
        run_sse_url = f'{agent_url}:streamQuery?alt=sse'
        
        auth_config_to_store = None
        function_call_id_to_store = None
        auth_uri_to_return = None
        text_response = ""

        print(f"--- Chat Request (Initial) ---\nURL: {run_sse_url}\nHeaders: {headers}\nBody: {json.dumps(data, indent=2)}\n--------------------------")
        # Make a streaming request to the agent.
        with requests.Session() as s:
            response = s.post(run_sse_url, headers=headers, json=data, stream=True, timeout=60)
            print(f"--- Chat Response (Initial) ---\nStatus Code: {response.status_code}\nHeaders: {response.headers}\n--------------------------")
            response.raise_for_status()
            
            # Process the SSE stream from the agent.
            decoder = json.JSONDecoder()
            buffer = ""
            for chunk in response.iter_content(chunk_size=None):
                buffer += chunk.decode('utf-8')
                while buffer:
                    try:
                        sse_data, index = decoder.raw_decode(buffer)
                        print(f"SSE Data: {json.dumps(sse_data)}")
                        # Extract text and function calls from the agent's response.
                        for part in sse_data.get("content", {}).get("parts", []):
                            if part.get('text'):
                                text_response += part['text']
                            
                            # If the agent requests credentials, extract the auth URI and other necessary data.
                            function_call = part.get("function_call")
                            if function_call and function_call.get("name") == "adk_request_credential":
                                function_call_id_to_store = function_call.get("id")
                                args = function_call.get("args", {})
                                auth_config = args.get("authConfig")
                                if auth_config:
                                    auth_uri = auth_config.get("exchangedAuthCredential", {}).get("oauth2", {}).get("authUri")
                                    if auth_uri:
                                        auth_config_to_store = auth_config
                                        auth_uri_to_return = auth_uri
                        buffer = buffer[index:].lstrip()
                    except json.JSONDecodeError:
                        # Not enough data to decode a full JSON object, break and get more
                        break

        # If an authorization URL was found, store the auth config and function call ID in the session and return the URL to the frontend.
        if auth_uri_to_return:
            session['auth_config'] = auth_config_to_store
            session['function_call_id'] = function_call_id_to_store
            return jsonify({'authorization_url': auth_uri_to_return})
        
        # Otherwise, return the agent's text response.
        return jsonify({'response': text_response or "No response text found."})

    # This branch handles the final step of the OAuth flow, where the authorization code is sent to the agent.
    elif 'auth_code' in req_data:
        # Retrieve the auth config and function call ID from the session.
        auth_config = session.get('auth_config')
        function_call_id = session.get('function_call_id')
        if not auth_config or not function_call_id:
            return jsonify({'error': 'Auth config or function call ID not found in session.'}), 500

        # Prepare the payload for the agent with the authorization code.
        auth_code = req_data['auth_code']
        state = req_data.get('state')
        auth_config['exchangedAuthCredential']['oauth2']['authResponseUri'] = f"http://127.0.0.1:8080/oauth_callback?state={state}&code={auth_code}"

        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "message": {
                "role": "user",
                "parts": [{
                    "function_response": {
                        "name": "adk_request_credential",
                        "id": function_call_id,
                        "response": auth_config
                    }
                }]
            }
        }
        data = {"class_method": "async_stream_query", "input": payload}
        run_sse_url = f'{agent_url}:streamQuery?alt=sse'
        final_response_text = ""
        print(f"--- Chat Request (Auth Code) ---\nURL: {run_sse_url}\nHeaders: {headers}\nBody: {json.dumps(data, indent=2)}\n--------------------------")
        # Make a streaming request to the agent to complete the OAuth flow.
        with requests.Session() as s:
            response = s.post(run_sse_url, headers=headers, json=data, stream=True, timeout=60)
            print(f"--- Chat Response (Auth Code) ---\nStatus Code: {response.status_code}\nHeaders: {response.headers}\n--------------------------")
            response.raise_for_status()
            
            # Process the final response from the agent.
            decoder = json.JSONDecoder()
            buffer = ""
            for chunk in response.iter_content(chunk_size=None):
                buffer += chunk.decode('utf-8')
                while buffer:
                    try:
                        sse_data, index = decoder.raw_decode(buffer)
                        print(f"Auth Code Stream Data: {json.dumps(sse_data)}")
                        for part in sse_data.get("content", {}).get("parts", []):
                            if part.get('text'):
                                final_response_text += part['text']
                        buffer = buffer[index:].lstrip()
                    except json.JSONDecodeError:
                        # Not enough data to decode a full JSON object, break and get more
                        break
        return jsonify({'response': final_response_text})

    else:
        return jsonify({'error': 'Request must contain either "message" or "auth_code"'}), 400

@app.route('/oauth_callback')
def oauth_callback():
    """
    Handles the OAuth 2.0 callback from the authorization server.

    This endpoint receives the authorization code and state from the OAuth provider. It then renders a simple HTML page with a script that sends the code and state to the parent window (the main chat interface) via `postMessage`.

    Returns:
        str: The HTML content of the callback page.
    """
    code = request.args.get('code')
    state = request.args.get('state')
    html_content = """
    <!DOCTYPE html><html><head><title>Authentication Complete</title></head><body>
    <p>Authentication successful. Please wait...</p><script>
        window.onload = function() {
            if (window.opener) {
                window.opener.postMessage({ type: 'oauth_complete', auth_code: '{{ code }}', state: '{{ state }}' }, window.opener.location.origin);
                window.close();
            } else { document.body.innerHTML = "<h1>Error: Not in a popup.</h1>"; }
        };
    </script></body></html>
    """
    return render_template_string(html_content, code=code, state=state)

if __name__ == '__main__':
    # Runs the Flask application.
    app.run(host='0.0.0.0', port=8080, debug=True)
