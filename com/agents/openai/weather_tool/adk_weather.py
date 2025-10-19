from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, Tool, FunctionTool

from openai.types.shared.reasoning import Reasoning
import asyncio
import os
from com.services.gcp_secret import get_secret_value
import json
import requests

# --- Pydantic Models for OpenWeatherMap API Response ---
class WeatherObj(BaseModel):
    temperature_celsius: float
    temperature_fahrenheit: float

class WeatherResponse(BaseModel):
    weather: WeatherObj
    location: str
    cityName: str


class LatLangSchema(BaseModel):
  lat: float
  long: float

  # Get API keys from secret manager
key = get_secret_value("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = key



# --- Define tool: get_current_weather ---
async def get_current_weather(ctx, params: str) -> str:
      """
      Get the current weather for a given latitude and longitude using OpenWeatherMap. Return temperature in Celsius.
      """
      weather_key = get_secret_value("OPEN_WEATHER_API_KEY")
      os.environ["OPEN_WEATHER_API_KEY"] = weather_key
      args = json.loads(params)
      lat = args.get("lat")
      long = args.get("long")
      unit = args.get("unit", "celsius")

      api_endpoint = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={weather_key}"

      try:
          response = requests.get(api_endpoint)
          response.raise_for_status()
          data = response.json()
          temperature = data["main"]["temp"] - 273.15
          if unit.lower() == "fahrenheit":
              temperature = (temperature * 9 / 5) + 32
          return json.dumps({
              "lat": lat,
              "long": long,
              "temperature": f"{temperature:.2f}",
              "unit": unit
          })
      except Exception as e:
          return json.dumps({"error": str(e)})

# Define the function schema properly
weather_function =  FunctionTool(
    name="get_current_weather",
    description="Get the current weather for a given latitude and longitude.",
    on_invoke_tool=get_current_weather,
    params_json_schema={
        "type": "object",
        "properties": {
             "lat": {
                        "type": "number",
                        "description": "The latitude e.g., '37.7749'",
                    },
            "long": {
                        "type": "number",
                        "description": "The longitude, e.g., '-122.4194'",
                    },
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
        },
        "required": ["lat","long"],
    },
)



lat_long_agent = Agent(
  name="Web research to find latitude and longitude of a city",
  instructions="Find the latitude and longitude for the following city and store the result in state['lat_long'] in the format 'latitude,longitude'.",
  model="gpt-5-mini",
  output_type=LatLangSchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low"
    )
  )
)


weather_agent = Agent(
  name="Find weather information",
  instructions="""Get the current weather for a given latitude and longitude using get_current_weather tool and 
  return response in WeatherResponse format.
""",
  model="gpt-5",
  tools=[weather_function],
  output_type=WeatherResponse,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="minimal"
    )
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def call_weather_agent_openai_adk(workflow_input: WorkflowInput):

  workflow = workflow_input.model_dump()
  conversation_history: list[TResponseInputItem] = [
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": workflow["input_as_text"]
        }
      ]
    }
  ]
  lat_lang_results = await Runner.run(
    lat_long_agent,
    input=[
      *conversation_history
    ]
  )

  conversation_history.extend([item.to_input_item() for item in lat_lang_results.new_items])

  weather_result_temp = await Runner.run(
    weather_agent,
    input=[
      *conversation_history
    ]
  )

  result_summary = {
      "output_parsed": weather_result_temp.final_output.model_dump()
  }
  print(result_summary)
  result = (f"Current weather at {result_summary['output_parsed']['cityName']} "
            f"is {result_summary['output_parsed']['weather']['temperature_celsius']} celsius and "
            f"{result_summary['output_parsed']['weather']['temperature_fahrenheit']} fahrenheit.")
  print(result)
  return result

if __name__ == "__main__":
  workflow_input: WorkflowInput = WorkflowInput(
    input_as_text="Tell me the weather in Panchkula, Haryana"
  )
  asyncio.run(call_weather_agent_openai_adk(workflow_input))