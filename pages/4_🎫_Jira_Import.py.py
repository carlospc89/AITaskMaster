import streamlit as st
import os
import tempfile
from task_assistant.services import initialize_services
from task_assistant.jira_handler import process_jira_csv
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
rules_engine = st.session_state.rules_engine

st.set_page_config(page_title="Jira Import", page_icon="🗂️", layout="wide")

# --- Page Content ---
st.markdown("# Import Action Items from Jira")
st.info("Upload a CSV file exported from Jira. The app will find tasks assigned to the user defined in your .env file.")

jira_file = st.file_uploader("Choose a Jira CSV file", type=['csv'])

if jira_file is not None:
    if st.button("🚀 Process Jira File"):
        with st.spinner("Processing Jira export..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(jira_file.getvalue())
                tmp_path = tmp.name

            try:
                jira_tasks = process_jira_csv(tmp_path)
                if jira_tasks:
                    enriched_tasks = rules_engine.apply_priority(jira_tasks)
                    source_name = f"Jira Import - {jira_file.name}"
                    file_content = jira_file.getvalue().decode('utf-8')

                    if not db_handler.check_source_exists(file_content):
                        db_handler.insert_data(source_name, file_content, enriched_tasks)
                        st.success(f"Successfully imported and saved {len(enriched_tasks)} action items!")
                    else:
                        st.warning("This Jira file has already been imported.")
                else:
                    st.warning("No new tasks assigned to you were found in this file.")
            except Exception as e:
                st.error(f"An error occurred while processing the Jira file: {e}")
                log.error(f"Failed to process Jira file: {e}")
            finally:
                os.remove(tmp_path)
