# ServiceNow Dynamic OAuth Agent
## Overview
The ServiceNow Dynamic OAuth Agent is a conversational agent built using the Google Agent Development Kit (ADK). It is designed to act as a specialized assistant for interacting with a ServiceNow instance. The agent simplifies the OAuth 2.0 Authorization Code Grant Flow, allowing users to authenticate securely and then perform operations on ServiceNow resources, such as managing Incidents.

When a user interacts with the agent for the first time from Agentspace, it initiates the OAuth 2.0 flow, guiding the user through the authorization process with their ServiceNow account. Once authorized, the agent uses the obtained tokens to make secure API calls to ServiceNow on the user's behalf via a Google Cloud Integration Connector. This enables seamless and secure API access for managing ServiceNow data through a conversational interface.

## Features
*   **Conversational Incident Management**: Allows users to create, retrieve, update, and list ServiceNow incidents using natural language.
*   **Secure Dynamic OAuth 2.0 Flow**: Guides the user through a one-time authorization process within Agentspace, securely managing access tokens for subsequent API calls.
*   **Integration Connector Toolset**: Utilizes the Google Cloud Integration Connector for ServiceNow, providing a robust and pre-built set of tools for interacting with ServiceNow entities.
*   **Deployable and Scalable**: Built with the ADK to be deployed to Agent Engine, providing a scalable and managed conversational AI service.

## Prerequisites

*   **Google Cloud Project**: You need a Google Cloud project with billing enabled.
*   **Enabled APIs**: In your Google Cloud project, ensure the following APIs are enabled:
    *   Application Integration API
    *   Vertex AI Search and Conversation API
*   **Python 3.8+**: This project requires Python 3.8 or later. It's recommended to use a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html).
*   **Google Agent Development Kit (ADK)**: Install the ADK using pip:
    ```bash
    pip install google-adk
    ```
