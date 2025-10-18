from pydantic import BaseModel
import json
import requests

# --- Pydantic Models for OpenWeatherMap API Response ---
class WeatherMain(BaseModel):
    temp: float


class WeatherResponse(BaseModel):
    main: WeatherMain


def get_current_weather(latitude: str, longitude: str, api_key: str):
    """
    Get the current weather in a given location using the OpenWeatherMap API.
    """



    api_endpoint = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"

    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()  # Raise an exception for bad status codes
        weather_data = response.json()

        # Parse with Pydantic
        parsed_data = WeatherResponse.model_validate(weather_data)

        # Convert Kelvin to Celsius
        temp_celsius = parsed_data.main.temp - 273.15

        return json.dumps({"latitude": latitude, "longitude":longitude, "temperature": f"{temp_celsius:.2f}", "unit": "celsius"})

    except requests.exceptions.RequestException as e:
        return json.dumps({"latitude": latitude, "temperature": "unknown", "error": str(e)})
    except Exception as e:
        return json.dumps(
            {"latitude": latitude, "temperature": "unknown", "error": f"Failed to parse weather data: {e}"})