import os
from openai import OpenAI
from datetime import datetime
import json
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# It's recommended to set the API key via environment variable for security
# Make sure you have a .env file with OPENAI_API_KEY="your_key_here"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_time_based_greeting():
    """Gets a greeting based on the current time of day."""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning!"
    elif 12 <= current_hour < 18:
        return "Good afternoon!"
    else:
        return "Good evening!"


def get_current_weather(location, unit="fahrenheit"):
    """
    Get the current weather in a given location using a weather API.
    """
    # Replace with the actual API endpoint from your MCP tool
    api_endpoint = "https://api.weatherprovider.com/v1/current.json"
    
    # Replace with your actual API key or authentication method
    api_key = os.environ.get("WEATHER_API_KEY")

    params = {
        "key": api_key,
        "q": location,
        "aqi": "no" 
    }

    try:
        response = requests.get(api_endpoint, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        weather_data = response.json()

        # Customize this part based on the actual response structure of your MCP tool
        temperature = weather_data.get("current", {}).get(f"temp_{unit}", "unknown")
        return json.dumps({"location": location, "temperature": temperature, "unit": unit})

    except requests.exceptions.RequestException as e:
        return json.dumps({"location": location, "temperature": "unknown", "error": str(e)})


def run_conversation():
    """Starts a conversation with the OpenAI agent."""
    greeting = get_time_based_greeting()
    print(f"Agent: {greeting}")

    messages = [{
        "role": "user",
        "content": "What's the weather like in San Francisco?"
    }]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    # First response from the model
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_current_weather": get_current_weather,
        }
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
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
        print(f"Agent: {second_response.choices[0].message.content}")


if __name__ == "__main__":
    run_conversation()
