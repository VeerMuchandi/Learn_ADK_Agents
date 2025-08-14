from google.adk.agents import LlmAgent
from .unsplash_tool import get_photo_by_id, get_random_photo, search_unsplash_photos

# Define the agent's instructions and list of tools
root_agent = LlmAgent(
    name="Image_Finder",
    model="gemini-2.5-flash",
    description="An agent that finds images based on user descriptions.",
    instruction="""You are a helpful assistant that can find images using the Unsplash API.
You have access to the following tools: `search_unsplash_photos`, `get_random_photo`, and `get_photo_by_id`.
When the user asks for a picture of something, use the `search_unsplash_photos` tool with their description as the query.
When the user asks for a random photo, use the `get_random_photo` tool.
When the user provides a photo ID, use the `get_photo_by_id` tool.
You should not try to generate the image yourself.
You should respond with only the image URL and no other information.""",
    tools=[
        get_photo_by_id,
        get_random_photo,
        search_unsplash_photos,
    ],
)