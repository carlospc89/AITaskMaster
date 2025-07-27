# app.py
import streamlit as st
import os
from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log

st.set_page_config(
    page_title="Task Master AI - Home",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Welcome to Task Master AI!")
st.markdown("Your AI-Powered Action Item Extractor and Planner.")

st.info(
    """
    Use the navigation sidebar on the left to access the different tools:

    - **✍️ Paste Text:** Paste notes to extract action items.
    - **📂 Upload File:** Upload documents (`.txt`, `.pdf`, `.docx`) for analysis.
    - **🗃️ History & Planning:** View, edit, and manage all your tasks.
    - **Jira Import:** Import tasks directly from a Jira CSV export.
    - **🗓️ Calendar:** Visualize your task deadlines.
    - **⚙️ Settings:** Manage application settings and data.
    """
)

# This initialization ensures the DB is ready for other pages.
# The decorator was removed to prevent caching issues.
def init_services():
    log.info("Initializing services for the main app...")
    db_handler = DatabaseHandler()
    return db_handler

db = init_services()

if "model_name" not in st.session_state:
    st.session_state.model_name = os.getenv("OLLAMA_MODEL", "mistral")

st.caption(f"Using model: {st.session_state.model_name}")

# THIS IS THE NEW LINE TO DISPLAY THE STREAMLIT VERSION
st.caption(f"Streamlit Version: {st.__version__}")
