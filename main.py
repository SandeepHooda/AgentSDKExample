import os
from openai import OpenAI
from datetime import datetime
import json
from dotenv import load_dotenv
import requests
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

# Load environment variables from .env file
load_dotenv()

# It's recommended to set the API key via environment variable for security
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = FastAPI()

# --- Pydantic Models for OpenWeatherMap API Response ---
class WeatherMain(BaseModel):
    temp: float

class WeatherResponse(BaseModel):
    main: WeatherMain

def get_time_based_greeting():
    """Gets a greeting based on the current time of day."""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning!"
    elif 12 <= current_hour < 18:
        return "Good afternoon!"
    else:
        return "Good evening!"

def get_current_weather(location: str, unit: str = "celsius"):
    """
    Get the current weather in a given location using the OpenWeatherMap API.
    """
    api_key = os.environ.get("OPEN_WEATHER_API_KEY")
    if not api_key:
        return json.dumps({"location": location, "temperature": "unknown", "error": "OPEN_WEATHER_API_KEY not set"})

    try:
        lat, lon = location.split(',')
    except ValueError:
        return json.dumps({"location": location, "temperature": "unknown", "error": "Invalid location format. Please use 'latitude,longitude'"})

    api_endpoint = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()  # Raise an exception for bad status codes
        weather_data = response.json()

        # Parse with Pydantic
        parsed_data = WeatherResponse.parse_obj(weather_data)

        # Convert Kelvin to Celsius
        temp_celsius = parsed_data.main.temp - 273.15

        return json.dumps({"location": location, "temperature": f"{temp_celsius:.2f}", "unit": "celsius"})

    except requests.exceptions.RequestException as e:
        return json.dumps({"location": location, "temperature": "unknown", "error": str(e)})
    except Exception as e:
        return json.dumps({"location": location, "temperature": "unknown", "error": f"Failed to parse weather data: {e}"})


tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather for a given latitude and longitude.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The latitude and longitude, e.g., '37.7749,-122.4194'",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

available_functions = {
            "get_current_weather": get_current_weather,
        }

async def run_conversation(user_message: str):
    """Starts a conversation with the OpenAI agent."""
    greeting = get_time_based_greeting()

    messages = [{
        "role": "user",
        "content": user_message
    }]


    # 2. First response from the model
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools, # 2.1 Register tools (text description of tools) so that AI can decide to use it
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 3. If there's a tool call, execute it and get the result
    if tool_calls:

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name] # 3.1 Map tool call to actual function from available functions array
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call( # 3.2 A simple python function call to the function with arguments from AI's first response
                location=function_args.get("location"),
                unit=function_args.get("unit"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )

        # Second response from the model
        second_response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )
        return f"{greeting} {second_response.choices[0].message.content}"
    else:
        return f"{greeting} {response_message.content}"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html") as f:
        return f.read()
# 1. Receive a request with a location
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    location = data.get("location")
    user_message = f"What's the weather like at {location}?"
    response = await run_conversation(user_message)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
