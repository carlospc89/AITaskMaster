# pages/8_📚_Context_Manager.py
import streamlit as st
import os
import tempfile

from task_assistant.services import initialize_services
from task_assistant.utils import normalize_text
from task_assistant.file_handler import read_file
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
vector_store = st.session_state.vector_store

st.set_page_config(page_title="Context Manager", page_icon="📚", layout="wide")


# --- Helper Function ---
def add_to_context(content: str, source_name: str):
    """
    Adds document content directly to the vector store without creating tasks.
    """
    normalized_content = normalize_text(content)

    # We use a simplified check here to avoid inserting duplicate context
    # Note: This doesn't use the source_documents table, so re-adding is possible
    # but harmless. A more advanced version could also check the hash.
    with st.spinner("📄 Indexing document for AI memory..."):
        try:
            vector_store.add_document(normalized_content)
            st.success(f"Successfully added `{source_name}` to the AI's contextual memory!")
            st.balloons()
        except Exception as e:
            st.error(f"An error occurred while adding context: {e}")
            log.error(f"Error in Context Manager: {e}", exc_info=True)


# --- Page Content ---
st.markdown("# 📚 Context Manager")
st.info(
    "Upload documents here to add them to the AI's long-term memory. This is ideal for background information, reports, or research that you want the AI to reference later when breaking down tasks. No action items will be created from these files.")

uploaded_file = st.file_uploader("Choose a file to add to the context", type=['txt', 'docx', 'pdf'],
                                 key="context_uploader")

if uploaded_file is not None:
    st.write(f"File uploaded: `{uploaded_file.name}`")
    if st.button("🧠 Add to AI Memory"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            file_content = read_file(tmp_path)
            add_to_context(file_content, uploaded_file.name)
        finally:
            os.remove(tmp_path)
