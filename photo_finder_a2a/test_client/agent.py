import os
from google.adk.agents import LlmAgent

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH



# Remote Agents

REMOTE_AGENT_DESCRIPTION = os.getenv(
    "REMOTE_AGENT_DESCRIPTION", "An agent that tests the remote A2A agent."
)
REMOTE_AGENT_CARD = os.getenv(
    "REMOTE_AGENT_CARD"
)


remote_agent = RemoteA2aAgent(
   name="remote_agent",
   description=REMOTE_AGENT_DESCRIPTION,
   agent_card=(
      REMOTE_AGENT_CARD
   ),
)

# phone_plan_shopper_agent = RemoteA2aAgent(
#     name="phone_plan_shopper_agent",
#     description="Agent that helps shop for EPP discounted phone plans an devices.",
#     agent_card=(
#         f"http://localhost:8001/a2a/phoneplan_shopper{AGENT_CARD_WELL_KNOWN_PATH}"
#     ),
# )

root_agent = LlmAgent(
            model='gemini-2.0-flash-001',
            name='a2a_tester',
            description='An agent that tests the remote A2A agent.',
            #after_tool_callback=self._handle_auth_required_task,
            instruction="""
                Identify what the remote agent does by inquiring on the Agent card.
                Cleary explain to the user that you are proxying the remote agent and explain what you can do based on what you gathered
                from the Agent card.
                Interact with the user and act as an intermediary in the conversations with the remote agent.
                """,
	# Add the sub_agents parameter below
            sub_agents=[remote_agent],

        )
