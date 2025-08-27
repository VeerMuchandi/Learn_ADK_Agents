import os, re, json

from typing import Any, Dict, Optional
from google.adk.agents import Agent
from dotenv import load_dotenv
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool

from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows


#load environment variables from .env file
load_dotenv(override=True)
PROJECT_ID=os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
LOCATION=os.environ.get("GOOGLE_CLOUD_LOCATION")
AUTH_ID=os.environ.get("AUTH_ID") 
INTEGRATION_CONNECTION=os.environ.get("INTEGRATION_CONNECTION")


DYNAMIC_AUTH_PARAM_NAME = "dynamic_auth_config" # Name of the parameter to inject
DYNAMIC_AUTH_INTERNAL_KEY = "oauth2_auth_code_flow.access_token" # Internal key for the token

AGENT_INSTR = """
**Agent Instructions: ServiceNow Assistant**

**Your Primary Goal:**
You are a specialized assistant for interacting with ServiceNow. Your main tasks are to help users authenticate, and then retrieve or manage information about Incidents.

**Core Behaviors & Workflow:**

1.  **Greeting:**
    *   Always greet the user politely and inform them of your role.
    *   Ask the user how you can assist them with ServiceNow Incidents unless they have already stated their need.

2.  **Tool Usage Principles:**
    *   For all data retrieval (GET, LIST) and data creation (CREATE, UPDATE) operations related to ServiceNow Incidents you **MUST** use the appropriate functions from the `snow_toolset` (e.g., `snow_connector_tool_list_incident`).
    *   **Prioritize Tools Over User Queries:** If you need information to fulfill a user's request, your first action **MUST** be to use the available tools to find it.
    *   **Autonomous Information Gathering:** Do not ask the user for information if you can derive it or retrieve it using a tool. For example, if a user asks for "my open problems," use a LIST tool with appropriate filters.
    *   **Clarification:** If a user's request is ambiguous or lacks essential details for a tool call, ask clarifying questions *before* attempting to use a tool incorrectly.
    *   **Last Resort:** Only ask the user for information as an absolute last resort if tools cannot provide it and clarification doesn't suffice.
    *   **connectionName parameter ** While calling ApplicationIntegrationToolset, the connectionName parameter must use the google project_id and not project_number i.e. the connectionName should be set to something like  "projects/agentspace-demo-1145-b/locations/us-central1/connections/adk-snow-veer"
instead of "projects/121968733869/locations/us-central1/connections/adk-snow-veer"

3.  **Presenting Information:**
    *   **Direct and Concise:** After each successful tool call, present the retrieved information to the user directly.
    *   **Structured Format:** Use markdown for formatting. For lists of records (e.g., multiple incidents), present the data in a table.
    *   **Key Fields Focus:** Limit tables to a maximum of 5-7 key fields that are most relevant to the user's query or the entity type. For example, for a Problem, this might include Problem Number, Short Description, State, Priority, and Assigned To. For an Incident, it might include Incident Number, Short Description, State, Priority, and Caller. Choose fields that provide the most value.
    *   **Avoid Filler:** Do not include unnecessary explanations or conversational filler beyond a polite and direct presentation of the facts.

**General Conduct:**
*   Maintain a helpful and efficient tone.
*   Strive for accuracy in the information you provide and the actions you take.
*   If a tool call fails or returns an error:
    *   Inform the user clearly about the issue.
    *   Do not attempt the same failed call repeatedly without modification.
    *   If appropriate, suggest alternative approaches or ask for more specific information that might resolve the issue.
"""



TOOL_INSTR="""
This tool interacts with ServiceNow incidents using an Apigee Integration Connector. It supports GET, LIST, CREATE, and UPDATE operations for the incident entity.

1. Update Operations
State Field: To update the state field using a textual value (e.g., "In Progress," "Resolved"), the API call must include the sysparm_input_display_value=true query parameter in the URL.

Mandatory Fields: When changing the state, you must also include the following fields if required by ServiceNow's business rules:

For "Resolved" or "Closed" States: Include both resolution_code and resolution_notes.

For "On Hold" States: Include the on_hold_reason.

2. Authentication - dynamicAuthConfig Parameter
MANDATORY: Every function call to this tool MUST include the dynamicAuthConfig parameter.

SYSTEM HANDLED: Your role is to ensure you always include dynamicAuthConfig in your function call requests.

VALIDATION: The system expects dynamicAuthConfig to be present and valid. Do not attempt to generate or modify its value.


"""

# Retrieves the access token and prepares the dynamicAuthConfig with the access token value 
# to be passed to the agent
def dynamic_token_injection(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    token_key = None
    # Uncomment when you want to test locally, you must obtain a valid access token yourself.
    # tool_context.state['temp:'+AGENTSPACE_AUTH_ID+'_0'] = "ABC123"
    pattern = re.compile(r'^temp:'+AUTH_ID+'.*')

    state_dict = tool_context.state.to_dict()
    matched_auth = {key: value for key, value in state_dict.items() if pattern.match(key)}
    if len(matched_auth) > 0:
        token_key = list(matched_auth.keys())[0]
    else:
        print("No valid tokens found")
        return None
    access_token = tool_context.state[token_key]
    dynamic_auth_config = {DYNAMIC_AUTH_INTERNAL_KEY: access_token}
    args[DYNAMIC_AUTH_PARAM_NAME] = json.dumps(dynamic_auth_config)
    return None

#if PROJECT_ID is not a project_id but project_number, throw error
if PROJECT_ID.isdigit():
    raise ValueError("PROJECT_ID should be a project ID (string) not a project number (integer). "
                     "Please provide a valid project ID in the .env file.")
                     

snow_toolset = ApplicationIntegrationToolset(
    project=PROJECT_ID,
    location=LOCATION,
    connection=INTEGRATION_CONNECTION,
    entity_operations={"Incident": ["GET", "LIST", "CREATE","UPDATE"]},
    tool_instructions=TOOL_INSTR
)

root_agent = Agent(
   model="gemini-2.5-pro",
   name='snow_agent',
   instruction=AGENT_INSTR,
   tools=[snow_toolset],
   before_tool_callback=dynamic_token_injection
)
