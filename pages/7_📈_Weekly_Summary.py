# pages/7_📈_Weekly_Summary.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from task_assistant.services import initialize_services
from task_assistant.prompts import weekly_summary_prompt
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler
agent = st.session_state.agent

st.set_page_config(page_title="Weekly Summary", page_icon="📈", layout="wide")


# --- Helper Function ---
def sanitize_df_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            continue
        if df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).fillna('')
        if "Int64" in str(df_copy[col].dtype):
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0).astype(int)
    return df_copy


# --- Page Content ---
st.subheader("📈 AI-Powered Weekly Summary")
st.info("Click the button below to generate a strategic summary of your tasks due in the next 7 days.")

if st.button("🚀 Generate Weekly Report", type="primary"):
    all_tasks_df = db_handler.get_all_action_items_as_df()

    if all_tasks_df.empty:
        st.warning("No tasks found in the database. Add some tasks with due dates to generate a report.")
        st.stop()

    all_tasks_df = sanitize_df_for_streamlit(all_tasks_df)

    # Filter for tasks due in the next 7 days
    today = pd.to_datetime(datetime.now().date())
    next_week = today + timedelta(days=7)

    upcoming_tasks_df = all_tasks_df[
        (all_tasks_df['due_date'] >= today) &
        (all_tasks_df['due_date'] <= next_week) &
        (all_tasks_df['status'] != 'Done')
        ]

    if upcoming_tasks_df.empty:
        st.success("🎉 You have no tasks due in the next 7 days! Looks like a clear week ahead.")
        st.stop()

    with st.spinner("🤖 AI is analyzing your week..."):
        try:
            tasks_json = upcoming_tasks_df.to_json(orient="records")

            # Use the get_prioritization method, which is a simple, direct call to the model
            summary = agent.get_prioritization(tasks_json, weekly_summary_prompt)

            st.markdown("---")
            st.markdown(summary)

        except Exception as e:
            st.error(f"An error occurred while generating the summary: {e}")
            log.error(f"Failed to generate weekly summary: {e}", exc_info=True)
