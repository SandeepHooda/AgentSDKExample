from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from com.agents.google.weather_tool.adk_weather import call_weather_agent_google_adk
from com.agents.openai.weather_tool.adk_weather import call_weather_agent_openai_adk
from com.agents.openai.weather_tool.openai_client import get_weather_open_ai_client
from com.agents.openai.company_research.openai_agent_builder import run_workflow, WorkflowInput
import os
import uuid
from com.services.gcp_secret import get_secret_value
from com.agents.google.youtube_reel.loop_agent_runner import call_agent_async

os.environ["OPENAI_API_KEY"] = get_secret_value("OPENAI_API_KEY")
os.environ["GEMINI_API_KEY"] = get_secret_value("GEMINI_API_KEY")

"""key = os.environ["OPENAI_API_KEY"]
if key is None or key == "":
    key = get_secret_value("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = key
"""
app = FastAPI(title="AI agents", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()

@app.get("/openai-client-weather")
async def chat(city_name: str = "Panchkula, Haryana"):
    user_message = f"What's the weather like at {city_name}?"
    response = await get_weather_open_ai_client(user_message)
    return {"response": response}

@app.get("/openai-adk")
async def openAIADK(company_name: str = "OpenAI"):
    user_input = f"Tell me about {company_name}"

    workflow_input: WorkflowInput = WorkflowInput(
        input_as_text=user_input
    )
    response_data = await run_workflow(workflow_input)
    return {"response": response_data}

@app.get("/youtube-reels")
async def getYoutubeReels(topic_name: str = "OpenAI"):
    user_input = f"I want to write a short script on {topic_name}"
    user_id = "some_user_id"  # Replace with actual user identifier
    session_id = str(uuid.uuid4())

    response_data = await call_agent_async(
        query=user_input,
        user_id=user_id,
        session_id=session_id
    )


    return {"response": response_data}

@app.get("/openai-adk-weather")
async def getWeatherOpenAI(city_name: str = "Panchkula, Haryana"):

    workflow_input: WorkflowInput = WorkflowInput(
        input_as_text=f"Tell me the weather in city_name {city_name}"
    )

    response_data = await call_weather_agent_openai_adk(
        workflow_input=workflow_input
    )
    return {"response": response_data}

@app.get("/google-adk-weather")
async def getWeather(city_name: str = "Panchkula, Haryana"):
    user_input = f"Tell me the weather in city_name {city_name}"

    user_id = "some_user_id"  # Replace with actual user identifier
    session_id = str(uuid.uuid4())

    response_data = await call_weather_agent_google_adk(
        query=user_input,
        user_id=user_id,
        session_id=session_id
    )
    return {"response": response_data}
app.mount("/", StaticFiles(directory="static", html=True), name="static")
