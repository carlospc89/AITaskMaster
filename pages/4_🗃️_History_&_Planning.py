# pages/4_🗃️_History_&_Planning.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from task_assistant.services import initialize_services
from task_assistant.logger_config import log

# --- Initialization and Service Retrieval ---
initialize_services()
db_handler = st.session_state.db_handler

st.set_page_config(
    page_title="History & Planning",
    page_icon="🗃️",
    layout="wide"
)


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
st.info("Here you can triage tasks that need a due date, or filter and edit your scheduled tasks below.")

full_df = db_handler.get_all_action_items_as_df()

if full_df.empty:
    st.warning("No tasks found in the database. Add some tasks from the sidebar pages to get started!")
    st.stop()

full_df = sanitize_df_for_streamlit(full_df)

# --- Split the DataFrame into two sections ---
tasks_with_due_date = full_df.dropna(subset=['due_date'])
tasks_without_due_date = full_df[full_df['due_date'].isna()]

# --- Section for Tasks without a Due Date ---
st.markdown("---")
with st.expander(f"**🗓️ Triage Tasks without a Due Date ({len(tasks_without_due_date)})**", expanded=True):
    if not tasks_without_due_date.empty:
        for _, row in tasks_without_due_date.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"- {row['task_description']}")
            with col2:
                new_date = st.date_input("Assign Due Date", key=f"date_assign_{row['id']}", value=None)
            with col3:
                st.write("")
                st.write("")
                if st.button("Save Date", key=f"save_date_{row['id']}"):
                    if new_date:
                        db_handler.update_action_item(row['id'], {'due_date': new_date})
                        st.toast(f"Due date added for task {row['id']}!")
                        st.rerun()
                    else:
                        st.warning("Please select a date first.")
    else:
        st.write("All tasks have been assigned a due date. Great job!")

# --- Main Data Grid for Scheduled Tasks ---
st.markdown("---")
st.markdown("#### 🔎 Filter and Search Scheduled Tasks")

filter_cols = st.columns(5)
with filter_cols[0]:
    search_query = st.text_input("Search", placeholder="Filter by keyword...")
with filter_cols[1]:
    project_list = ["All"] + sorted(tasks_with_due_date['project'].dropna().unique().tolist())
    selected_project = st.selectbox("Project", project_list)
with filter_cols[2]:
    priority_list = ["All"] + sorted(tasks_with_due_date['priority'].dropna().unique().tolist())
    selected_priority = st.selectbox("Priority", priority_list)
with filter_cols[3]:
    status_list = ["All"] + sorted(tasks_with_due_date['status'].dropna().unique().tolist())
    selected_status = st.selectbox("Status", status_list)
with filter_cols[4]:
    date_range = st.date_input(
        "Filter by Due Date",
        value=(datetime.now().date() - timedelta(days=30), datetime.now().date() + timedelta(days=30)),
        key="date_range_picker"
    )

# Apply filters to the DataFrame that already has due dates
filtered_df = tasks_with_due_date.copy()
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