*   **ServiceNow Developer Instance**: You need a ServiceNow instance to connect to. You can get a free personal developer instance from the [ServiceNow Developer Portal](https://developer.servicenow.com/).
*   **ServiceNow User Account**: A user account in the ServiceNow instance with the necessary roles (e.g., `admin`) to create and manage OAuth Application Registry entries.
*   **Agentspace Access**: You need access to an Agentspace environment to register and interact with the deployed agent.
*   **Agent Registration Tool**: You will need the Agent Registration Tool to register your agent with Agentspace. Clone this repository to your local machine.

## Setup and Configuration

Follow these two steps to configure ServiceNow and the agent.

### Step 1: Create an OAuth Application Registry in ServiceNow
First, you need to register the agent as an OAuth client in your ServiceNow instance.

1. Log in to your ServiceNow instance with an administrator account.

2. In the navigation filter, type System OAuth and navigate to System OAuth > Application Registry.

3. Click the New button.

4. On the interceptor page, select Create an OAuth API endpoint for external clients.

5. Fill out the form with the following details:

* *  Name: A descriptive name, e.g., Dynamic OAuth Integration Agent. Make a note of the name you give here as it will be used later. 
* * Redirect URL: The callback URL where the agent will be listening. The agent runs a local web server to receive the authorization code. The URL must be accessible from the machine where you perform the browser-based authorization. Set this to `https://vertexaisearch.cloud.google.com/oauth-redirect`.
* * Add the auth scope `useraccount` to the Auth Scopes section

6. Submit the form.

7. After the record is created, ServiceNow will display the Client ID. You will also have a Client Secret. Copy both of these values, as you will need them to configure the agent.

### Step 2: Configure a Google Integration Connector

This agent is designed to work with Google Integration Connectors, specifically for ServiceNow. Refer detailed [setup instructions](https://cloud.google.com/integration-connectors/docs/connectors/servicenow/configure) as required. Here's how to configure it:

1.  **Create a new connection** in your Google Cloud project.
2.  Choose your region like **us-central1**.
3.  Select the **ServiceNow connector**.
4.  Give the connection a name and description (optional). Note connector name as it will be used in the later steps while deploying the agent.
5.  Enable Cloud Logging with log level set to **ERROR**.
6.  Click Next to get to Destinations and set your ServiceNow instance URL as the host address under HostUrl (https://<your-servicenow-instance>.service-now.com).
7. Click Next to get to Authentication section
8.  For the **Authentication type**, choose **OAuth 2.0**.
9.  Enter the **Client ID** and **Client Secret** you obtained in Step 1. For Client Secret, you would have to add it to th secret manager following the directions.
10.  For the **Authorization URL**, use `https://<your-servicenow-instance>.service-now.com/oauth_auth.do`. Replace `<your-servicenow-instance>` with your actual ServiceNow instance name.
11. Grant permissions to the service account to access the secret.
12. Check **Enable Authentication Override** and click **Next**
13. Review the configuration and click **Create** to create the connection.

It takes a few minutes to provision the connection. You will see that the connection needs to be Authorized. Click to **Authorize Connection** and it brings up **Authorize** window.

* * Copy the **Redirect URI** value that looks like this https://console.cloud.google.com/connectors/oauth?project=YOUR_PROJECT_ID

* * Go back to ServiceNow registry entry you created in the previous step. Replace the Redirect URI in the ServiceNow OAuth Application Registry entry with the above value temporarily. 

* * Now in the **Authorize** window click on **Authorize** button. Sign into ServiceNow and authorize. 

* * Once the authorization is complete, go back to ServiceNow Application Registry and change the redirect URI back to `https://vertexaisearch.cloud.google.com/oauth-redirect` and save it.


### Step 3: Configure an Application Integration ExecuteConnection

Navigate to **Application Integration** in cloud console and create an ExecuteConnection using Quick Setup as explained [here](https://cloud.google.com/application-integration/docs/setup-application-integration#quick). 



## Deploy and Register Agent

We will use `adk deploy` to deploy the ADK agent to Agent Engine, and then the agent registration tool (https://github.com/VeerMuchandi/agent_registration_tool) to create authorization id and to register the agent with Agentspace. Read the documentation for the agent registration tool on how to use it.


### Create Authorization Resource in Agentspace
1. Using the agent registration tool (`python as_registry_client.py`), choose the option to `create_authorization`. You will need to provide the following parameters:
* * Authorization_Id (AUTH_ID): Provide a name (example - snow_dynamic_oauth)
* * OAuth Client Id (OAUTH_CLIENT_ID): **Client Id** that was generated in Step 1 during ServiceNow Application Registry entry setup
* * OAuth Client Secret: **Client Secret** that was generated in Step 1 during ServiceNow Application Registry entry setup
* * Authorization URI: Provide the Auth URI. Create this URI using the following format "https://<your-servicenow-instance>.service-now.com/oauth_auth.do?state=<AUTH_ID>&response_type=code&client_id=$<OAUTH_CLIENT_ID>&scope=useraccount&redirect_uri=<REDIRECT_URI>", by substituting the values in <>. Note the REDIRECT_URI is `https://vertexaisearch.cloud.google.com/oauth-redirect`.
* * OAuth Token URI: Provide the Token URI. Create this URI using the following format "https://<your-servicenow-instance>.service-now.com/oauth_token.do"
2. Ensure that the authorization resource is successfully created.


### Deploy Agent

1. Create the .env file using the env_template. Substitute the values for GOOGLE_CLOUD_PROJECT_ID, AUTH_ID (from the previous step), INTEGRATION_CONNECTOR_NAME (based on Google Integration Connector configuration set up).

2. Create a GCS bucket to use for staging your code for deployment. Note the name of your GCS bucket

3. From the directory where the agent code is, run `adk deploy` to deploy the agent to Agent Engine 
```
adk deploy agent_engine --project=YOUR_PROJECT_ID --region=LOCATION --staging_bucket=gs://YOUR_GCS_BUCKET_NAME --display_name="SNOW Incident Manager" --trace_to_cloud  .
```

It takes several minutes to deploy the agent. Be patient. Note the reasoning engine id as you will need it in the next step as the ADK deployment id.

### Register the agent to Agentspace

Use agent registration tool (`python as_registry_client.py`) to register the agent to Agentspace by using the option `register_agent` by providing
* * Display name: example - SNOW Incident Manager
* * Description: "Agent to manage Service Now incidents"
* * Tool description: "Use this tool for any CRUD operations on SNOW Incident table. Follow directions in the agent and tool instructions"
* * Authorization id: Use the authorization id that you created earlier and configured in the .env file while deploying the agent
* * ADK deployment id: Use the reasoning engine id from the ADK deployment to Agent Engine
* * Optionally you can provide an icon URL

In a couple of seconds the agent will be registered with Agentspace.


## Use the agent from Agentspace

* Navigate to Agent Gallery in Agentspace. (Refresh the screen if you don't see it as the screen may have stale data).
* Invoke the agent and it should ask you to run the OAuth flow with ServiceNow.
* Once the OAuth steps are complete, your agent should connect to ServiceNow and perform incident management operations for you.
