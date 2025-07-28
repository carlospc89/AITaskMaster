# pages/2_📂_Extract_Tasks_from_File.py
import streamlit as st
import os
import tempfile
import json

from task_assistant.services import initialize_services
from task_assistant.utils import normalize_text
from task_assistant.prompts import task_master_prompt
from task_assistant.file_handler import read_file
from langchain_core.messages import HumanMessage
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent
rules_engine = st.session_state.rules_engine

st.set_page_config(page_title="Extract Tasks from File", page_icon="📂", layout="wide")


# --- Helper Function ---
def process_and_display(content: str, source_name: str):
    normalized_content = normalize_text(content)
    if db_handler.check_source_exists(normalized_content):
        st.warning(f"This content from '{source_name}' has already been processed.")
        return

    with st.spinner("🤖 AI is analyzing and indexing..."):
        try:
            agent.system = task_master_prompt
            result = agent.graph.invoke({"messages": [HumanMessage(content=normalized_content)]})
            raw_response = result["messages"][-1].content
            log.info(f"Raw AI Response: {raw_response}")

            start_index = raw_response.find('[')
            end_index = raw_response.rfind(']')

            if start_index != -1 and end_index != -1:
                json_str = raw_response[start_index: end_index + 1].strip()
                tasks = json.loads(json_str)
                enriched_tasks = rules_engine.apply_priority(tasks)

                if enriched_tasks:
                    db_handler.insert_data(source_name, content, enriched_tasks)
                    st.success(f"Successfully extracted and saved {len(enriched_tasks)} action items!")
                else:
                    st.info("No action items were found, but the document has been added to the context memory.")
                    # Still add the document to context even if no tasks are found
                    db_handler.insert_data(source_name, content, [])
            else:
                st.error("The AI returned an invalid response. Could not find a valid JSON block.")
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
