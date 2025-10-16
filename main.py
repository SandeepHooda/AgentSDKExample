from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from openai_client import run_conversation
from openai_agent_builder import run_workflow, WorkflowInput
import os
from com.services.gcp_secret import get_secret_value
key = get_secret_value("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = key

app = FastAPI(title="AI agents", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    location = data.get("location")
    user_message = f"What's the weather like at {location}?"
    response = await run_conversation(user_message)
    return {"response": response}

@app.get("/openai-adk")
async def openAIADK(company_name: str = "OpenAI"):
    user_input = f"Tell me about {company_name}"

    workflow_input: WorkflowInput = WorkflowInput(
        input_as_text=user_input
    )
    response_data = await run_workflow(workflow_input)
    return {"response": response_data}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
