# Photo Finder A2A (Agent-to-Agent)

This example demonstrates how to convert a simple ADK agent into an A2A (Agent-to-Agent) agent that can communicate with other agents. We start with the `photo_finder_mcp` agent and adapt it for A2A communication.

## From a simple agent to an A2A agent

The original `photo_finder_mcp` agent is designed to connect to a remotely deployed MCP (Multi-agent Communication Protocol) server. To transform it into an A2A agent, we've copied its code into the `photo_finder` sub-directory.

The key change is the addition of an `agent.json` file within the `photo_finder` directory.

### The `agent.json` file

The `agent.json` file is what enables an ADK agent to be discoverable and operate as an A2A agent. It contains essential metadata about the agent, such as its name, version, and the skills it exposes. When you run the agent as an A2A server, the ADK uses this file to configure the necessary API endpoints for other agents to interact with it.

Here is an example of what the `agent.json` for our `photo_finder` agent looks like:

```json
{
    "name": "photo_finder_agent",
    "description": "This agent helps find images and photos from Unsplash ",
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json"],
    "skills": [
        {
        "id": "get_photo_by_id",
        "name": "Find a photo by ID",
        "description": "Given a photo id, it can find a photo or image from Unspash",
        "tags": ["photo finder", "image finder", "unsplash"]
         },
        {
        "id": "get_random_photo",
        "name": "Find a random photo",
        "description": "Finds a random photo from Unsplash, if the user doesnt give any criteria",
        "tags": ["random photo finder", "random image finder", "unsplash"]
        },
        {
        "id": "search_photos",
        "name": "Search for photos",
        "description": "Searches photos or images from Unsplash based on user input",
        "tags": ["photo searcher", "image searcher", "unsplash"]
        }
    ],
    "url": "http://localhost:8010/a2a/photofinder",
    "capabilities": {},
    "version": "1.0.0"
}
```

*   **`name`**: This is a human-readable name for the agent, like `"photo_finder_agent"`. While the documentation you highlighted refers to it as `agent_name`, the correct field in the `agent.json` is simply `name`.

*   **`skill_sets`**: This field is not part of the current A2A `AgentCard` specification, so it's not used in the `agent.json` file. Skills are listed directly under the `skills` array.

*   **`skills`**: This is a crucial field. It's an array that lists all the capabilities the agent can perform. Each object in the array represents a single skill and contains details like:
    *   `id`: A unique identifier for the skill (e.g., `"get_photo_by_id"`).
    *   `name`: A human-readable name for the skill (e.g., `"Find a photo by ID"`).
    *   `description`: A clear explanation of what the skill does. This is very important for other agents or LLMs to understand how and when to use this skill.
    *   `tags`: Keywords that help in categorizing and discovering the skill.

*   **`url`**: The preferred endpoint URL where other agents can communicate with this agent. This URL must support the transport protocol defined in the `preferred_transport` field (which defaults to `JSONRPC`). In this case, we wil run the agent locally at port `8010`. We are choosing that port as we will run the tester at port `8000`.

*   **`capabilities`**: An object that declares optional features the agent supports. In this example, it's empty (`{}`), but it can be used to specify capabilities like:
    *   `streaming`: Whether the agent supports streaming responses (e.g., using Server-Sent Events).
    *   `push_notifications`: Whether the agent can send push notifications for asynchronous task updates.
    *   `state_transition_history`: Whether the agent can provide a history of a task's state changes.



## How to run and test locally

To test the A2A agent locally, we will run the `photo_finder` agent as an A2A server and then use the provided `test_client` to communicate with it.

### How the `test_client` Works

The `test_client` is another ADK agent, specifically an `LlmAgent`, designed to interact with our `photo_finder` A2A agent. It demonstrates how one agent can discover and use the skills of another.

Here's how it works:

*   **Discovery via Agent Card**: The `test_client` is configured to treat the `photo_finder` agent as one of its tools. The ADK framework automatically discovers the `photo_finder` agent's capabilities by reading its `agent.json` file, which serves as its public "Agent Card".

*   **Skill Understanding**: The `test_client`'s underlying LLM parses the `skills` array within the `agent.json`. It reads the `description` of each skill (`get_photo_by_id`, `get_random_photo`, and `search_photos`) to understand what they do.

*   **Tool Invocation**: When you provide a prompt to the `test_client` (e.g., "a photo of a cat"), its LLM reasons that the `search_photos` skill from the `photo_finder` agent is the most appropriate tool to fulfill the request. It then formulates a call to that skill and sends it to the `photo_finder` agent's `url`.

