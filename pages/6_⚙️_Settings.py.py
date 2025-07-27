# pages/6_⚙️_Settings.py
import streamlit as st
from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log

# --- Initialization ---
def init_page_services():
    """Initializes services needed for this specific page."""
    log.info("Initializing services for Settings page...")
    db_handler = DatabaseHandler()
    return db_handler

db_handler = init_page_services()

# --- Page Content ---
st.set_page_config(page_title="Settings", page_icon="⚙️")
st.markdown("# Application Settings")

st.markdown("---")
st.error("🚨 **Danger Zone** 🚨")
st.warning(
    "This action will permanently delete all processed documents and action items from the database. This cannot be undone."
)

if st.button("❌ Drop All Database Tables"):
    try:
        db_handler.drop_all_tables()
        st.success("All database tables have been successfully dropped.")
        # We use st.rerun() to refresh the state of all pages after deletion
        st.rerun()
    except Exception as e:
        st.error(f"An error occurred while dropping tables: {e}")
        log.error(f"Failed to drop tables: {e}")