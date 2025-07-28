# pages/6_🧠_AI_Task_Breakdown.py
import streamlit as st
import pandas as pd
import os
import json

from task_assistant.database_handler import DatabaseHandler
from task_assistant.agent import Agent
from task_assistant.prompts import task_breakdown_prompt
from task_assistant.rules_engine import RulesEngine
from task_assistant.logger_config import log
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

st.set_page_config(page_title="AI Task Breakdown", page_icon="🧠", layout="wide")


# --- Initialization ---
@st.cache_resource
def init_page_services():
    db_handler = DatabaseHandler()
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    model = ChatOllama(model=model_name)
    # This agent instance is for a simple, one-off call
    agent = Agent(model, system="")
    rules_engine = RulesEngine()
    return db_handler, agent, rules_engine


db_handler, abot, rules_engine = init_page_services()

# --- Page Content ---
st.subheader("🧠 AI-Powered Task Breakdown")
st.info("Describe a large goal or project, and the AI will break it down into smaller, manageable tasks for you.")

goal_input = st.text_area("Enter your goal here:", height=150,
                          placeholder="e.g., Plan and execute a new marketing campaign for the Q4 product launch.")

if st.button("✨ Break Down Goal", type="primary"):
    if goal_input:
        with st.spinner("🤖 AI is planning..."):
            try:
                # We use a simple invoke call with the formatted prompt
                formatted_prompt = task_breakdown_prompt.format(goal=goal_input)
                result = abot.model.invoke(formatted_prompt)
                raw_response = result.content
                log.info(f"Task Breakdown Raw Response: {raw_response}")

                start_index = raw_response.find('[')
                end_index = raw_response.rfind(']')

                if start_index != -1 and end_index != -1:
                    json_str = raw_response[start_index: end_index + 1].strip()
                    tasks = json.loads(json_str)

                    # Store the generated tasks in session state for review
                    st.session_state.tasks_to_review = tasks
                else:
                    st.error("The AI returned an invalid response. Could not find a valid JSON block.")

            except Exception as e:
                log.error(f"Failed during AI task breakdown: {e}", exc_info=True)
                st.error(f"An error occurred during breakdown: {e}")
    else:
        st.warning("Please enter a goal to break down.")

# --- Review and Save Section ---
if "tasks_to_review" in st.session_state and st.session_state.tasks_to_review:
    st.markdown("---")
    st.subheader("Review and Save Sub-Tasks")
    st.write("Here are the suggested sub-tasks. You can edit or remove them before saving.")

    # Use the data editor to allow for final tweaks
    edited_tasks_df = st.data_editor(
        pd.DataFrame(st.session_state.tasks_to_review),
        num_rows="dynamic",
        key="review_editor"
    )

    if st.button("💾 Save to My Tasks"):
        with st.spinner("Saving..."):
            tasks_to_save = edited_tasks_df.to_dict(orient="records")

            # We need to rename the 'task' column to 'task_description' for the DB
            for task in tasks_to_save:
                if 'task' in task:
                    task['task_description'] = task.pop('task')

            # We reuse the insert_data function, but the source is the AI itself
            source_name = f"AI Breakdown: {goal_input[:30]}..."
            content_to_hash = json.dumps(tasks_to_save)

            enriched_tasks = rules_engine.apply_priority(tasks_to_save)

            db_handler.insert_data(source_name, content_to_hash, enriched_tasks)
            st.success(f"Successfully saved {len(enriched_tasks)} new tasks!")
            st.balloons()

            # Clear the state to hide the review section
            del st.session_state.tasks_to_review