This process showcases the power of A2A: one agent can dynamically use another's capabilities without needing to know its internal implementation details. All the necessary information for discovery and interaction is contained within the `agent.json` file.

### The Role of `RemoteA2aAgent`

The `test_client` uses a special ADK component called `RemoteA2aAgent` to represent the `photo_finder` agent as a tool. This is defined in the `test_client/agent.py` file:

```python
import os
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

# The remote agent's description and card URL are retrieved from environment variables.
REMOTE_AGENT_DESCRIPTION = os.getenv(
    "REMOTE_AGENT_DESCRIPTION", "An agent that tests the remote A2A agent."
)
REMOTE_AGENT_CARD = os.getenv(
    "REMOTE_AGENT_CARD"
)

remote_agent = RemoteA2aAgent(
   name="remote_agent",
   description=REMOTE_AGENT_DESCRIPTION,
   agent_card=REMOTE_AGENT_CARD,
)

root_agent = LlmAgent(
    model='gemini-2.0-flash-001',
    name='a2a_tester',
    description='An agent that tests the remote A2A agent.',
    instruction="""
        Identify what the remote agent does by inquiring on the Agent card.
        Cleary explain to the user that you are proxying the remote agent and explain what you can do based on what you gathered
        from the Agent card.
        Interact with the user and act as an intermediary in the conversations with the remote agent.
        """,
    sub_agents=[remote_agent],
)
```

The `RemoteA2aAgent` class is responsible for:
1.  **Fetching the Agent Card**: It takes the URL to the remote agent's `agent.json` file, which is passed via the `REMOTE_AGENT_CARD` environment variable.
2.  **Resolving Skills**: It parses the fetched `agent.json` to understand the skills offered by the remote agent.
3.  **Acting as a Proxy**: The `test_client` (`a2a_tester`) is configured with the `RemoteA2aAgent` as a `sub_agent`. When the `test_client`'s LLM needs to use a skill from the remote agent, the `RemoteA2aAgent` instance handles the underlying A2A communication, sending the request to the correct `url` and returning the response.

Set the following values in your `.env` file:

```
REMOTE_AGENT_DESCRIPTION="This agent finds photos from Unsplash based on the user's input" 
REMOTE_AGENT_CARD="./photofinder/agent.json"
```

To test the A2A agent locally, we will run the `photo_finder` agent as an A2A server and then use the provided `test_client` to communicate with it.

### Step 1: Run the Photo Finder A2A Agent

1.  Open a terminal and navigate to the `photo_finder_a2a` directory:
    ```bash
    cd learn_adk_agents/photo_finder_a2a
    ```

2.  Run the following command to start the agent as an A2A server on port 8010. The `.` tells the server to look for agents in the current directory. **Note:** This command should be run from the parent directory not while you are inside `photofinder`.
    ```bash
    adk api_server --a2a --port 8010 .
    ```

3.  After running the command, you should see log messages indicating that the server is running. Look for a confirmation that the agent was configured successfully:
    ```
    fast_api.py:386 - Successfully configured A2A agent: photofinder
    ```
    This confirms that your `photo_finder` A2A agent is up and running.

### Step 2: Run the Test Client

The `test_client` is another ADK agent designed to interact with our `photo_finder` A2A agent. It uses the `photo_finder` agent's card to establish a connection and call its skills.

1.  Open a **new** terminal window.

2.  Navigate to the `test_client` directory inside `photo_finder_a2a`:
    ```bash
    cd learn_adk_agents/photo_finder_a2a/test_client
    ```

3.  Start the ADK web interface for the `test_client`:
    ```bash
    adk web
    ```

4.  Open your web browser and go to `http://127.0.0.1:8000`. This is the web UI for the `test_client`.

### Step 3: Test the A2A Communication

Now we will use the `test_client`'s web interface to communicate with the `photo_finder` A2A agent.

1.  In the `test_client` web UI, you will see a text box to enter a prompt.

2.  The `test_client` is programmed to take your input, connect to the `photo_finder` agent using its agent card, and invoke the `find_photo` skill with your input as the query.

3.  Enter a query for a photo, for example:
    ```
    a photo of a cat
    ```

4.  Click "Submit".

5.  The `test_client` will communicate with the `photo_finder` agent running in the other terminal. The `photo_finder` agent will process the request, and the result (a URL to a photo) will be displayed in the `test_client`'s web interface.

You have now successfully tested A2A communication between two agents running locally!