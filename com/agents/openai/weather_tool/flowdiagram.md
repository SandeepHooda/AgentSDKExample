                   ┌────────────────────────┐
                   │   START (main block)   │
                   └────────────┬───────────┘
                                │
                                ▼
               ┌──────────────────────────────────┐
               │ Create WorkflowInput object      │
               │ "Tell me the weather   Panchkula"│
               └──────────────────────────────────┘
                                │
                                ▼
            ┌──────────────────────────────────────────┐
            │ call_weather_agent_openai_adk() async fn │
            └──────────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────┐
        │ Build conversation_history (user text)│
        └───────────────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────┐
     │ Runner.run(lat_long_agent)                       │
     │ → Uses GPT model to find latitude & longitude    │
     │ → Output type: LatLangSchema(lat, long)          │
     └──────────────────────────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────┐
     │ Extend conversation_history with new items       │
     └──────────────────────────────────────────────────┘
                                │
                                ▼
     ┌──────────────────────────────────────────────────┐
     │ Runner.run(weather_agent)                        │
     │ → Uses FunctionTool: get_current_weather()       │
     │ → Fetches data from OpenWeatherMap API           │
     │ → Converts Kelvin → Celsius / Fahrenheit         │
     │ → Returns WeatherResponse                        │
     └──────────────────────────────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────┐
        │ Extract cityName and temperatures  │
        │ Format result summary string       │
        └────────────────────────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Print & return result│
                     │  Example:            │
                     │ "Current weather in  │
                     │ Panchkula is 29°C .."│
                     └──────────────────────┘
                                │
                                ▼
                        ┌─────────────┐
                        │    END 🏁   │
                        └─────────────┘

