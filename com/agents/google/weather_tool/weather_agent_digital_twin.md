# Weather Agent Dependencies

This document outlines the dependencies between the components of the `weather_agent.py` script. It is intended to be a reference for developers to understand the potential impact of changes to the system.

## High-Level Architecture

The weather agent is a multi-step process orchestrated by a `LoopAgent`. It first determines the latitude and longitude of a city and then uses that information to find the current weather.

The main components are:
- **Configuration and Secrets Management**
- **Instruction Loading**
- **Tools**
- **LLM Agents**
- **Main Agent (`LoopAgent`)**
- **Session and Runner**

## Component Dependencies

### 1. Configuration and Secrets Management

- **`.env` file:** The `load_dotenv()` function loads environment variables from a `.env` file at the start of the script.
    - **Impact of change:** If this file is missing, or if variables are removed, the application may fail to connect to external services.
- **`get_secret_value(secret_name)`:** This function fetches secrets from GCP Secret Manager.
    - **Secrets used:** `GEMINI_API_KEY`, `OPEN_WEATHER_API_KEY`, `COCKROACHDB_URI_PYTHON`.
    - **Impact of change:** If the name of a secret changes in GCP Secret Manager, the corresponding call to `get_secret_value` must be updated. If the secret value itself is changed (e.g., a new API key), the application will need to be restarted to pick up the new value.

### 2. Instruction Loading

- **`load_instruction_from_file(filename, ...)`:** This function loads the instruction for the `weather_agent` from an external file.
    - **File dependency:** `weather_instruction.txt`. This file is expected to be in the same directory as `weather_agent.py`.
    - **Impact of change:** Any change to the content of `weather_instruction.txt` will alter the behavior of the `weather_agent`. If the file is renamed or moved, the `load_instruction_from_file` function will use a default instruction, which will likely cause the agent to behave incorrectly.

### 3. Tools

- **`get_current_weather(lat_long, unit)`:**
    - **External dependency:** Makes an API call to `https://api.openweathermap.org`.
    - **Impact of change:**
        - If the OpenWeatherMap API changes its endpoint, response format, or API key requirements, this function will need to be updated.
        - The function expects the `lat_long` parameter to be a string of comma-separated latitude and longitude. If the format of this data changes, the function will fail.
- **`google_search`:**
    - **External dependency:** This tool is imported from the `google.adk.tools` library and is used by the `lat_long_agent`.

### 4. LLM Agents

- **`lat_long_agent`:**
    - **Input:** Expects a city name to be present in `state['city_name']`.
    - **Output:** Stores the latitude and longitude in `state['lat_long']`.
    - **Impact of change:**
        - The prompt is hardcoded. Changes to the prompt will affect the agent's ability to find the correct latitude and longitude.
        - If the key used for the output (`output_key="lat_long"`) is changed, the `weather_agent` will fail.
- **`weather_agent`:**
    - **Input:** The underlying LLM uses the `state['lat_long']` value to call the `get_current_weather` tool.
    - **Output:** Stores the weather information in `state['weather_output']`.
    - **Impact of change:**
        - If the `lat_long` data is not available or is in an incorrect format in the state, this agent will fail.
        - The behavior of this agent is highly dependent on the instructions in `weather_instruction.txt`.

### 5. Main Agent (`main_agent`)

- **Type:** `LoopAgent`
- **Sub-agents:** `[lat_long_agent, weather_agent]`
- **Dependency:** The order of the sub-agents is critical. `lat_long_agent` must execute before `weather_agent` because the latter depends on the output of the former.
    - **Impact of change:** Reversing the order of the agents will break the data flow and cause the `weather_agent` to fail.

### 6. Session and Runner

- **`setup_session_and_runner(...)`:**
    - **External dependency:** Connects to a CockroachDB database using the `COCKROACHDB_URI_PYTHON` secret.
    - **Impact of change:** If the database is unavailable, or if the connection string is incorrect, session creation will fail.
- **`call_weather_agent_async(...)`:**
    - This is the main entry point for the agent. It orchestrates the setup and execution of the agent.

## Data Flow through State

The agents communicate by reading and writing to a shared `state` dictionary. The keys of this dictionary are a critical part of the contract between the agents.

- `state['city_name']` -> **`lat_long_agent`** -> `state['lat_long']`
- `state['lat_long']` -> **`weather_agent`** -> `state['weather_output']`

**Impact of change:** If the name of any of these keys is changed in one agent, the other agents that depend on it will fail. This is not something that can be caught by a compiler or interpreter.
