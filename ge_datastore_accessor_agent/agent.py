import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.genai import types

from .tools import search_datastore_records

load_dotenv()

MODEL = "gemini-2.5-flash"
AGENT_APP_NAME = 'enterpriseagent'

instruction_prompt = """
You are a helpful assistant that answers user questions by searching a secure corporate datastore.
When a user asks a question, you MUST use the `search_datastore_records` tool to search the datastore for relevant information.
Synthesize the results from the datastore into a clear, concise answer.
If the datastore results contain the answer, provide it. Otherwise, say you could not find the answer in the datastore.
Ensure the final output is valid Markdown.
"""

root_agent = Agent(
        model=MODEL,
        name=AGENT_APP_NAME,
        description="An agent that searches a secure corporate datastore to answer questions.",
        instruction=instruction_prompt,
        generate_content_config=types.GenerateContentConfig(temperature=0.2),
        tools = [search_datastore_records]
)
