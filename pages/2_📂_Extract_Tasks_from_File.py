import streamlit as st
import os
import tempfile
from task_assistant.services import initialize_services
from task_assistant.utils import normalize_text
from task_assistant.prompts import task_master_prompt
from task_assistant.file_handler import read_file
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent
rules_engine = st.session_state.rules_engine
data_ingestor = st.session_state.data_ingestor

st.set_page_config(page_title="Extract Tasks from File", page_icon="📂", layout="wide")


# --- Helper Function ---
def process_and_display(content: str, source_name: str):
    normalized_content = normalize_text(content)

    with st.spinner("🤖 AI is analyzing and indexing..."):
        try:
            # THIS IS THE FIX: Call the new agent method and handle the Pydantic object
            task_list_obj = agent.get_structured_tasks(task_master_prompt, normalized_content)

            tasks_to_save = [task.dict() for task in task_list_obj.tasks]

            if tasks_to_save:
                enriched_tasks = rules_engine.apply_priority(tasks_to_save)
                data_ingestor.ingest_data(source_name, content, enriched_tasks)
                st.success(f"Successfully extracted and saved {len(enriched_tasks)} action items!")
            else:
                st.info("No action items were found, but the document has been added to the context memory.")
                # Still add the document to context even if no tasks are found
                data_ingestor.ingest_data(source_name, content, [])

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            log.error(f"Error in Upload File processing: {e}", exc_info=True)


# --- Page Content ---
st.markdown("# Extract Tasks from File")
st.info(
    "Upload a document (e.g., meeting notes) to parse for action items. The content will also be added to the AI's memory for context.")
uploaded_file = st.file_uploader("Choose a file", type=['txt', 'docx', 'pdf'])

if uploaded_file is not None:
    st.write(f"File uploaded: `{uploaded_file.name}`")
    if st.button("📄 Process File"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            file_content = read_file(tmp_path)
            process_and_display(file_content, uploaded_file.name)
        finally:
            os.remove(tmp_path)
