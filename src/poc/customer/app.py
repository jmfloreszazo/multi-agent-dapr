from dapr_agents import AssistantAgent, OpenAIChatClient
from dotenv import load_dotenv
import asyncio
import os
import pandas as pd
import docx
import PyPDF2

SYSTEM_PROMPT = """
You are orchestrating a structured conversation between two agents: the ClientAgent, who represents the issuer of an RFP, and the SupplierAgent, who represents a creative and media agency submitting a proposal.

Your role is to ensure that the ClientAgent challenges the SupplierAgent section by section, based on the RFP content, and that the SupplierAgent responds with strategic, clear, and comprehensive answers drawn from internal best practices.

Guide the agents through a constructive dialogue to iteratively build and refine a complete, high-quality proposal aligned with the RFP requirements.
"""

RFP_FILES_DIR = os.path.abspath("../files/customer")

def extract_text_from_files():
    texts = []
    for filename in os.listdir(RFP_FILES_DIR):
        path = os.path.join(RFP_FILES_DIR, filename)
        if filename.endswith(".docx"):
            doc = docx.Document(path)
            texts.append("\n".join(p.text for p in doc.paragraphs))
        elif filename.endswith(".pdf"):
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                texts.append("\n".join(page.extract_text() for page in reader.pages if page.extract_text()))
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(path)
            texts.append(df.to_string())
    return "\n\n".join(texts)

async def main():
    try:
        llm = OpenAIChatClient(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )

        context = extract_text_from_files()

        agent = AssistantAgent(
            role="Client",
            name="ClientAgent",
            goal="Coordinate a constructive and iterative dialogue between the client and supplier agents to produce a complete, high-quality response to the RFP.",
            instructions=[SYSTEM_PROMPT, context],
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
