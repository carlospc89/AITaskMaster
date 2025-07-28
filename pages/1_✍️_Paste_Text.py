import streamlit as st
import json
from task_assistant.services import initialize_services
from task_assistant.utils import normalize_text
from task_assistant.prompts import task_master_prompt
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent
rules_engine = st.session_state.rules_engine
data_ingestor = st.session_state.data_ingestor

st.set_page_config(page_title="Paste Text", page_icon="✍️", layout="wide")


# --- Helper Function ---
def process_and_display(content: str, source_name: str):
    normalized_content = normalize_text(content)

    with st.spinner("🤖 AI is analyzing..."):
        try:
            # THIS IS THE FIX: Call the new agent method and handle the Pydantic object
            task_list_obj = agent.get_structured_tasks(task_master_prompt, normalized_content)

            # The result is a Pydantic object; we convert it to a list of dicts
            tasks_to_save = [task.dict() for task in task_list_obj.tasks]

            if tasks_to_save:
                enriched_tasks = rules_engine.apply_priority(tasks_to_save)
                # Use the data_ingestor to save the data
                data_ingestor.ingest_data(source_name, content, enriched_tasks)
                st.success(f"Successfully extracted and saved {len(enriched_tasks)} action items!")
            else:
                st.info("No action items were found.")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            log.error(f"Error in Paste Text processing: {e}", exc_info=True)


# --- Page Content ---
st.markdown("# Paste Text for Analysis")
with st.form(key="text_input_form"):
    notes_input = st.text_area("Paste your meeting notes or any text here:", height=250)
    submit_text = st.form_submit_button(label="✨ Extract Action Items")

if submit_text and notes_input:
    process_and_display(notes_input, "pasted_text")
