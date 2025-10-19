from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig
from openai.types.shared.reasoning import Reasoning
import asyncio


class WebResearchAgentSchema__CompaniesItem(BaseModel):
  company_name: str
  industry: str
  headquarters_location: str
  company_size: str
  website: str
  description: str
  founded_year: float


class WebResearchAgentSchema(BaseModel):
  companies: list[WebResearchAgentSchema__CompaniesItem]


class SummarizeAndDisplaySchema(BaseModel):
  company_name: str
  industry: str
  headquarters_location: str
  company_size: str
  website: str
  description: str
  founded_year: float


web_research_agent = Agent(
  name="Web research agent",
  instructions="You are a helpful assistant. Use web search to find information about the following company I can use in marketing asset based on the underlying topic.",
  model="gpt-5-mini",
  output_type=WebResearchAgentSchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low"
    )
  )
)


summarize_and_display = Agent(
  name="Summarize and display",
  instructions="""Put the research together in a nice display using the output format described.
""",
  model="gpt-5",
  output_type=SummarizeAndDisplaySchema,
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
async def run_workflow(workflow_input: WorkflowInput):
  state = {

  }
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
  web_research_agent_result_temp = await Runner.run(
    web_research_agent,
    input=[
      *conversation_history
    ],
    run_config=RunConfig(trace_metadata={
      "__trace_source__": "agent-builder",
      "workflow_id": "wf_68f0375feb6c8190a110fbdd34abf144037c1473f024bba3"
    })
  )

  conversation_history.extend([item.to_input_item() for item in web_research_agent_result_temp.new_items])

  # This is just to show both text and parsed output, it is not used further in the workflow
  web_research_agent_result = {
    "output_text": web_research_agent_result_temp.final_output.json(),
    "output_parsed": web_research_agent_result_temp.final_output.model_dump()
  }
  summarize_and_display_result_temp = await Runner.run(
    summarize_and_display,
    input=[
      *conversation_history
    ],
    run_config=RunConfig(trace_metadata={
      "__trace_source__": "agent-builder",
      "workflow_id": "wf_68f0375feb6c8190a110fbdd34abf144037c1473f024bba3"
    })
  )
  summarize_and_display_result = {
    "output_text": summarize_and_display_result_temp.final_output.json(),
    "output_parsed": summarize_and_display_result_temp.final_output.model_dump()
  }
  print(summarize_and_display_result)
  return summarize_and_display_result

if __name__ == "__main__":
  workflow_input: WorkflowInput = WorkflowInput(
    input_as_text="Tell me about OpenAI"
  )
  asyncio.run(run_workflow(workflow_input))