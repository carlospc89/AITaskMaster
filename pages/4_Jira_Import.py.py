# pages/4_Jira_Import.py
import streamlit as st
import os
import tempfile

# We need to re-import all necessary components for this page
from task_assistant.database_handler import DatabaseHandler
from task_assistant.rules_engine import RulesEngine
from task_assistant.jira_handler import process_jira_csv  # Specific to this page
from task_assistant.logger_config import log


# --- Initialization ---
@st.cache_resource
def init_page_services():
    """Initializes services needed for this specific page."""
    log.info("Initializing services for Jira Import page...")
    db_handler = DatabaseHandler()
    rules_engine = RulesEngine()
    return db_handler, rules_engine


db_handler, rules_engine = init_page_services()

# --- Page Content ---
st.set_page_config(page_title="Jira Import", page_icon="🗂️")
st.markdown("# Import Action Items from Jira")
st.info(
    "Upload a CSV file exported from Jira. The app will find tasks assigned to the user defined in your .env file."
)

jira_file = st.file_uploader("Choose a Jira CSV file", type=['csv'])

if jira_file is not None:
    if st.button("🚀 Process Jira File"):
        with st.spinner("Processing Jira export..."):
            # Use a temporary file to safely read the content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(jira_file.getvalue())
                tmp_path = tmp.name

            try:
                jira_tasks = process_jira_csv(tmp_path)
                if jira_tasks:
                    enriched_tasks = rules_engine.apply_priority(jira_tasks)
                    source_name = f"Jira Import - {jira_file.name}"

                    # Read file content for hashing
                    file_content = jira_file.getvalue().decode('utf-8')

                    if not db_handler.check_source_exists(file_content):
                        db_handler.insert_data(source_name, file_content, enriched_tasks)
                        st.success(f"Successfully imported and saved {len(enriched_tasks)} action items!")
                        st.balloons()
                    else:
                        st.warning("This Jira file has already been imported.")
                else:
                    st.warning("No new tasks assigned to you were found in this file.")
            except Exception as e:
                st.error(f"An error occurred while processing the Jira file: {e}")
                log.error(f"Failed to process Jira file: {e}")
            finally:
                # Clean up the temporary file
                os.remove(tmp_path)