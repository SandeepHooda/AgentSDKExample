from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from openai_client import run_conversation

app = FastAPI(title="AI agents", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()
# 1. Receive a request with a location
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    location = data.get("location")
    user_message = f"What's the weather like at {location}?"
    response = await run_conversation(user_message)
    return {"response": response}



app.mount("/", StaticFiles(directory="static", html=True), name="static")