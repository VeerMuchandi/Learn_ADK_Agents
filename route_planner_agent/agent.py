from google.adk.agents import LlmAgent
from .route_planner import get_directions, get_address_of_place, search_nearby_places  # Import the custom tool module

# This agent uses a custom tool that handles a user-centric OAuth flow.
# The ADK framework discovers the `get_directions` function from the tool and
# makes it available to the LLM.
#
# The LLM uses the agent's instructions and the tool's docstring to
# determine when and how to use it. When the tool is called, the user running
# the agent will be prompted to sign in via their browser if they haven't
# already.
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="route_planning_agent",
    description="An agent that can plan routes using Google Maps with user authentication.",
    instruction="""You are a helpful route planning assistant. Your goal is to provide routing information between two locations.

If the user provides a named place (like 'home', 'office', or a business name) instead of a full address, you MUST first use the `get_address_of_place` tool to find the full address for that place.

Once you have the full addresses for both the origin and destination, and the travel mode (e.g., driving, walking, bicycling, or transit), you MUST call the `get_directions` tool to find the route.

If the user asks for places near a location, you MUST use the `search_nearby_places` tool. You will need the location's address and what type of place to search for (e.g., "restaurants", "coffee shops").

If any of this information is missing, ask the user for it before calling a tool.

Present the final directions from the tool directly to the user.""",
    tools=[get_directions, get_address_of_place, search_nearby_places],
)
