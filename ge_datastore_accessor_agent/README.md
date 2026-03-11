# Gemini Enterprise Datastore Accessor Agent

This agent demonstrates how to build a **High-Code AI Agent** using the Google Agent Development Kit (ADK) that securely accesses a Gemini Enterprise Datastore, inspired by the concepts established in ["ADK Agents with Agentspace Authenticated Datastores"](https://medium.com/google-cloud/adk-agents-with-agentspace-authenticated-datastores-efd24d2712be) by Olejniczak Lukasz.

## 🔐 Security & ACLs (Access Control Lists)

The critical feature of this agent is its ability to respect **User-Level Access Controls (ACLs)**. 

When searching a corporate datastore (like one connected to Google Drive or Jira), it is vital that the AI agent **only** retrieves documents that the specific calling user is authorized to see. 

This agent achieves this by passing the **User's OAuth Token** directly to the Discovery Engine API.
*   **No Generic Service Account**: The agent does *not* use a broad service account to search.
*   **User Identity Propagation**: The end-user's identity is propagated from the Gemini Enterprise runtime -> to the Agent -> to the Datastore API.
*   **Result Trimming**: The Datastore API uses the user's token to filter results at the source, ensuring no unauthorized data ever reaches the agent's context.

## 🛠️ Code Deep Dive: `DatastoreService`

The core logic resides in [`tools.py`](./tools.py), specifically the `DatastoreService` class. It implements a dual-strategy for authentication to support both Production and Local Development.

### 1. Production Strategy (Gemini Enterprise)
In a deployed environment, the Gemini Enterprise runtime handles the complex OAuth handshake with the user. It places the user's **Access Token** into the agent's session state.

The `search_datastore_records` tool retrieves this token:
```python
# tools.py
access_token = tool_context.state.get(AUTH_NAME)
```
This token is then used in the `Authorization` header of the API request:
```python
headers = {
    "Authorization": f"Bearer {self.access_token}",
    "Content-Type": "application/json"
}
```

### 2. Local Development Strategy (ADC)
For local testing, you don't have the Agentspace runtime injecting tokens. The `DatastoreService` handles this gracefully by falling back to **Application Default Credentials (ADC)**.

```python
# tools.py
if access_token:
    self.access_token = access_token
else:
    # Fallback to local user credentials
    creds, project = google.auth.default()
    creds.refresh(google.auth.transport.requests.Request())
    self.access_token = creds.token
```
This allows you to run and test the agent on your workstation using your own gcloud credentials (`gcloud auth application-default login`), simulating the permissions you would have in production.

## 🚀 Deployment

We deploy the agent to **Vertex AI Agent Engine** using the standard `adk deploy` command. This effectively "freezes" the agent code and configuration into a managed service.

### Prerequisites
1.  **GCP Project**: Ensure you have a project with Vertex AI and Discovery Engine APIs enabled.
2.  **Staging Bucket**: A GCS bucket to store the agent code during deployment.

### Command
Run the following from this directory:

```bash
adk deploy agent_engine \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --staging_bucket=gs://YOUR_STAGING_BUCKET \
  --display_name="GE Datastore Accessor" \
  .
```

## 🔗 Registration (Gemini Enterprise)

To enable the OAuth flow and make the agent available in Gemini Enterprise:

### 1. Create OAuth Client ID
1.  Go to **GCP Console > APIs & Services > Credentials**.
2.  Click **Create Credentials > OAuth client ID**.
3.  Application type: **Web application**.
4.  **Authorized redirect URIs**: Add `https://vertexaisearch.cloud.google.com/oauth-redirect`.
5.  Create and note the **Client ID** and **Client Secret**.

### 2. Create Authorization Resource

The "Authorization" menu is often hidden in the Console. We will use the API directly.

**Run this `curl` command:**

```bash
# Set your values
PROJECT_ID="your-project-id"
LOCATION="global" # or us-central1
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"
AUTH_ID="my-auth-resource"

curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/authorizations?authorizationId=${AUTH_ID}" \
-d "{
  \"displayName\": \"${AUTH_ID}\",
  \"serverSideOauth2\": {
    \"clientId\": \"${CLIENT_ID}\",
    \"clientSecret\": \"${CLIENT_SECRET}\",
    \"tokenUri\": \"https://oauth2.googleapis.com/token\",
    \"authorizationUri\": \"https://accounts.google.com/o/oauth2/v2/auth?client_id=${CLIENT_ID}&response_type=code&redirect_uri=https://vertexaisearch.cloud.google.com/oauth-redirect&scope=https://www.googleapis.com/auth/cloud-platform&access_type=offline&prompt=consent\",
    \"scopes\": [\"https://www.googleapis.com/auth/cloud-platform\"]
  }
}"
```
*Note the `AUTH_ID` you set here.*

### 3. Update or Delete Authorization (If needed)

If you made a mistake (e.g., incorrect `client_id` or `authorizationUri`), you must delete the existing resource before creating it again.

**To Delete:**
```bash
curl -X DELETE \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
"https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/authorizations/${AUTH_ID}"
```
Then run the **Create** command (Step 2) again with the corrected values.

### 4. Register the Agent
For now, we will use the REST API approach via the CLI to ensure the agent is configured correctly with the authorization resource, as the Gemini Enterprise UI for agent registration currently does not support `tool_authorizations`.

**Critical Concept:** Registering the agent with an `authorization_config` pointing to our Authorization Object (from Step 2) is the mechanism that tells the Gemini Enterprise UI to automatically trigger the OAuth sign-in flow for the end-user.

**Run this `curl` command:**

```bash
# Set your values
PROJECT_ID="your-project-id"
PROJECT_NUMBER="your-project-number"
ENDPOINT_LOCATION="global" # or us or eu
APP_ID="your-gemini-enterprise-app-id"
ADK_RESOURCE_ID="projects/your-project-id/locations/us-central1/reasoningEngines/your-engine-id"
AUTH_ID="my-auth-resource" # From Step 2

curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: ${PROJECT_ID}" \
"https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents" \
-d '{ 
  "displayName": "Corporate Search Assistant", 
  "description": "Searches internal documents securely.", 
  "adk_agent_definition": { 
    "provisioned_reasoning_engine": { 
      "reasoning_engine": "'"${ADK_RESOURCE_ID}"'" 
    } 
  }, 
  "authorization_config": { 
    "tool_authorizations": [ "projects/'"${PROJECT_NUMBER}"'/locations/global/authorizations/'"${AUTH_ID}"'" ] 
  } 
}'
```

### 5. Configure User Access
By default, the agent is not available to anyone. To grant access:
1.  In the Agents list, find your agent.
2.  Navigate to the **User Permissions** tab.
3.  Click **Add User**.
4.  Enter the email addresses (e.g., specific users or "All Users" in your organization).
5.  Select the **Agent User** role.

**Result**: Because the agent was registered with the `tool_authorizations` configuration, when a user chats with this agent, Gemini Enterprise will automatically prompt them to sign in via Google to grant access. The resulting Access Token is then securely injected into the agent's session state under the `AUTH_NAME` key, enabling `DatastoreService` to perform user-context searches on their behalf.

## 💻 Local Testing

You can test the agent locally using the ADK web server.

1.  **Authenticate Locally**:
    ```bash
    gcloud auth application-default login
    ```
2.  **Configure Environment**:
    Ensure your `.env` file has the correct `DATA_STORE_ID`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION`.
3.  **Run the Agent**:
    ```bash
    adk web .
    ```
4.  **Interact**:
    Open the provided local URL (usually `http://localhost:8080`) and chat with the agent. The `DatastoreService` will automatically detect that no token was passed by the runtime and fall back to your local `gcloud` credentials to search the datastore.

