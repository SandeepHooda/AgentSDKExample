                         ┌────────────────────────┐
                         │   Start / Entry Point  │
                         └────────────┬───────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────────┐
                     │ Load environment variables (.env)  │
                     └────────────────────────────────────┘
                                      │
                                      ▼
                   ┌───────────────────────────────────────┐
                   │ Fetch secrets via get_secret_value()  │
                   │  - GEMINI_API_KEY                     │
                   │  - OPEN_WEATHER_API_KEY               │
                   │  - COCKROACHDB_URI_PYTHON             │
                   └───────────────────────────────────────┘
                                      │
                                      ▼
          ┌────────────────────────────────────────────────────────┐
          │ Define utility: load_instruction_from_file(filename)   │
          │  → Reads text instructions (fallback to default)       │
          └────────────────────────────────────────────────────────┘
                                      │
                                      ▼
          ┌────────────────────────────────────────────────────────┐
          │ Define tool: get_current_weather(lat_long, unit)       │
          │  • Parse lat/long                                      │
          │  • Call OpenWeatherMap API                             │
          │  • Convert temperature (C/F)                           │
          │  • Return JSON output                                  │
          └────────────────────────────────────────────────────────┘
                                      │
                                      ▼
   ┌──────────────────────────────────────────────────────────┐
   │ Define LlmAgent: lat_long_agent                          │
   │  - Finds coordinates using google_search                 │
   │  - Stores result in state['lat_long']                    │
   └──────────────────────────────────────────────────────────┘
                                      │
                                      ▼
   ┌──────────────────────────────────────────────────────────┐
   │ Define LlmAgent: weather_agent                           │
   │  - Loads instruction from file                           │
   │  - Calls get_current_weather()                           │
   │  - Stores result in state['weather_output']              │
   └──────────────────────────────────────────────────────────┘
                                      │
                                      ▼
        ┌────────────────────────────────────────────────┐
        │ Define LoopAgent: main_agent                   │
        │  - Runs lat_long_agent → weather_agent         │
        │  - max_iterations = 1                          │
        └────────────────────────────────────────────────┘
                                      │
                                      ▼
        ┌───────────────────────────────────────────────────────────┐
        │ setup_session_and_runner(user_id, session_id)             │
        │  • Initialize DatabaseSessionService                      │
        │  • Create session (CockroachDB)                           │
        │  • Initialize Runner(main_agent, session_service)         │
        └───────────────────────────────────────────────────────────┘
                                      │
                                      ▼
        ┌───────────────────────────────────────────────────────────┐
        │ call_weather_agent_google_adk(query, user_id, session_id) │
        │  • Create user message (types.Content)                    │
        │  • Setup session + runner                                 │
        │  • Run main_agent asynchronously                          │
        │  • Wait for final response                                │
        │  • Return final weather result                            │
        └───────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │       End / Return     │
                         └────────────────────────┘
