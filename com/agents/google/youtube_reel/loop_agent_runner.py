# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Shows how to call all the sub-agents in a loop iteratively. Run this as you would run a standard python file.

from sqlalchemy import create_engine
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import google_search
import os
# Use a direct import since this script is meant to be run directly.
from .util import load_instruction_from_file, get_secret_value


# --- Sub Agent 1: Scriptwriter ---
scriptwriter_agent = LlmAgent(
    name="ShortsScriptwriter",
    model="gemini-2.0-flash-001",
    instruction=load_instruction_from_file("scriptwriter_instruction.txt"),
    tools=[google_search],
    output_key="generated_script",  # Save result to state
)

# --- Sub Agent 2: Visualizer ---
visualizer_agent = LlmAgent(
    name="ShortsVisualizer",
    model="gemini-2.0-flash-001",
    instruction=load_instruction_from_file("visualizer_instruction.txt"),
    description="Generates visual concepts based on a provided script.",
    output_key="visual_concepts",  # Save result to state
)

# --- Sub Agent 3: Formatter ---
# This agent would read both state keys and combine into the final Markdown
formatter_agent = LlmAgent(
    name="ConceptFormatter",
    model="gemini-2.0-flash-001",
    instruction="""Combine the script from state['generated_script'] and the visual concepts from state['visual_concepts'] into the final Markdown format requested previously (Hook, Script & Visuals table, Visual Notes, CTA).""",
    description="Formats the final Short concept.",
    output_key="final_short_concept",
)


# --- Loop Agent Workflow ---
youtube_shorts_agent = LoopAgent(
    name="youtube_shorts_agent",
    max_iterations=1,
    sub_agents=[scriptwriter_agent, visualizer_agent, formatter_agent],
)

# --- Root Agent for the Runner ---
# The runner will now execute the workflow
root_agent = youtube_shorts_agent


# Code required to make the agent programmatically runnable.
from google.genai import types
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from dotenv import load_dotenv

load_dotenv()

# Instantiate constants
APP_NAME = "youtube_shorts_app"

COCKROACHDB_URI_PYTHON = get_secret_value("COCKROACHDB_URI_PYTHON")
os.environ["COCKROACHDB_URI_PYTHON"] = COCKROACHDB_URI_PYTHON
"""COCKROACHDB_URI_PYTHON = os.environ['COCKROACHDB_URI_PYTHON']
if COCKROACHDB_URI_PYTHON is None or COCKROACHDB_URI_PYTHON == "":
    COCKROACHDB_URI_PYTHON = get_secret_value("COCKROACHDB_URI_PYTHON")
    os.environ['COCKROACHDB_URI_PYTHON'] = COCKROACHDB_URI_PYTHON
"""

# Session and Runner
async def setup_session_and_runner(user_id: str,   session_id: str):
     # Path to your downloaded root.crt file

    # 1. Instantiate the DatabaseSessionService with your connection string
    session_service = DatabaseSessionService( db_url=COCKROACHDB_URI_PYTHON )  # ⬅️ REPLACED InMemorySessionService

    print("Creating session...")
    session =  await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    print(f"Session created successfully. {session}", session)

    runner = Runner(agent=youtube_shorts_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_agent_async(query: str, user_id: str,   session_id: str):
    print(f"User_ID: {user_id}, Session_ID: {session_id}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner( user_id,   session_id)
    events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            #print("Agent Response: ", final_response)
    return final_response

# called from main.py
#asyncio.run( call_agent_async("I want to write a short script on how to build AI Agents"))