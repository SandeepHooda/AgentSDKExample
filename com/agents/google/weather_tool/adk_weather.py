from google.adk.runners import Runner

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import google_search
from google.genai import types

import requests
import os
import json
from dotenv import load_dotenv
from com.services.gcp_secret import get_secret_value



# Load environment variables
load_dotenv()

# Get API keys from secret manager
api_key = get_secret_value("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = api_key

def load_instruction_from_file(
    filename: str, default_instruction: str = "Default instruction."
) -> str:
    """Reads instruction text from a file relative to this script."""
    instruction = default_instruction
    try:
        # Construct path relative to the current script file (__file__)
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, "r", encoding="utf-8") as f:
            instruction = f.read()
        print(f"Successfully loaded instruction from {filename}")
    except FileNotFoundError:
        print(f"WARNING: Instruction file not found: {filepath}. Using default.")
    except Exception as e:
        print(f"ERROR loading instruction file {filepath}: {e}. Using default.")
    return instruction

# --- Define tool: get_current_weather ---
def get_current_weather(lat_long: str, unit: str = "celsius"):
    """
    Get the current weather for a given latitude and longitude using OpenWeatherMap. Return temperature in Celsius.
    """
    weather_key = get_secret_value("OPEN_WEATHER_API_KEY")
    os.environ["OPEN_WEATHER_API_KEY"] = weather_key
    print(f" lat_long: {lat_long}, unit: {unit}")
    try:
        lat, lon = lat_long.split(',')
    except ValueError:
        return json.dumps({"error": "Invalid lat_long format. Use 'latitude,longitude'"})
    lat = lat.strip()
    lon = lon.strip()
    api_endpoint = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_key}"

    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        temperature = data["main"]["temp"] - 273.15
        if unit.lower() == "fahrenheit":
            temperature = (temperature * 9/5) + 32
        return json.dumps({
            "lat_long": lat_long,
            "temperature": f"{temperature:.2f}",
            "unit": unit
        })
    except Exception as e:
        return json.dumps({"error": str(e)})



lat_long_agent = LlmAgent(
    name="lat_long_agent",
    model="gemini-2.0-flash-001",
    instruction="""Find the latitude and longitude for the (from `state['city_name']`) and store the result in state['lat_long'] in the format 'latitude,longitude'.""",
    tools=[google_search],
    output_key="lat_long",  # Save result to state
)

weather_agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.0-flash-001",
    instruction=load_instruction_from_file("weather_instruction.txt"),
    tools=[get_current_weather],
    output_key="weather_output",  # Save result to state
)


main_agent = LoopAgent(
    name="main_agent",
    max_iterations=1,
    sub_agents=[lat_long_agent,weather_agent],
)

# Instantiate constants
APP_NAME = "weater_app"

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

    runner = Runner(agent=main_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_weather_agent_google_adk(query: str, user_id: str, session_id: str):
    print(f"User_ID: {user_id}, Session_ID: {session_id}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner( user_id,   session_id)
    events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            #print("Agent Response: ", final_response)
    return final_response