import streamlit as st
import os
import tempfile
import json
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
from langchain_ollama.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

from task_assistant.agent import Agent
from task_assistant.prompts import task_master_prompt, prioritization_prompt
from task_assistant.file_handler import read_file
from task_assistant.utils import normalize_text
from task_assistant.rules_engine import RulesEngine
from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log

# --- App Configuration & Initializations ---
st.set_page_config(
    page_title="Task Master AI",
    page_icon="📝",
    layout="wide"
)


@st.cache_resource
def init_services():
    """Initializes all necessary services."""
    log.info("Initializing services...")
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    model = ChatOllama(model=model_name)
    agent = Agent(model, system=task_master_prompt)
    rules_engine = RulesEngine()
    db_handler = DatabaseHandler()
    st.session_state.model_name = model_name
    return agent, rules_engine, db_handler


abot, rules_engine, db_handler = init_services()


# --- Helper Function to Process Input ---
def process_and_display(content: str, source_name: str):
    """Processes content, stores it in the DB, and displays the result."""
    normalized_content = normalize_text(content)

    if db_handler.check_source_exists(normalized_content):
        st.warning(f"This content from '{source_name}' has already been processed. No new tasks were added.")
        return

    with st.spinner("🤖 AI is analyzing..."):
        try:
            result = abot.graph.invoke({"messages": [HumanMessage(content=normalized_content)]})
            raw_response = result["messages"][-1].content
            log.info(f"Raw AI Response: {raw_response}")

            start_index = raw_response.find('[')
            end_index = raw_response.rfind(']')
            if start_index == -1 or end_index == -1:
                st.error("The AI returned an invalid response. Please try again.")
                return
            tasks = json.loads(raw_response[start_index: end_index + 1])
            enriched_tasks = rules_engine.apply_priority(tasks)

            if enriched_tasks:
                db_handler.insert_data(source_name, normalized_content, enriched_tasks)
                st.success("Successfully extracted and saved action items!")

            st.divider()
            st.subheader("✅ Your Action Items")
            if not enriched_tasks:
                st.info("No action items were found.")
                return

            for task in enriched_tasks:
                project_name = f"**Project:** {task.get('project', 'N/A')} |" if task.get('project') else ""
                st.markdown(f"**Task:** {task.get('task', 'No description')}")
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{project_name} **Due:** `{task.get('due_date', 'N/A')}` | **Priority:** {task.get('priority', '⚪ Normal')}")

        except Exception as e:
            log.error(f"An unexpected error occurred during processing: {e}")
            st.error(f"An unexpected error occurred: {e}")


# --- UI Layout ---
st.title("📝 Task Master AI")
st.markdown("Your AI-Powered Action Item Extractor and Planner.")
if "model_name" in st.session_state: st.caption(f"Using model: {st.session_state.model_name}")

tab_list = ["✍️ Paste Text", "📂 Upload File", "🗃️ History & Planning", "Jira Import", "🗓️ Calendar", "⚙️ Settings"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_list)

with tab1:
    with st.form(key="text_input_form"):
        notes_input = st.text_area("Paste your meeting notes here:", height=250)
        submit_text = st.form_submit_button(label="✨ Extract from Text")
    if submit_text and notes_input:
        process_and_display(notes_input, "pasted_text")

with tab2:
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'docx', 'pdf'])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        try:
            file_content = read_file(tmp_path)
            process_and_display(file_content, uploaded_file.name)
        finally:
            os.remove(tmp_path)

