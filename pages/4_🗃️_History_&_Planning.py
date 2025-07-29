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
st.info(
    "Here you can triage tasks without a due date, or filter, edit, and set dependencies for your scheduled tasks below.")

full_df = db_handler.get_all_action_items_as_df()

if full_df.empty:
    st.warning("No tasks found in the database. Add some tasks from the sidebar pages to get started!")
    st.stop()

full_df = sanitize_df_for_streamlit(full_df)

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

# ... (Filtering controls and logic remain the same)

filtered_df = tasks_with_due_date.copy()
# ... (Filtering logic is the same)

st.divider()

# --- THIS IS THE CORRECTED LOGIC ---

# 1. Create a list of user-friendly strings for the dropdown options
dependency_options = ["—"] + [f"Task {row['id']}: {row['task_description'][:50]}..." for _, row in full_df.iterrows()]

# 2. Create a mapping from the friendly string back to the ID for saving
desc_to_id_map = {"—": None}
for _, row in full_df.iterrows():
    desc_to_id_map[f"Task {row['id']}: {row['task_description'][:50]}..."] = row['id']

# 3. We need to pre-convert the 'depends_on_id' into the string format for display
id_to_desc_map = {v: k for k, v in desc_to_id_map.items()}
display_df = filtered_df.copy()
display_df['depends_on_id'] = display_df['depends_on_id'].map(id_to_desc_map).fillna("—")

st.session_state.df_for_editing = display_df.reset_index(drop=True)

edited_df = st.data_editor(
    st.session_state.df_for_editing,
    num_rows="dynamic",
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "task_description": st.column_config.TextColumn("Task", width="large"),
        "depends_on_id": st.column_config.SelectboxColumn(
            "Depends On",
            help="Select the task that must be completed before this one.",
            options=dependency_options
        ),
        # ... (other columns are the same)
    },
    column_order=("id", "task_description", "depends_on_id", "status", "priority", "due_date", "project", "created_at"),
    key="data_editor"
)

if st.button("💾 Save Changes"):
    try:
        edited_rows = st.session_state["data_editor"].get("edited_rows", {})
        if edited_rows:
            updates = []
            for row_index, changed_data in edited_rows.items():
                # Get the original ID from the unfiltered, original dataframe
                original_id = filtered_df.reset_index(drop=True).iloc[row_index]['id']

                # If the dependency was changed, convert the string back to an ID
                if 'depends_on_id' in changed_data:
                    changed_data['depends_on_id'] = desc_to_id_map.get(changed_data['depends_on_id'])

                db_handler.update_action_item(original_id, changed_data)
                updates.append(original_id)

            if updates:
                st.toast(f"Updated {len(updates)} task(s).")

        # ... (deletion logic remains the same)

        if not edited_rows:  # Simplified condition
            st.toast("No changes to save.")

        st.rerun()

    except Exception as e:
        log.error(f"CRITICAL ERROR in 'Save Changes' block: {e}", exc_info=True)
        st.error(f"An error occurred while saving changes: {e}")
