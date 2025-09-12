# app.py
import os
import uuid
import json
import vertexai
import time
import google.auth
from dotenv import load_dotenv
from google.adk.auth import AuthConfig
from vertexai.agent_engines import _utils
from flask import Flask, request, render_template, jsonify, session
from vertexai import agent_engines

# Load environment variables from .env file
load_dotenv()

# --- IMPORTANT: Replace with your actual project details ---
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

def get_project_number():
    """Retrieves the project number from the active Google Cloud credentials."""
    try:
        credentials, project_id = google.auth.default()
        return credentials.quota_project_id
    except Exception as e:
        print(f"Error getting project number: {e}")
        return None

# Get the Project Number
PROJECT_NUMBER = get_project_number()

# Initialize the Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=LOCATION)


# Load the deployed agent
try:
    print(f"Loading agent engine: {AGENT_ENGINE_ID}")
    # The class to interact with a deployed agent is ReasoningEngine
    remote_agent = agent_engines.get(AGENT_ENGINE_ID)
    print("Agent loaded successfully.")
    print(" Supported Operations \n" + json.dumps(
        remote_agent.operation_schemas(), indent=2
    ))
except Exception as e:
    print(f"Error loading agent: {e}")
    remote_agent = None

app = Flask(__name__)

app.secret_key = SECRET_KEY

@app.route('/')
def index():
    """Renders the main HTML page for the frontend."""
    # Create a unique session ID for the user if it doesn't exist
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/query_agent', methods=['POST'])
def query_agent():
    """Receives a user query and sends it to the agent."""
    if remote_agent is None:
        return jsonify({"error": "Agent is not loaded."}), 500

    user_query = request.json.get('query')
    if not user_query:
        return jsonify({"error": "No query provided."}), 400

    session_id = session.get('session_id')
    if not session_id:
        return jsonify({"error": "Session ID not found."}), 500

    try:
        # Use stream_query to handle responses as a stream, providing the
        # required 'message' and 'user_id' arguments.
        response_stream = remote_agent.stream_query(
            message=user_query, user_id=session_id)

        # The stream can yield various types of chunks (text, tool calls, etc.).
        # We need to iterate through them and find the final answer chunk,
        # which is typically a dictionary containing the 'output'.
        final_answer = None
        for chunk in response_stream:
            if isinstance(chunk, dict) and ("output" in chunk or "answer" in chunk):
                final_answer = chunk.get("output") or chunk.get("answer")

        if final_answer is None:
            return jsonify({"error": "No final answer found in agent response stream."}), 500

        # The final answer should already be a dictionary if it's JSON.
        if isinstance(final_answer, dict):
            output_dict = final_answer
        else:
            # Use dump_event_for_json to handle complex ADK objects
            if isinstance(final_answer, AuthConfig):
                output_dict = _utils.dump_event_for_json(final_answer)
            else:
                output_dict = json.loads(final_answer)
        # Check if the agent returned an auth_url. If so, send it back
        # directly, as the frontend is specifically looking for this key.
        if "auth_url" in output_dict:
            json_response = jsonify(output_dict)
            print(f"Sending auth response to frontend: {json_response.get_data(as_text=True)}")
            return json_response, 200

        # Otherwise, package the final answer into the consistent
        # {"response": "..."} structure that the frontend expects.
        json_response = jsonify({"response": output_dict.get("output") or output_dict.get("answer")})
        print(f"Sending final response to frontend: {json_response.get_data(as_text=True)}")
        return json_response, 200

    except Exception as e:
        print(f"!!! Exception in outer try/except block: {e}")
        return jsonify({"error": f"Error during agent query: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)