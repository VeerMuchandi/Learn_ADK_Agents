from google.adk.agents import Agent
from .prompts import ROOT_AGENT_INSTR

from .snow_connector_tool import snow_connector_tool

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='servicenow_agent',
    description="ServiceNow Agent to help with Problems and Incidents.",
    instruction=ROOT_AGENT_INSTR,
    tools= [snow_connector_tool],
)