with tab3:
    st.subheader("Action Item History & Planning")

    if st.button("🤖 What should I do next?"):
        with st.spinner("AI is thinking..."):
            all_tasks_df = db_handler.get_all_action_items_as_df()
            active_tasks_df = all_tasks_df[all_tasks_df['status'] != 'Done']
            if not active_tasks_df.empty:
                tasks_json = active_tasks_df.to_json(orient="records")
                suggestion = abot.get_prioritization(tasks_json, prioritization_prompt)
                st.info(suggestion)
            else:
                st.warning("There are no active tasks to prioritize.")

    st.divider()

    if 'edited_df' not in st.session_state or st.button("🔄 Refresh Table"):
        st.session_state.edited_df = db_handler.get_all_action_items_as_df()

    edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "task_description": st.column_config.TextColumn("Task", width="large"),
            "due_date": st.column_config.DateColumn(
                "Due Date",
                format="DD/MM/YYYY"
            ),
            "project": st.column_config.TextColumn("Project"),
            "priority": st.column_config.SelectboxColumn("Priority",
                                                         options=["🔴 High", "🟠 Medium", "🟢 Low", "⚪ Normal"]),
            "status": st.column_config.SelectboxColumn("Status", options=["To Do", "In Progress", "Done", "Blocked"]),
            "created_at": st.column_config.DateColumn(
                "Created On",
                format="DD/MM/YYYY",
                disabled=True
            )
        },
        key="data_editor"
    )

    if st.button("💾 Save Changes"):
        try:
            original_df = st.session_state.edited_df

            deleted_ids = list(set(original_df['id']) - set(edited_df['id']))
            if deleted_ids:
                db_handler.delete_action_items(deleted_ids)
                st.toast(f"Deleted {len(deleted_ids)} task(s).")

            updates = []
            for _, row in edited_df.iterrows():
                item_id = row['id']
                if pd.isna(item_id): continue

                original_row = original_df[original_df['id'] == item_id]
                if not original_row.empty and not row.equals(original_row.iloc[0]):
                    update_dict = row.to_dict()

                    if 'due_date' in update_dict and pd.notna(update_dict['due_date']):
                        update_dict['due_date'] = pd.to_datetime(update_dict['due_date']).strftime('%d/%m/%Y')
                    if 'created_at' in update_dict and pd.notna(update_dict['created_at']):
                        update_dict['created_at'] = pd.to_datetime(update_dict['created_at']).strftime('%d/%m/%Y')

                    db_handler.update_action_item(item_id, update_dict)
                    updates.append(item_id)

            if updates:
                st.toast(f"Updated {len(updates)} task(s).")
            if not deleted_ids and not updates:
                st.toast("No changes to save.")

            st.session_state.edited_df = db_handler.get_all_action_items_as_df()
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred while saving changes: {e}")
            log.error(f"Failed to save changes: {e}")

with tab4:
    st.subheader("Import Action Items from Jira")
    st.info(
        "Upload a CSV file exported from Jira. The app will find tasks assigned to the user defined in your .env file.")
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
                finally:
                    os.remove(tmp_path)

with tab5:
    st.subheader("🗓️ Task Calendar")
    st.info("This calendar shows all your tasks that have a specific due date.")

    if st.button("Refresh Calendar"):
        st.session_state.calendar_df = db_handler.get_all_action_items_as_df()

    if 'calendar_df' not in st.session_state:
        st.session_state.calendar_df = db_handler.get_all_action_items_as_df()

    if 'calendar_df' in st.session_state and not st.session_state.calendar_df.empty:
        df = st.session_state.calendar_df.copy()
        df_filtered = df.dropna(subset=['due_date'])


        # --- Helper to format tasks for the calendar ---
        def format_tasks_for_calendar(df):
            calendar_events = []
            for _, row in df.iterrows():
                event = {
                    "title": f"{row['priority']} - {row['task_description']}",
                    "start": row['due_date'].isoformat(),
                    "end": row['due_date'].isoformat(),
                    "allDay": True,
                    "extendedProps": {
                        "project": row['project'],
                        "status": row['status']
                    }
                }
                calendar_events.append(event)
            return calendar_events


        calendar_events = format_tasks_for_calendar(df_filtered)

        # --- Calendar Configuration ---
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay",
            },
            "initialView": "dayGridMonth",
            "editable": False,
            "height": "auto",  # Add this line to make the calendar fully visible
        }

        calendar(events=calendar_events, options=calendar_options)
    else:
        st.warning("No tasks with due dates found.")

with tab6:
    st.subheader("Application Settings")
    st.markdown("---")
    st.error("🚨 **Danger Zone** 🚨")
    st.warning(
        "This action will permanently delete all processed documents and action items from the database. This cannot be undone.")
    if st.button("❌ Drop All Database Tables"):
        db_handler.drop_all_tables()
        if 'edited_df' in st.session_state:
            del st.session_state['edited_df']
        if 'calendar_df' in st.session_state:
            del st.session_state['calendar_df']
        st.success("All data has been deleted. The database has been reset.")
        st.rerun()