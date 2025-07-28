import streamlit as st
from task_assistant.services import initialize_services
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

# --- Page Content ---
st.markdown("# Application Settings")
st.markdown("---")
st.error("🚨 **Danger Zone** 🚨")
st.warning("This action will permanently delete all data from the database. This cannot be undone.")

if st.button("❌ Drop All Database Tables"):
    try:
        db_handler.drop_all_tables()
        st.success("All database tables have been successfully dropped.")
        st.rerun()
    except Exception as e:
        st.error(f"An error occurred while dropping tables: {e}")
        log.error(f"Failed to drop tables: {e}")
