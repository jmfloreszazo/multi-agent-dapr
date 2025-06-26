from dapr_agents import AssistantAgent, OpenAIChatClient
from dotenv import load_dotenv
import asyncio
import os
import docx

SYSTEM_PROMPT = """
You are a senior representative of a full-service creative and media agency with proven expertise in tourism marketing. 
You have submitted a detailed proposal in response to the MCCVB RFP, and you are now being challenged by the client to justify and defend how your agency will meet each of the RFP requirements.

For each question or challenge, respond with clarity, professionalism, and evidence-based reasoning. 
Reference the contents of your proposal where appropriate, and be prepared to elaborate or refine your approach.

Focus on strategic alignment, creativity, media planning, KPIs, tourism sector knowledge, and your agency's capacity to deliver results across all requested services.
"""


RESPONSE_PATH = "../files/supplier/bestpractices.docx"

def load_response_docx():
    if not os.path.exists(RESPONSE_PATH):
        return ""
    doc = docx.Document(RESPONSE_PATH)
    return "\n".join(p.text for p in doc.paragraphs)

async def main():
    try:
        llm = OpenAIChatClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )

        response_text = load_response_docx()

        agent = AssistantAgent(
            role="Supplier",
            name="SupplierAgent",
            goal="Defend and clarify the agency’s proposal by responding to the client’s questions in a professional and strategic manner, demonstrating how all RFP requirements are met through creative, media, and tourism marketing expertise.",
            instructions=[SYSTEM_PROMPT, response_text],
            message_bus_name="messagepubsub",
            state_store_name="workflowstatestore",
            state_key="workflow_state",
            agents_registry_store_name="agentstatestore",
            agents_registry_key="agents_registry",
            llm=llm,
        )

        await agent.start()
    except Exception as e:
        print(f"Error starting service: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())