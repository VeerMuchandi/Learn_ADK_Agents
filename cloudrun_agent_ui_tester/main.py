import os
import json
from flask import Flask, request, jsonify, redirect, session, url_for
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

# The URL of the deployed agent
DEFAULT_AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000")
print(f"Using default agent URL: {DEFAULT_AGENT_URL}")

def initialize_app_name(agent_url):
    """Gets the app name from the /list-apps endpoint."""
    print(f"Initializing app name for {agent_url}...")
    try:
        print(f"Calling {agent_url}/list-apps")
        response = requests.get(f'{agent_url}/list-apps')
        response.raise_for_status()
        app_names = response.json()
        if app_names:
            app_name = app_names[0]
            session['app_name'] = app_name
            print(f"Successfully fetched app name: {app_name}")
            return app_name
        else:
            print("No app names found.")
            session.pop('app_name', None)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting app name: {e}.")
        session.pop('app_name', None)
        return None

@app.route('/')
def index():
    """Renders the chat interface."""
    initialize_app_name(DEFAULT_AGENT_URL)
    with open("templates/index.html") as f:
        return f.read()

@app.route('/initialize-app-name', methods=['POST'])
def initialize_app_name_endpoint():
    agent_url = request.json.get('agent_url', DEFAULT_AGENT_URL)
    app_name = initialize_app_name(agent_url)
    return jsonify({'app_name': app_name})

@app.route('/agent-url')
def get_agent_url():
    return jsonify({'agent_url': DEFAULT_AGENT_URL})

@app.route('/session', methods=['GET', 'POST', 'DELETE'])
def session_manager():
    if request.method == 'GET':
        return jsonify({'session_id': session.get('session_id')})
    
    agent_url = request.json.get('agent_url', DEFAULT_AGENT_URL)
    app_name = session.get('app_name')
    if not app_name:
        return jsonify({'error': 'App name not found in session. Please initialize the app name.'}), 400
    if request.method == 'POST':
        headers = {'Content-Type': 'application/json'}
        session_url = f'{agent_url}/apps/{app_name}/users/user/sessions'
        response = requests.post(session_url, headers=headers)
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data['id']
        session['session_id'] = session_id
        return jsonify({'session_id': session_id})
    elif request.method == 'DELETE':
        session.pop('session_id', None)
        return jsonify({'status': 'ok'})

@app.route('/chat', methods=['POST'])
def chat():
    """Receives a message from the user, forwards it to the agent, and returns the response."""
    user_message = request.json.get('message')
    auth_code = request.json.get('auth_code')
    state = request.json.get('state')
    agent_url = request.json.get('agent_url', DEFAULT_AGENT_URL)
    app_name = session.get('app_name')
    if not app_name:
        return jsonify({'error': 'App name not found in session. Please initialize the app name.'}), 400

    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({'error': 'No active session. Please create a new session.'}), 400

        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://127.0.0.1:8080',
            'Referer': 'http://127.0.0.1:8080/',
            'Accept': 'text/event-stream',
        }

        if auth_code:
            print(f"Auth code received: {auth_code}")
            auth_config = session.get('auth_config')
            function_call_id = session.get('function_call_id')
            if not auth_config or not function_call_id:
                return jsonify({'error': 'Auth config or function call ID not found in session.'}), 500

            auth_config['exchangedAuthCredential']['oauth2']['authResponseUri'] = f"http://127.0.0.1:8080/oauth_callback?state={state}&code={auth_code}"

            data = {
                "appName": app_name,
                "userId": "user",
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "id": function_call_id,
                            "name": "adk_request_credential",
                            "response": auth_config
                        }
                    }]
                }
            }
        else:
            data = {
                "appName": app_name,
                "userId": "user",
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [
                        {
                            "text": user_message
                        }
                    ]
                },
                "stateDelta": None,
                "streaming": False
            }

        run_sse_url = f'{agent_url}/run_sse'

        print(f"--- Chat Request ---\nURL: {run_sse_url}\nHeaders: {headers}\nBody: {json.dumps(data, indent=2)}\n--------------------------")
        response = requests.post(run_sse_url, headers=headers, json=data, stream=True)
        print(f"--- Chat Response ---\nStatus Code: {response.status_code}\nHeaders: {response.headers}\n--------------------------")
        response.raise_for_status()

        auth_config_to_store = None
        function_call_id_to_store = None
        auth_uri_to_return = None
        text_response = None

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"SSE Data: {decoded_line}")
                if decoded_line.startswith('data:'):
                    data_str = decoded_line[5:]
                    try:
                        data = json.loads(data_str)

                        if data.get('actions') and data['actions'].get('requestedAuthConfigs'):
                            for tool_id, auth_config in data['actions']['requestedAuthConfigs'].items():
                                auth_uri = auth_config.get('exchangedAuthCredential', {}).get('oauth2', {}).get('authUri')
                                if auth_uri:
                                    auth_config_to_store = auth_config
                                    auth_uri_to_return = auth_uri

                        if data.get('content') and data.get('content').get('parts'):
                            for part in data['content']['parts']:
                                if part.get('functionCall', {}).get('name') == 'adk_request_credential':
                                    function_call_id_to_store = part['functionCall']['id']
                                if part.get('text'):
                                    text_response = part['text']

                    except json.JSONDecodeError:
                        print(f"JSONDecodeError: {data_str}")
                        return jsonify({'response': data_str})

        if auth_uri_to_return:
            session['auth_config'] = auth_config_to_store
            session['function_call_id'] = function_call_id_to_store
            return jsonify({'authorization_url': auth_uri_to_return})
        
        if text_response:
            return jsonify({'response': text_response})

        print("No answer event received from the agent.")
        return jsonify({'error': 'No answer from the agent.'})


    except requests.exceptions.RequestException as e:
        print(f"RequestException during run_sse call: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/oauth_callback')
def oauth_callback():
    """Handles the callback from the OAuth2 authorization server."""
    print("OAuth Callback function called.")
    auth_code = request.args.get('code')
    state = request.args.get('state')
    if auth_code:
        print(f"Auth code received: {auth_code}")
        # Render a small HTML page that closes the popup and triggers the opener.
        return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Complete</title>
    <script type="text/javascript">
        window.onload = function() {{
            if (window.opener) {{
                window.opener.postMessage({{ 'auth_code': '{auth_code}', 'state': '{state}' }}, window.opener.location.origin);
                window.close();
            }} else {{
                // Fallback if not opened as a popup
                window.location.href = '/';
            }}
        }};
    </script>
</head>
<body>
    <p>Authentication complete. You can close this window.</p>
</body>
</html>
'''
    else:
        print("Error: No authorization code received in callback.")
        return "Error: No authorization code received."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)