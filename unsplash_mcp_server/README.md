# Deploying the Unsplash API as an MCP Server

This project provides a practical example of how to wrap an external REST API (the Unsplash API) and expose its functionality as a set of tools using **FastMCP**, a component of the Google Agent Development Kit (ADK).

By creating a standalone tool server, you can build reusable, scalable, and independently deployable tools that any ADK agent can connect to and use. This approach is ideal for production environments and for sharing tools across multiple agents.

## Prerequisites

- Python 3.8+
- An Unsplash Access Key. You can get one from the [Unsplash Developer portal](https://unsplash.com/developers).

## Setup

1.  **Complete the General Setup:** Follow the initial setup instructions in the main [README.md](../README.md) to create and activate a Python virtual environment.

2.  **Install Dependencies:** From within this directory (`unsplash_mcp_server/`), install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key:** Create a file named `.env` in this directory and add your Unsplash Access Key:
    ```env
    UNSPLASH_ACCESS_KEY="your_unsplash_access_key_here"
    ```

## Code Walkthrough: `app.py`

The entire tool server is defined in `app.py`. Let's break down how it works.

### 1. Server Initialization and Configuration

We start by setting up the FastMCP server and loading the necessary API key from the environment.

```python
# /unsplash_mcp_server/app.py
import os
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Initialize the FastMCP application
mcp = FastMCP("Unsplash MCP Server")

# Retrieve Unsplash Access Key from environment variables
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
if not UNSPLASH_ACCESS_KEY:
    raise ValueError("UNSPLASH_ACCESS_KEY environment variable not set...")
```
- **`load_dotenv()`**: Loads secrets from a `.env` file, which is a best practice for local development.
- **`mcp = FastMCP(...)`**: Creates an instance of the tool server.
- **`os.getenv(...)`**: Securely fetches the `UNSPLASH_ACCESS_KEY`. The server will fail to start if the key is missing, ensuring it doesn't run in a misconfigured state.

### 2. Defining a Tool with `@mcp.tool()`

Any Python function can be exposed as a tool by using the `@mcp.tool()` decorator. The ADK uses the function's signature and docstring to create a schema that an agent can understand.

```python
# /unsplash_mcp_server/app.py
@mcp.tool("search_photos")
def search_photos(query: str, per_page: int = 10, page: int = 1, orientation: str = None) -> dict:
    """
    Searches for photos on Unsplash based on a query. 📸
    ...
    :param query: The search term for photos...
    ...
    :return: A dictionary containing the search results...
    """
    # ... function implementation ...
```
- **`@mcp.tool("search_photos")`**: This decorator registers the `search_photos` function as a callable tool with the name "search_photos".
- **Function Signature & Type Hints**: The parameters (`query: str`, `per_page: int`) define the tool's input arguments and their expected types.
- **Docstring**: The docstring is critical. It provides a human-readable description of the tool and its parameters, which the agent's LLM uses to determine when and how to call the tool.

### 3. Calling the External API

Inside the tool function, we use the `requests` library to make the actual HTTP call to the Unsplash API.

```python
# /unsplash_mcp_server/app.py
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
        "client_id": UNSPLASH_ACCESS_KEY
    }
    # ...
    try:
        response = requests.get(f"{UNSPLASH_API_BASE_URL}/search/photos", params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    # ... error handling ...
```
- **`params` dictionary**: We construct the query parameters for the API call from the tool's input arguments.
- **`requests.get(...)`**: This sends the GET request to the Unsplash endpoint.
- **`response.raise_for_status()`**: A convenient method to automatically check if the API returned an error status code (e.g., 401 Unauthorized, 404 Not Found) and raise an exception if it did.
- **`return response.json()`**: If the call is successful, we parse the JSON response from the API and return it. This data is sent back to the agent that called the tool.

### 4. Robust Error Handling

Proper error handling is essential for a reliable tool. We catch potential exceptions and return structured error messages.

```python
# /unsplash_mcp_server/app.py
    except requests.exceptions.HTTPError as e:
        error_message = f"Failed to fetch photos... Status: {e.response.status_code}, Details: {e.response.text}"
        tools.tool_error(error_message)
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        # ...
```
- **`except ... as e`**: We catch specific `requests` exceptions to handle different failure modes (API errors vs. network errors).
- **`tools.tool_error(error_message)`**: This is a crucial ADK function. It logs the error within the MCP framework, making it visible in the server logs for easier debugging.
- **`return {"error": ...}`**: The tool returns a JSON object with an "error" key. This provides a structured error back to the agent, allowing it to understand that the tool call failed and potentially try again or inform the user.

## Running the MCP Server locally

To run the server locally for development or testing, execute the `app.py` script from your terminal:

```bash
python app.py
```

The server will start and listen for requests, typically on `http://127.0.0.1:8080`. Your ADK agents can now be configured to connect to this endpoint to use the Unsplash tools.

## Test the MCP Server

Once your local MCP server is running, you can test it using the provided `client.py` script. This script acts as a simple client that connects to the server, lists the available tools, and calls each one to verify it's working correctly.

1.  **Ensure your MCP server is running locally.** In one terminal, from the `unsplash_mcp_server/` directory, run:
    ```bash
    python app.py
    ```
    The server should be listening on `http://127.0.0.1:8080`.

2.  **Run the client against your local server.** The client accepts a `--local` flag to connect to the local server. Open a second terminal, from the `unsplash_mcp_server/` directory, run the client script with this flag:
    ```bash
    python client.py --local
    ```

You should see output indicating a successful connection to your local server, a list of the tools it provides (`search_photos`, `get_random_photo`, `get_photo_by_id`), and the results from calling each of those tools. If you run `python client.py` without the flag, it will test the deployed remote server.

## Deploying the MCP Server to Cloud Run

You can deploy this MCP server as a containerized application on Google Cloud Run. This makes it a scalable, serverless tool that your agents can access from anywhere.

### Prerequisites

1.  **Google Cloud SDK**: Make sure you have the `gcloud` command-line tool installed and authenticated (`gcloud auth login` and `gcloud config set project [PROJECT_ID]`).
2.  **Enable APIs**: Enable the Cloud Build, Artifact Registry, and Cloud Run APIs for your Google Cloud project.
3.  **Permissions**: Ensure your account has the necessary permissions to build images and deploy to Cloud Run (e.g., `Cloud Build Editor`, `Artifact Registry Administrator`, `Cloud Run Admin`, `Service Account User`).

### Deployment Steps

1.  **Set up a Secret in Secret Manager**:
    Your Unsplash Access Key should be stored securely. Use Google Cloud Secret Manager to store your key.

    a. Create a new secret:
    ```bash
    gcloud secrets create unsplash-access-key --replication-policy="automatic"
    ```

    b. Add your API key as a secret version. Replace `your_unsplash_access_key_here` with your actual key.
    ```bash
    echo -n "your_unsplash_access_key_here" | gcloud secrets versions add unsplash-access-key --data-file=-
    ```

    c. Grant the Cloud Run service account permission to access the secret. By default, Cloud Run uses the Compute Engine default service account (`[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`).

    ```bash
    gcloud secrets add-iam-policy-binding unsplash-access-key \
      --member="serviceAccount:$(gcloud projects describe [PROJECT_ID] --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor" \
      --project=[PROJECT_ID]
    ```
    > **Note:** Replace `[PROJECT_ID]` with your actual Google Cloud project ID. This command dynamically fetches your project number to construct the service account email.

2.  **Build and Deploy to Cloud Run**:
    Use a single `gcloud` command to build your container image from the source and deploy it to Cloud Run. This command also configures the service to use the secret you created. Replace `[PROJECT_ID]` and `[REGION]` with your project ID and desired region (e.g., `us-central1`).

    ```bash
    gcloud run deploy unsplash-mcp-server \
      --source . \
      --set-secrets=UNSPLASH_ACCESS_KEY=unsplash-access-key:latest \
      --allow-unauthenticated \
      --region [REGION] \
      --project [PROJECT_ID]
    ```
    -   `--source .`: This tells Cloud Build to use the source code in the current directory and the `Dockerfile` to build the image.
    -   `--set-secrets`: Securely mounts the `unsplash-access-key` secret as the `UNSPLASH_ACCESS_KEY` environment variable inside your container.
    -   `--allow-unauthenticated`: Makes the tool server publicly accessible. For production, you would likely want to configure IAM-based authentication.

Once the deployment is complete, `gcloud` will provide you with a service URL. This is the endpoint your ADK agents will use to connect to the Unsplash tool server.

## Testing the MCP Server deployed on Cloud Run

After deploying the server to Cloud Run, you can test the live endpoint using the `client.py` script. The script uses the `gcloud` command-line tool to automatically discover the project number from the project ID.

**Prerequisite:** Ensure you have the Google Cloud SDK installed and authenticated (`gcloud auth login`).

From your terminal, execute the client script with the `--project-id` flag, replacing `[PROJECT_ID]` with your Google Cloud project ID.

```bash
python client.py --project-id [PROJECT_ID]
```

This will connect to your deployed Cloud Run instance and run the same set of tests, confirming that your server is working correctly in the cloud.


## Conclusion

This example demonstrates a complete, end-to-end workflow for productizing an external, third-party API as a secure and scalable tool for ADK agents. By wrapping the Unsplash REST API in a FastMCP server, you have created a standalone microservice that can be independently developed, tested, and deployed on Google Cloud Run.

Key takeaways from this pattern include:

*   **Decoupling**: Tool logic is fully separated from the agent's implementation. This allows the Unsplash tools to be maintained independently and used by multiple different agents without code duplication.
*   **Scalability and Security**: Deploying the tool server to Cloud Run provides a serverless, scalable, and cost-effective hosting solution. Using Secret Manager ensures that sensitive credentials like API keys are handled securely, following production best practices.
*   **Testability**: The project includes a dedicated `client.py` script, demonstrating how to build and run tests against both local and live cloud deployments, ensuring reliability throughout the development lifecycle.

This MCP server pattern is the recommended approach for building robust, reusable, and production-ready tools for your Google ADK agents.
