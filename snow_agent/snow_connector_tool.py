import os
from dotenv import load_dotenv
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.tools.apihub_tool.clients.secret_client import SecretManagerClient
from google.adk.auth import AuthCredential, AuthCredentialTypes, OAuth2Auth

from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows


load_dotenv()

SNOW_CONNECTION_PROJECT_ID=os.getenv("SNOW_CONNECTION_PROJECT_ID")
SNOW_CONNECTION_REGION=os.getenv("SNOW_CONNECTION_REGION")
SNOW_CONNECTION_NAME=os.getenv("SNOW_CONNECTION_NAME")
SNOW_INSTANCE_NAME=os.getenv("SNOW_INSTANCE_NAME")
SNOW_OAUTH_SCOPES=os.getenv("SNOW_OAUTH_SCOPES")
SECRET_MANAGER_SNOW_CLIENT_ID=os.getenv("SECRET_MANAGER_SNOW_CLIENT_ID")
SECRET_MANAGER_SNOW_CLIENT_SECRET=os.getenv("SECRET_MANAGER_SNOW_CLIENT_SECRET")

SNOW_CLIENT_ID=f"projects/{SNOW_CONNECTION_PROJECT_ID}/secrets/{SECRET_MANAGER_SNOW_CLIENT_ID}/versions/latest"
#SNOW_CLIENT_SECRET=f"projects/{SNOW_CONNECTION_PROJECT_ID}/secrets/adk-snow-client-secret/versions/2"
SNOW_CLIENT_SECRET=f"projects/{SNOW_CONNECTION_PROJECT_ID}/secrets/{SECRET_MANAGER_SNOW_CLIENT_SECRET}/versions/1"

AGENT_REDIRECT_URI=os.getenv("AGENT_REDIRECT_URI")

# Get the credentials for the ServiceNow APIs
secret_manager_client = SecretManagerClient()
snow_client_id = secret_manager_client.get_secret(SNOW_CLIENT_ID)
snow_client_secret = secret_manager_client.get_secret(SNOW_CLIENT_SECRET)

TOOL_INSTR="""
        **Tool Definition: ServiceNow Connector via Apigee Integration**

        This tool interacts with ServiceNow entities (Problems, Incidents) using an Apigee Integration Connector.
        It supports GET, LIST, and CREATE operations as defined for each entity.

        **CRITICAL: Authentication - `dynamic_auth_config` Parameter**

        *   **MANDATORY:** Every function call to this tool (e.g., `snow_connector_tool_get_problem`, `snow_connector_tool_list_incident`) **MUST** include the `dynamic_auth_config` parameter in the function call.
        *   **SYSTEM HANDLED:** This parameter is automatically populated with the necessary OAuth access token by the system. Your role is to ensure you *always* include `dynamic_auth_config` in your function call requests.
        *   **VALIDATION:** The system expects `dynamic_auth_config` to be present and valid. Do not attempt to generate or modify its value.

        **General Tool Usage:**

        *   **Tool Naming Convention:** Tool functions follow the pattern: `snow_connector_tool_<operation>_<entity_name_singular>`.
            *   Example: `snow_connector_tool_get_problem`, `snow_connector_tool_list_incident`.
        *   **Supported Entity Operations:**
            *   `Problem`: GET, LIST, CREATE
            *   `Incident`: GET, LIST, CREATE

        **Data Retrieval (GET and LIST Operations):**

        *   **Retrieve Specific Record (GET):**
            *   Use the `GET` operation (e.g., `snow_connector_tool_get_problem`).
            *   The `entity_id` parameter **MUST** be the ServiceNow `sys_id` of the record.
        *   **Retrieve Multiple Records (LIST):**
            *   Use the `LIST` operation (e.g., `snow_connector_tool_list_problem`).
            *   **Filtering with `filterClause`:** This is essential for targeted data retrieval.
                *   **To retrieve a Problem record by its Problem Number (e.g., "PRB000123"):**
                    Use `snow_connector_tool_list_problem` with `filterClause="number='PRB000123'"`.
                *   **To retrieve Problem records assigned to a specific user:**
                    Use `snow_connector_tool_list_problem` with `filterClause="assigned_to='USER_SYS_ID'"` (where `USER_SYS_ID` is the `sys_id` of the user).
                *   **To retrieve related Incidents for a given Problem record:**
                    Use `snow_connector_tool_list_incident` with `filterClause="problem_id='PROBLEM_SYS_ID'"` (where `PROBLEM_SYS_ID` is the `sys_id` of the parent Problem).

        **Problem Creation:**

        *   **Tool:** Use `snow_connector_tool_create_problem`.
        *   **Information Gathering:**
            1.  Collect minimal information from the user to describe the new problem.
            2.  Deduce appropriate values for `category`, `impact`, and `urgency` based on the user-provided details.
        *   **User Confirmation:**
            1.  Before calling `snow_connector_tool_create_problem`, present the summarized details (description, deduced category, impact, urgency) to the user.
            2.  Ask for explicit confirmation from the user to proceed with creation.
        *   **Post-Creation Steps:**
            1.  After the problem is successfully created by `snow_connector_tool_create_problem` (which will return the new record including its `sys_id`).
            2.  Immediately call `snow_connector_tool_get_problem` using the `sys_id` of the newly created problem to fetch its complete and up-to-date details.
            3.  Present the **Problem Number** (e.g., "PRB0040001") and other key details (like description, state, priority) to the user. Do **NOT** show the `sys_id` as the primary identifier to the user.
"""

oauth2_scheme = OAuth2(
   flows=OAuthFlows(
      authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl=f"https://{SNOW_INSTANCE_NAME}.service-now.com/oauth_auth.do",
            tokenUrl=f"https://{SNOW_INSTANCE_NAME}.service-now.com/oauth_token.do",
            scopes={
                f"{SNOW_OAUTH_SCOPES}" : "default",
            }
      )
   )
)

oauth2_credential = AuthCredential(
  auth_type=AuthCredentialTypes.OAUTH2,
  oauth2=OAuth2Auth(
    client_id=snow_client_id,
    client_secret=snow_client_secret,
    redirect_uri=AGENT_REDIRECT_URI # This is the ADK Web UI
  )
)


snow_connector_tool = ApplicationIntegrationToolset(
    project=SNOW_CONNECTION_PROJECT_ID, 
    location=SNOW_CONNECTION_REGION, 
    connection=SNOW_CONNECTION_NAME,
    entity_operations={
        "Problem": ["GET", "LIST", "CREATE"],
        "Incident": ["GET", "LIST", "CREATE"],
    },
    tool_name_prefix="snow_connector_tool",
    tool_instructions=TOOL_INSTR,
    auth_credential=oauth2_credential,
    auth_scheme=oauth2_scheme,
)