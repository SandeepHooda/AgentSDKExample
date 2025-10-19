# adk_weather.py Component Dependencies

This document outlines the components of `adk_weather.py` and their interdependencies. It focuses on non-obvious dependencies that a compiler or interpreter would not catch, which could lead to runtime errors if modified without care.

## 1. Core Components

The script is composed of the following main components:

*   **Pydantic Models:** `WeatherObj`, `WeatherResponse`, `LatLangSchema`, `WorkflowInput`. These define the data structures for API responses and workflow inputs.
    *   `WeatherObj` now contains `temperature_celsius` and `temperature_fahrenheit`.
    *   `WeatherResponse` now contains a `cityName` field.
*   **Tool:** `get_current_weather` function and its `FunctionTool` wrapper `weather_function`. This component is responsible for fetching weather data from an external API.
*   **Agents:** `lat_long_agent` and `weather_agent`. These are AI agents that perform specific tasks.
*   **Workflow:** `call_weather_agent_openai_adk` function. This orchestrates the execution of the agents.
*   **External Services:**
    *   Google Cloud Secret Manager (for API keys)
    *   OpenWeatherMap API (for weather data)

## 2. Interaction Flow

The `call_weather_agent_openai_adk` function defines the main execution flow:

1.  It receives a `WorkflowInput` containing a natural language query (e.g., "What's the weather in London?").
2.  It runs `lat_long_agent` to convert the city name into latitude and longitude coordinates.
3.  The result from `lat_long_agent` is added to the conversation history.
4.  It runs `weather_agent`, which uses the conversation history (containing the latitude and longitude) to call the `get_current_weather` tool.
5.  `get_current_weather` fetches the weather from the OpenWeatherMap API.
6.  The final weather information is formatted and returned.

## 3. Implicit Dependencies & Potential Breaking Changes

The following are dependencies that are not enforced by the code's syntax but are critical for the script's correct operation.

### 3.1. Agent Output to Agent Input

*   **Dependency:** The `weather_agent` implicitly depends on the output format of the `lat_long_agent`.
*   **How it can break:** The `lat_long_agent` is instructed to "store the result in state['lat_long'] in the format 'latitude,longitude'". The `weather_agent` relies on this exact format being present in the conversation history to extract the latitude and longitude for its tool call. If the instructions for `lat_long_agent` are changed to produce a different format (e.g., a JSON object, or a different string representation), the `weather_agent` will fail.

### 3.2. Tool Function and its JSON Schema

*   **Dependency:** The `get_current_weather` function's implementation is tightly coupled to the `params_json_schema` defined in `weather_function`.
*   **How it can break:** The `get_current_weather` function expects its `params` argument to be a JSON string containing `"lat"` and `"long"` keys. The `params_json_schema` in `weather_function` defines this contract. If you were to change the expected parameters in the `get_current_weather` function (e.g., rename `lat` to `latitude`), you *must* also update the `params_json_schema` to match. Failure to do so would cause the `weather_agent` to fail when trying to use the tool.

### 3.3. External API Contracts

*   **Dependency:** The `get_current_weather` function is dependent on the structure of the JSON response from the OpenWeatherMap API.
*   **How it can break:** The code accesses the temperature via `data["main"]["temp"]`. If OpenWeatherMap changes its API and moves this value to a different location in the JSON response, the `get_current_weather` function will raise a `KeyError` and fail.

*   **Dependency:** The `get_current_weather` function is also dependent on the API endpoint URL.
*   **How it can break:** The code uses `https://api.openweathermap.org/data/2.5/weather...`. If this URL changes, the function will fail.

### 3.4. Secret Management

*   **Dependency:** The script relies on specific secret names in Google Cloud Secret Manager.
*   **How it can break:** The code hardcodes the secret names `"OPENAI_API_KEY"` and `"OPEN_WEATHER_API_KEY"`. If these names are changed in Secret Manager, the `get_secret_value` calls will fail, and the application will not be able to authenticate with the necessary services.

### 3.5. Pydantic Model and Agent Output

*   **Dependency:** The `weather_agent` is expected to produce an output that conforms to the `WeatherResponse` Pydantic model.
*   **How it can break:** The `instructions` for the `weather_agent` tell it to "return response in WeatherResponse format". If these instructions are changed and the agent produces a differently structured output, the `call_weather_agent_openai_adk` function will fail during the final parsing of the result (`weather_result_temp.final_output.model_dump()`). The final result string formatting also depends on the new fields `cityName`, `weather.temperature_celsius`, and `weather.temperature_fahrenheit` being present in the parsed output.
