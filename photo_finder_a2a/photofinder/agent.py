import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams


# The URL for the Unsplash MCP server.
# Defaults to the local server, but can be overridden by an environment variable.
UNSPLASH_MCP_SERVER_URL = os.getenv(
    "UNSPLASH_MCP_SERVER_URL", "http://127.0.0.1:8080/mcp/"
)

# Define the connection to the Unsplash MCP server.
# This toolset will connect to the remote server and expose its tools to the agent.
unsplash_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=UNSPLASH_MCP_SERVER_URL
    )
)

# Define the agent's instructions and list of tools
root_agent = LlmAgent(
    name="Image_Finder_MCP",
    model="gemini-2.5-flash",
    description="An agent that finds images by calling a remote MCP tool server.",
    instruction="""You are a helpful assistant that can find images using tools from a remote server.
You should not try to generate the image yourself.
You should respond with only the image URL and no other information.""",
    tools=[
       unsplash_toolset,
    ],
)