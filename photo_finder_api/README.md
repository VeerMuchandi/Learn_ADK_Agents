# Building an ADK agent to use Unsplash APIs

This example demonstrates how to build a Google ADK agent that directly calls an external REST API (the Unsplash API) to perform tasks. The API calls are wrapped in simple Python functions and provided as tools to the agent.

This approach is ideal for:
*   Simpler agents where the tools are tightly coupled with the agent logic.
*   When you don't need to share the tools across multiple different agents.
*   Rapid prototyping and development.

For scenarios where tools need to be shared, scaled independently, or are more complex, consider using the [MCP Server approach](../unsplash_mcp_server/README.md).

## Setup

1.  **Complete the initial environment setup** by following the instructions in the main [README.md file at the root of this repository](../README.md). This includes setting up a virtual environment and installing the ADK.

2.  **Install project-specific dependencies** from within this directory (`photo_finder_api/`):
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your API Key:** Create a file named `.env` in this directory and add your Unsplash Access Key:
    ```env
    UNSPLASH_ACCESS_KEY="your_unsplash_access_key_here"
    ```

## Code Walkthrough

This agent is composed of two main files:
*   `unsplash_tool.py`: Contains the Python functions that wrap the Unsplash API calls.
*   `agent.py`: Defines the `LlmAgent` and provides it with the tools and instructions.

### 1. Creating the Tools (`unsplash_tool.py`)

A "tool" for an ADK agent can be any standard Python function. The ADK uses the function's signature (name, parameters, type hints) and its docstring to understand what the tool does and how to use it.

Here's how we wrap the Unsplash "search photos" endpoint:

```python
# photo_finder_api/unsplash_tool.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_BASE_URL = "https://api.unsplash.com"

def search_unsplash_photos(query: str, per_page: int = 5) -> dict:
    """
    Searches for photos on Unsplash based on a query. 📸

    :param query: The search term for photos (e.g., "mountains", "cityscape").
    :param per_page: The number of results to return (default: 5).
    :return: A dictionary containing the search results, or an error message.
    """
    # ... (Implementation details in the actual file)
```

**Key Concepts:**
*   **No Special Decorators:** Unlike the MCP approach, these are plain Python functions.
*   **Docstrings are the Schema:** The LLM uses the docstring to understand the tool's purpose and its parameters. Clear, descriptive docstrings are essential.
*   **Type Hinting:** Type hints (`query: str`) help the agent understand the expected data types for each parameter.
*   **Returning Data:** The function should return JSON-serializable data (like a `dict` or `list`) that the agent can process. Returning an `{"error": ...}` dictionary is a simple way to handle failures.

### 2. Defining the Agent (`agent.py`)

The `agent.py` file brings everything together. It imports the tool functions and passes them to an `LlmAgent`.

```python
# photo_finder_api/agent.py
from google.adk.agents import LlmAgent
from .unsplash_tool import get_photo_by_id, get_random_photo, search_unsplash_photos

root_agent = LlmAgent(
    name="Image_Finder",
    model="gemini-1.5-flash",
    # ...
    instruction="""You are a helpful assistant that can find images...
You have access to the following tools: `search_unsplash_photos`, `get_random_photo`, and `get_photo_by_id`...""",
    tools=[
        get_photo_by_id,
        get_random_photo,
        search_unsplash_photos,
    ],
)
```

**Key Concepts:**
*   **Importing Tools:** We directly import the functions from our `unsplash_tool.py` file.
*   **`tools` Parameter:** The imported functions are passed as a list to the `tools` parameter of the `LlmAgent`. The ADK automatically inspects these functions to make them available to the LLM.
*   **`instruction` Prompt:** This is the most critical part. The prompt explicitly tells the agent about the tools it has (`search_unsplash_photos`, etc.) and gives it clear instructions on when to use each one based on the user's request.

## Running the Agent

You can run this agent locally using the ADK command-line interface.

1.  Make sure you are in the parent directory (`partnerexamples`).
2.  Run the agent, specifying the path to the agent object:

```bash
adk web
```

This will start a web server on the workstation. You can connect to the localhost to test the agent. Select the agent `photo_finder_api` and start interacting with the agent. 
