from dapr_agents import LLMOrchestrator, OpenAIChatClient
from dotenv import load_dotenv
import asyncio
import os

async def main():
    try:
        llm = OpenAIChatClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )

        orchestrator = LLMOrchestrator(
            name="LLMOrchestrator",
            message_bus_name="messagepubsub",
            state_store_name="workflowstatestore",
            state_key="workflow_state",
            agents_registry_store_name="agentstatestore",
            agents_registry_key="agents_registry",
            max_iterations=10,
            llm=llm,
        )

        service = orchestrator.as_service(port=8004)
        await service.start()
    except Exception as e:
        print(f"Error starting workflow: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
