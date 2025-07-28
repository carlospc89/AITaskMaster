import streamlit as st
import json
from task_assistant.services import initialize_services
from task_assistant.utils import normalize_text
from task_assistant.prompts import task_master_prompt
from langchain_core.messages import HumanMessage
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent
rules_engine = st.session_state.rules_engine

st.set_page_config(page_title="Paste Text", page_icon="✍️", layout="wide")

# --- Helper Function ---
def process_and_display(content: str, source_name: str):
    normalized_content = normalize_text(content)
    if db_handler.check_source_exists(normalized_content):
        st.warning(f"This content from '{source_name}' has already been processed.")
        return

    with st.spinner("🤖 AI is analyzing..."):
        try:
            # We now set the agent's system prompt right before the call
            agent.system = task_master_prompt
            result = agent.graph.invoke({"messages": [HumanMessage(content=normalized_content)]})
            raw_response = result["messages"][-1].content
            log.info(f"Raw AI Response: {raw_response}")

            start_index = raw_response.find('[')
            end_index = raw_response.rfind(']')

            if start_index != -1 and end_index != -1:
                json_str = raw_response[start_index : end_index + 1].strip()
                tasks = json.loads(json_str)
                enriched_tasks = rules_engine.apply_priority(tasks)

                if enriched_tasks:
                    db_handler.insert_data(source_name, content, enriched_tasks)
                    st.success(f"Successfully extracted and saved {len(enriched_tasks)} action items!")
                else:
                    st.info("No action items were found.")
            else:
                st.error("The AI returned an invalid response. Could not find a valid JSON block.")
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
