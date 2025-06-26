import json
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

STATE_FILE = os.path.abspath("../workflow/LLMOrchestrator_state.json")

def load_conversation():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    instances = data.get("instances", {})
    if not instances:
        print("No conversation instances found.")
        return
    def get_end_time(x):
        end_time = x.get("end_time")
        return end_time if end_time is not None else ""
    latest = max(instances.values(), key=get_end_time)
    messages = latest.get("messages", [])
    return messages

def format_markdown(messages):
    md = ["# Conversation between ClientAgent and SupplierAgent\n"]
    md.append("| # | Agent | Message |")
    md.append("|---|-------|---------|")
    for idx, msg in enumerate(messages, 1):
        role = msg.get("role", "")
        content = msg.get("content", "").replace("\n", "<br>")
        md.append(f"| {idx} | {role} | {content} |")
    return "\n".join(md)

def format_client_supplier_qa(messages):
    """
    Devuelve una tabla markdown con pares de pregunta (ClientAgent) y respuesta (SupplierAgent).
    Si hay más preguntas que respuestas, la respuesta queda vacía.
    """
    qa_pairs = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.get("name") == "ClientAgent":
            question = msg.get("content", "").replace("\n", "<br>")
            # Busca la siguiente respuesta del SupplierAgent
            answer = ""
            j = i + 1
            while j < len(messages):
                next_msg = messages[j]
                if next_msg.get("name") == "SupplierAgent":
                    answer = next_msg.get("content", "").replace("\n", "<br>")
                    break
                j += 1
            qa_pairs.append((question, answer))
        i += 1

    md = ["# Q&A entre ClientAgent y SupplierAgent\n"]
    md.append("| # | Pregunta (Cliente) | Respuesta (Supplier) |")
    md.append("|---|--------------------|---------------------|")
    for idx, (q, a) in enumerate(qa_pairs, 1):
        md.append(f"| {idx} | {q} | {a} |")
    return "\n".join(md)

def summarize_with_azure_openai(text):
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    response = client.chat.completions.create(
        model=deployment,
        messages=[{
            "role": "user",
            "content": (
                'Format the following conversation as a clear, human-readable Q&A transcript. For each question from the ClientAgent, number it and present it as "Question X:". Immediately after, present the corresponding answer from the SupplierAgent as "Answer X:". Do not include any document references, citations, or section numbers—just the questions and answers. If a question does not have a direct answer, write "Not answered 😕" in place of the answer, making it very visual and easy to spot. Use plain English and make the conversation easy to follow for a human reader. Do not summarize or omit any content; simply organize the dialogue into numbered question and answer pairs. All output should be in English.\n\n'
                + text
            )
        }]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    load_dotenv()
    messages = load_conversation()
    if messages:
        markdown = format_client_supplier_qa(messages)
        with open("conversation.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        print("conversation.md file generated.")
        summary = summarize_with_azure_openai(markdown) 
        with open("conversation_resume.md", "w", encoding="utf-8") as f:
            f.write(summary)
        print("conversation_resume.md file generated.")
    else:
        print("No messages to display.")