# ADK Agent with an MCP Toolset

This example demonstrates a Google ADK agent that connects to and uses a remote tool server built with FastMCP.

This approach decouples the agent's logic from the tool's implementation. The agent doesn't need to know how the tools work internally; it only needs the server's address to connect and use them. This is the recommended pattern for production agents, as it allows tools to be developed, scaled, and maintained independently.

This example should be used in conjunction with the [`unsplash_mcp_server`](../unsplash_mcp_server/README.md) example.

## How it Differs from Direct API Calls

In the `photo_finder_api` example, the agent's tools were Python functions that directly called the Unsplash API.

*   **`photo_finder_api` (Direct API Call):** The agent imports tool functions directly and lists them in the `tools` array. The agent and tools are tightly coupled.
    ```python
    # photo_finder_api/agent.py
    from .unsplash_tool import search_unsplash_photos
    # ...
    root_agent = LlmAgent(
        # ...
        tools=[search_unsplash_photos],
    )
    ```

*   **`photo_finder_mcp` (MCP Toolset):** In this example, the agent doesn't import any tool functions. Instead, it uses an `MCPToolset` to connect to the running tool server. The agent discovers the available tools (`search_photos`, etc.) from the server at runtime.
    ```python
    # photo_finder_mcp/agent.py
    from google.adk.tools.mcp_tool import MCPToolset
    # ...
    unsplash_toolset = MCPToolset(...)
    # ...
    root_agent = LlmAgent(
        # ...
        tools=[unsplash_toolset],
    )
    ```

This decoupling makes the agent simpler and the tools more reusable and scalable.

## Code Walkthrough: `agent.py`

The `agent.py` file defines how the agent connects to the MCP server.

```python
# photo_finder_mcp/agent.py
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

UNSPLASH_MCP_SERVER_URL = os.getenv(
    "UNSPLASH_MCP_SERVER_URL", "http://127.0.0.1:8080/mcp/"
)

unsplash_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=UNSPLASH_MCP_SERVER_URL)
)

root_agent = LlmAgent(
    name="Image_Finder_MCP",
    # ...
    tools=[unsplash_toolset],
)
```

**Key Components:**

*   **`os.getenv(...)`**: We fetch the server URL from an environment variable, `UNSPLASH_MCP_SERVER_URL`. This makes it easy to switch between a local test server and a deployed production server without changing the code. It defaults to the local server address.
*   **`MCPToolset`**: This is the core component from the ADK that represents a collection of tools available from an MCP server.
*   **`StreamableHTTPConnectionParams`**: This class configures the HTTP connection to the MCP server, taking the server's `url` as a parameter.
*   **`tools=[unsplash_toolset]`**: The `LlmAgent` is given the `unsplash_toolset` instance. The agent will automatically introspect the toolset to discover the available tools (`search_photos`, `get_random_photo`, etc.) and their schemas from the remote server.

## Running the Agent Locally

To test this agent, you first need to run the `unsplash_mcp_server` locally. Then, you can run the ADK web interface to interact with this agent.

1.  **Start the MCP Tool Server:**
    Open a terminal, navigate to the `unsplash_mcp_server` directory, and run the server. Make sure you have configured its `.env` file as described in its README.
    ```bash
    # In terminal 1, from the unsplash_mcp_server/ directory
    python app.py
    ```
    The server will be running at `http://127.0.0.1:8080`.

2.  **Run the ADK Web UI:**
    The `agent.py` file is already configured to connect to the local server by default. Open a second terminal, navigate to the root `partnerexamples` directory, and start the web UI.
    ```bash
    # In terminal 2, from the partnerexamples/ directory
    adk web
    ```

3.  **Test the Agent:**
    *   Open your browser to the URL provided by the `adk web` command (usually `http://127.0.0.1:8501`).
    *   In the sidebar, select the **`Image_Finder_MCP`** agent.
    *   In the chat input, type a request like: `Find me a picture of a classic car`.

The agent will connect to your local MCP server, use the `search_photos` tool, and return a result.

## Running against a Remote (Cloud Run) Server

You can also test this agent against the version of the `unsplash_mcp_server` that was deployed on Cloud Run. This simulates a production environment where the agent and its tools are running as separate services.

### Prerequisites

1.  You have successfully deployed the `unsplash_mcp_server` to your Google Cloud project on Cloud Run by following the instructions in its README file.
2.  You have your Google Cloud Project ID and the Region you deployed to.

### Steps

1.  **Get the Service URL:** The URL for your deployed service is provided at the end of the `gcloud run deploy` command. If you don't have it, you can find it in the Cloud Run section of the Google Cloud Console or reconstruct it.

2.  **Set the Environment Variable and Run:** When you run the ADK web UI, set the `UNSPLASH_MCP_SERVER_URL` environment variable to the URL of your deployed service. From the root `partnerexamples` directory, run:

    ```bash
    export UNSPLASH_MCP_SERVER_URL="[YOUR_CLOUD_RUN_SERVICE_URL]/mcp"
    adk web
    ```
    *(Note: The `export` command is for Linux/macOS. For Windows, use `set UNSPLASH_MCP_SERVER_URL="..."`)*

3.  **Test the Agent:**
    *   Open your browser to the URL provided by the `adk web` command.
    *   Select the **`Image_Finder_MCP`** agent.

The agent will now make calls to your live Cloud Run service instead of the local one.

