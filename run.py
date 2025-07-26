# In run.py

import os  # <-- Add this import
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from task_assistant.agent import Agent
from task_assistant.prompts import task_master_prompt
from task_assistant.file_handler import read_file

load_dotenv()


def main():
    """
    Main function to run the task assistant agent.
    """
    # Use the environment variable for the model name, with "mistral" as a fallback
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    print(f"🖥️  Using model: {model_name}")
    model = ChatOllama(model=model_name)

    abot = Agent(model, system=task_master_prompt)

    # ... rest of the function remains the same ...
    try:
        file_path = "meeting.txt"
        print(f"📄 Reading content from {file_path}...")
        query = read_file(file_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        return

    messages = [HumanMessage(content=query)]

    print("🤖 Invoking agent...")
    result = abot.graph.invoke({"messages": messages})

    final_response = result["messages"][-1].content
    print("\n✅ Final Response:\n")
    print(final_response)


if __name__ == "__main__":
    main()