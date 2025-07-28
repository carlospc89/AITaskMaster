import streamlit as st
import pandas as pd
import json
from task_assistant.services import initialize_services
from task_assistant.prompts import rag_task_breakdown_prompt  # Use the new RAG prompt
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent
vector_store = st.session_state.vector_store
rules_engine = st.session_state.rules_engine

st.set_page_config(page_title="AI Task Breakdown", page_icon="🧠", layout="wide")

# --- Page Content ---
st.subheader("🧠 AI-Powered Task Breakdown (with RAG)")
st.info(
    "Select an existing task, and the AI will use the context from your past notes to break it down into relevant sub-tasks.")

# --- Task Selection ---
all_tasks_df = db_handler.get_all_action_items_as_df()

if not all_tasks_df.empty:
    # Create a list of task descriptions for the selectbox
    task_options = all_tasks_df['task_description'].tolist()
    selected_task = st.selectbox("Select a task to break down:", task_options)

    if st.button("✨ Break Down Task", type="primary"):
        if selected_task:
            with st.spinner("🤖 AI is searching your notes and planning..."):
                try:
                    # 1. RAG - Retrieve Context
                    retrieved_context = vector_store.search(selected_task, k=3)
                    context_str = "\n\n---\n\n".join(retrieved_context)
                    if not context_str:
                        context_str = "No relevant context found in past notes."

                    # Display the context found
                    with st.expander("See context found by RAG"):
                        st.text(context_str)

                    # 2. RAG - Generate
                    formatted_prompt = rag_task_breakdown_prompt.format(goal=selected_task, context=context_str)
                    result = agent.model.invoke(formatted_prompt)
                    raw_response = result.content
                    log.info(f"RAG Breakdown Raw Response: {raw_response}")

                    start_index = raw_response.find('[')
                    end_index = raw_response.rfind(']')

                    if start_index != -1 and end_index != -1:
                        json_str = raw_response[start_index: end_index + 1].strip()
                        tasks = json.loads(json_str)
                        st.session_state.tasks_to_review = tasks
                    else:
                        st.error("The AI returned an invalid response.")

                except Exception as e:
                    log.error(f"Failed during RAG task breakdown: {e}", exc_info=True)
                    st.error(f"An error occurred during breakdown: {e}")
        else:
            st.warning("Please select a task.")
else:
    st.warning("No tasks found in the database. Add some tasks first to use this feature.")

# --- Review and Save Section ---
if "tasks_to_review" in st.session_state and st.session_state.tasks_to_review:
    st.markdown("---")
    st.subheader("Review and Save Sub-Tasks")
    edited_tasks_df = st.data_editor(
        pd.DataFrame(st.session_state.tasks_to_review),
        num_rows="dynamic",
        key="review_editor"
    )

    if st.button("💾 Save to My Tasks"):
        with st.spinner("Saving..."):
            tasks_to_save = edited_tasks_df.to_dict(orient="records")

            for task in tasks_to_save:
                if 'task' in task:
                    task['task_description'] = task.pop('task')

            source_name = f"AI RAG Breakdown: {selected_task[:30]}..."
            content_to_hash = json.dumps(tasks_to_save)
            enriched_tasks = rules_engine.apply_priority(tasks_to_save)

            db_handler.insert_data(source_name, content_to_hash, enriched_tasks)
            st.success(f"Successfully saved {len(enriched_tasks)} new tasks!")
            del st.session_state.tasks_to_review