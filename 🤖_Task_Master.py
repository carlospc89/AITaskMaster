# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, time
import altair as alt

# Import the new centralized initializer
from task_assistant.services import initialize_services
from task_assistant.logger_config import log
from task_assistant.prompts import prioritization_prompt

# --- Initialization ---
# This single function call will set up everything for the entire app session
initialize_services()

# --- Page Content ---
st.set_page_config(
    page_title="Task Master AI - Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Retrieve services from session_state ---
# This is now the standard way to access shared services on any page
db_handler = st.session_state.db_handler
abot = st.session_state.agent


def sanitize_df_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    """ A utility to prevent Streamlit's Arrow serialization errors """
    df_copy = df.copy()
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            continue
        if df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).fillna('')
        if "Int64" in str(df_copy[col].dtype):
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0).astype(int)
    return df_copy


st.title("📊 Task Dashboard")
st.markdown("Your AI-Powered Action Item Extractor and Planner.")

# --- "What should I do next?" feature ---
st.markdown("---")
if st.button("🤖 What should I do next?", type="primary"):
    with st.spinner("AI is thinking..."):
        all_tasks_df = db_handler.get_all_action_items_as_df()

        if not all_tasks_df.empty:
            all_tasks_df = sanitize_df_for_streamlit(all_tasks_df)
            active_tasks_df = all_tasks_df[all_tasks_df['status'] != 'Done']
            if not active_tasks_df.empty:
                tasks_json = active_tasks_df.to_json(orient="records")
                suggestion = abot.get_prioritization(tasks_json, prioritization_prompt)
                st.info(suggestion)
            else:
                st.warning("You have no active tasks to prioritize. Great job!")
        else:
            st.warning("No tasks found in the database to prioritize.")

# --- Data Loading and Graceful Handling of Empty State ---
full_df = db_handler.get_all_action_items_as_df()

if full_df.empty:
    st.info("👋 Welcome! Your task dashboard is ready. Add some tasks from the sidebar pages to get started.")
    st.stop()

# --- Dashboard Display ---
try:
    full_df = sanitize_df_for_streamlit(full_df)

    if 'status' in full_df.columns:
        active_tasks_df = full_df[full_df['status'] != 'Done'].copy()
    else:
        active_tasks_df = pd.DataFrame()

    today = pd.to_datetime(datetime.now().date())
    overdue_tasks = active_tasks_df[active_tasks_df['due_date'] < today]
    due_today_tasks = active_tasks_df[active_tasks_df['due_date'] == today]

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Tasks", len(active_tasks_df))
    col2.metric("Tasks Overdue", len(overdue_tasks), delta=f"{len(overdue_tasks)} urgent", delta_color="inverse")
    col3.metric("Tasks Due Today", len(due_today_tasks), delta=f"{len(due_today_tasks)} today", delta_color="off")

    st.markdown("---")
    list_col1, list_col2 = st.columns(2, gap="large")

    with list_col1:
        with st.expander(f"**🔴 Overdue Tasks ({len(overdue_tasks)})**", expanded=True):
            if not overdue_tasks.empty:
                for _, row in overdue_tasks.iterrows():
                    st.markdown(f"- **{row['task_description']}** (Due: {row['due_date'].strftime('%Y-%m-%d')})")
            else:
                st.write("No overdue tasks. Great job!")

    with list_col2:
        with st.expander(f"**🟠 Tasks Due Today ({len(due_today_tasks)})**", expanded=True):
            if not due_today_tasks.empty:
                for _, row in due_today_tasks.iterrows():
                    st.markdown(f"- **{row['task_description']}** (Project: {row['project']})")
            else:
                st.write("No tasks due today.")

    st.markdown("---")
    st.subheader("Tasks by Priority")

    if not active_tasks_df.empty and 'priority' in active_tasks_df.columns:
        priority_counts = active_tasks_df['priority'].value_counts().reset_index()
        priority_counts.columns = ['priority', 'count']

        chart = alt.Chart(priority_counts).mark_bar().encode(
            x=alt.X('priority', title='Priority', sort='-y'),
            y=alt.Y('count', title='Number of Tasks'),
            color=alt.Color('priority', legend=None),
            tooltip=['priority', 'count']
        ).properties(
            title='Distribution of Active Tasks by Priority'
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No active tasks to display in the chart.")

except Exception as e:
    st.error(f"An error occurred while building the dashboard: {e}")
    log.error(f"Dashboard error: {e}", exc_info=True)
