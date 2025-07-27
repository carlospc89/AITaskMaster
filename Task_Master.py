# Task_Master.py
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

# You can keep this initialization here to ensure services are ready for other pages
@st.cache_resource
def init_services():
    log.info("Initializing services...")
    # This ensures the DB is initialized once and shared across pages
    db_handler = DatabaseHandler()
    # You might need to initialize other services here if they are shared
    # across pages via session_state, but for now, the DB is the most critical.
    return db_handler

db = init_services()

if "model_name" not in st.session_state:
    st.session_state.model_name = os.getenv("OLLAMA_MODEL", "mistral")

st.caption(f"Using model: {st.session_state.model_name}")