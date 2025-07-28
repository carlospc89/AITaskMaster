# pages/2_📂_Upload_File.py
import streamlit as st
import os
import tempfile
import re
import json

# We need to re-import all necessary components for this page
from task_assistant.database_handler import DatabaseHandler
from task_assistant.agent import Agent
from task_assistant.prompts import task_master_prompt
from task_assistant.utils import normalize_text
from task_assistant.rules_engine import RulesEngine
from task_assistant.logger_config import log
from task_assistant.file_handler import read_file  # Specific to this page
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import HumanMessage


# --- Initialization ---
def init_page_services():
    """Initializes services needed for this specific page."""
    log.info("Initializing services for Upload File page...")
    db_handler = DatabaseHandler()
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    model = ChatOllama(model=model_name)
    agent = Agent(model, system=task_master_prompt)
    rules_engine = RulesEngine()
    return db_handler, agent, rules_engine


db_handler, abot, rules_engine = init_page_services()


# This is the same processing function from the original 🤖_Task_Master.py
def process_and_display(content: str, source_name: str):
    """Processes content, stores it in the DB, and displays the result."""
    normalized_content = normalize_text(content)

    if db_handler.check_source_exists(normalized_content):
        st.warning(f"This content from '{source_name}' has already been processed. No new tasks were added.")
        return

    with st.spinner("🤖 AI is analyzing..."):
        try:
            result = abot.graph.invoke({"messages": [HumanMessage(content=normalized_content)]})
            raw_response = result["messages"][-1].content
            log.info(f"Raw AI Response: {raw_response}")

            start_index = raw_response.find('[')
            end_index = raw_response.rfind(']')

            if start_index != -1 and end_index != -1:
                json_str = raw_response[start_index: end_index + 1].strip()
                tasks = json.loads(json_str)
                enriched_tasks = rules_engine.apply_priority(tasks)

                if enriched_tasks:
                    db_handler.insert_data(source_name, normalized_content, enriched_tasks)
                    st.success("Successfully extracted and saved action items!")
                else:
                    st.info("No action items were found.")
            else:
                st.error("The AI returned an invalid response. Could not find a valid JSON block.")
                return

        except json.JSONDecodeError as e:
            log.error(f"Failed to decode JSON: {e}. Raw response was: {raw_response}")
            st.error(f"The AI's response was not valid JSON. Please try again.")
        except Exception as e:
            log.error(f"An unexpected error occurred during processing: {e}")
            st.error(f"An unexpected error occurred: {e}")


# --- Page Content ---
st.set_page_config(page_title="Upload File", page_icon="📂")
st.markdown("# Upload a File for Analysis")

uploaded_file = st.file_uploader("Choose a file", type=['txt', 'docx', 'pdf'])

if uploaded_file is not None:
    # To handle the file processing, we'll show a button after upload
    st.write(f"File uploaded: `{uploaded_file.name}`")
    if st.button("📄 Process File"):
        # Use a temporary file to safely read the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            # The read_file function from file_handler.py abstracts the reading logic
            file_content = read_file(tmp_path)
            process_and_display(file_content, uploaded_file.name)
        finally:
            # Clean up the temporary file
            os.remove(tmp_path)