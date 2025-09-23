import os
from dotenv import load_dotenv

import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

from route_planner_agent.agent import root_agent

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = "us-central1"

# The GCS_BUCKET should be a unique bucket name, often based on the project ID.
if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT_ID environment variable not set.")
GCS_BUCKET = f"gs://{PROJECT_ID}-adk-staging"
GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET")
AGENT_REDIRECT_URI=os.getenv("AGENT_REDIRECT_URI")

# --- Initialize Vertex AI ---
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=GCS_BUCKET,
)

# --- Create ADK App for Deployment ---
# The AdkApp class wraps your ADK agent, making it deployable to Agent Engine.
adk_app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# --- Define Deployment Dependencies ---
# These are the Python packages your agent needs to run in the cloud.
requirements = [
    "google-adk",
    "google-cloud-aiplatform[reasoning_engine]",
    "google-auth-oauthlib",
    "requests",
    "python-dotenv",
]

# --- Deploy to Agent Engine ---
print(f"Deploying 'Route Planner Agent' to Project: {PROJECT_ID}, Location: {LOCATION}")
print(f"Using Staging Bucket: {GCS_BUCKET}")

env_vars = {
  "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
  "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
  "AGENT_REDIRECT_URI": AGENT_REDIRECT_URI,
}

# The `create` function packages your code and dependencies,
# and deploys them as a new Agent Engine.
deployed_engine = agent_engines.create(
    agent_engine=adk_app,
    display_name="Route Planner Agent",
    description="An agent that can plan routes using Google Maps with user authentication.",
    requirements=requirements,
    extra_packages=["route_planner_agent", "./route_planner_agent/google_genai-1.38.0-py3-none-any.whl"],
    env_vars=env_vars, # Package the entire agent directory
)

print(f"\nSuccessfully deployed Agent Engine!")
print(f"Resource Name: {deployed_engine.resource_name}")
