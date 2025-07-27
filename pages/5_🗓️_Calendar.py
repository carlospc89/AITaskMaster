# pages/5_🗓️_Calendar.py
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log
st.set_page_config(layout="wide")

# --- Initialization ---
def init_calendar_services():
    db_handler = DatabaseHandler()
    return db_handler


db_handler = init_calendar_services()


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
st.subheader("🗓️ Task Calendar")
st.info("Click on any task in the calendar to see more details appear on the right.")

if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

# --- Define the column layout ---
main_col, details_col = st.columns([2, 1], gap="large")

# --- Calendar Logic (now inside the main column) ---
with main_col:
    calendar_df = db_handler.get_all_action_items_as_df()
    calendar_df = sanitize_df_for_streamlit(calendar_df)
    df_filtered = calendar_df.dropna(subset=['due_date'])

    if not df_filtered.empty:
        calendar_events = []
        for _, row in df_filtered.iterrows():
            try:
                date_str = row['due_date'].strftime('%Y-%m-%d')
                calendar_events.append({
                    "title": f"{row['priority']} - {row['task_description']}",
                    "start": date_str,
                    "end": date_str,
                    "allDay": True,
                    "extendedProps": {
                        "id": row['id'],
                        "description": row['task_description'],
                        "project": row.get('project', 'N/A'),
                        "status": row.get('status', 'N/A'),
                        "priority": row.get('priority', 'N/A')
                    }
                })
            except Exception as e:
                log.warning(f"Could not format date for calendar event: {row['id']}. Error: {e}")

        if calendar_events:
            clicked_event = calendar(
                events=calendar_events,
                options={
                    "headerToolbar": {"left": "prev,next today", "center": "title",
                                      "right": "dayGridMonth,timeGridWeek,timeGridDay"},
                    "height": "800px",
                },
                key="calendar"
            )

            if clicked_event and clicked_event.get("eventClick"):
                event_data = clicked_event["eventClick"].get("event", {})
                new_details = event_data.get("extendedProps", {})
                # Only update and rerun if the clicked event is different from the one stored
                if st.session_state.selected_event_details != new_details:
                    st.session_state.selected_event_details = new_details
                    st.rerun()
        else:
            st.warning("Could not generate any calendar events.")
    else:
        st.warning("No tasks with valid due dates were found.")

# --- Details Pane Logic (now inside the side column) ---
with details_col:
    if st.session_state.selected_event_details:
        props = st.session_state.selected_event_details
        task_id = props.get('id', 'unknown')

        st.subheader("Task Details")

        # THIS IS THE FIX: We use a key that is unique to the task being displayed.
        # When the task_id changes, Streamlit knows it must create a new container.
        with st.container(border=True, key=f"details_container_{task_id}"):
            st.markdown(f"##### {props.get('priority', '')} {props.get('description', 'No description')}")

            st.markdown(f"**Project:** `{props.get('project', 'N/A')}`")

            status_options = ["To Do", "In Progress", "Done", "Blocked"]
            current_status = props.get('status', 'To Do')
            try:
                current_status_index = status_options.index(current_status)
            except ValueError:
                current_status_index = 0

            new_status = st.selectbox(
                "**Status:**",
                options=status_options,
                index=current_status_index,
                key=f"status_selectbox_{task_id}"
            )

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Update Status", key=f"update_btn_{task_id}"):
                    if new_status != current_status:
                        db_handler.update_action_item(task_id, {'status': new_status})
                        st.toast(f"Task {task_id} status updated to '{new_status}'!")
                        st.session_state.selected_event_details = None
                        st.rerun()
                    else:
                        st.toast("No change in status.")

            with col2:
                if st.button("Hide Details", key=f"hide_btn_{task_id}"):
                    st.session_state.selected_event_details = None
                    st.rerun()
    else:
        st.info("Click an event on the calendar to see its details here.")