# pages/3_🗃️_History_&_Planning.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log

# Set the page to wide mode for a better layout
st.set_page_config(
    page_title="History & Planning",
    page_icon="🗃️",
    layout="wide"
)


# --- Initialization ---
def init_page_services():
    db_handler = DatabaseHandler()
    return db_handler


db_handler = init_page_services()


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
st.subheader("Action Item History & Planning")
st.info("Here you can view, edit, delete, and filter all of your tasks.")

st.markdown("#### 🔎 Filter and Search Tasks")

full_df = db_handler.get_all_action_items_as_df()
full_df = sanitize_df_for_streamlit(full_df)

# --- Filter Controls ---
filter_cols = st.columns(5)
with filter_cols[0]:
    # THIS IS THE FIX: We give the text input a simple label for alignment.
    search_query = st.text_input("Search", placeholder="Filter by keyword...")
with filter_cols[1]:
    project_list = ["All"] + sorted(full_df['project'].dropna().unique().tolist())
    selected_project = st.selectbox("Project", project_list)
with filter_cols[2]:
    priority_list = ["All"] + sorted(full_df['priority'].dropna().unique().tolist())
    selected_priority = st.selectbox("Priority", priority_list)
with filter_cols[3]:
    status_list = ["All"] + sorted(full_df['status'].dropna().unique().tolist())
    selected_status = st.selectbox("Status", status_list)
with filter_cols[4]:
    date_range = st.date_input(
        "Filter by Due Date",
        value=(datetime.now().date() - timedelta(days=30), datetime.now().date() + timedelta(days=30)),
        key="date_range_picker"
    )

# --- Apply Filters ---
filtered_df = full_df.copy()
if search_query:
    filtered_df = filtered_df[filtered_df['task_description'].str.contains(search_query, case=False, na=False)]
if selected_project != "All":
    filtered_df = filtered_df[filtered_df['project'] == selected_project]
if selected_priority != "All":
    filtered_df = filtered_df[filtered_df['priority'] == selected_priority]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df_dates = pd.to_datetime(filtered_df['due_date'], errors='coerce').dt.date
    filtered_df = filtered_df[
        (filtered_df_dates >= start_date.date()) &
        (filtered_df_dates <= end_date.date())
        ]

st.divider()

st.session_state.df_for_editing = filtered_df.reset_index(drop=True)

edited_df = st.data_editor(
    st.session_state.df_for_editing,
    num_rows="dynamic",
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "task_description": st.column_config.TextColumn("Task", width="large"),
        "due_date": st.column_config.DateColumn("Due Date", format="DD-MM-YYYY"),
        "project": st.column_config.TextColumn("Project"),
        "priority": st.column_config.SelectboxColumn("Priority", options=["🔴 High", "🟠 Medium", "🟢 Low", "⚪ Normal"]),
        "status": st.column_config.SelectboxColumn("Status", options=["To Do", "In Progress", "Done", "Blocked"]),
        "created_at": st.column_config.DateColumn("Created On", format="DD-MM-YYYY", disabled=True)
    },
    key="data_editor"
)

if st.button("💾 Save Changes"):
    try:
        edited_rows = st.session_state["data_editor"].get("edited_rows", {})
        if edited_rows:
            updates = []
            for row_index, changed_data in edited_rows.items():
                item_id = st.session_state.df_for_editing.iloc[row_index]['id']
                db_handler.update_action_item(item_id, changed_data)
                updates.append(item_id)
            if updates:
                st.toast(f"Updated {len(updates)} task(s).")

        original_ids = set(st.session_state.df_for_editing['id'])
        current_ids = set(edited_df['id'])
        deleted_ids = list(original_ids - current_ids)
        if deleted_ids:
            db_handler.delete_action_items(deleted_ids)
            st.toast(f"Deleted {len(deleted_ids)} task(s).")

        if not edited_rows and not deleted_ids:
            st.toast("No changes to save.")

        st.rerun()

    except Exception as e:
        log.error(f"CRITICAL ERROR in 'Save Changes' block: {e}", exc_info=True)
        st.error(f"An error occurred while saving changes: {e}")
