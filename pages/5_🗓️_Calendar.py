# pages/5_🗓️_Calendar.py
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from task_assistant.database_handler import DatabaseHandler
from task_assistant.logger_config import log


# --- Initialization ---
@st.cache_resource
def init_calendar_services():
    db_handler = DatabaseHandler()
    return db_handler


db_handler = init_calendar_services()


def sanitize_df_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a DataFrame to prevent Arrow serialization errors in Streamlit.
    """
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
st.info("This calendar shows all your tasks that have a specific due date.")

calendar_df = db_handler.get_all_action_items_as_df()
# THIS IS THE FIX: Sanitize the DataFrame immediately after loading it
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
                "extendedProps": {"project": row.get('project'), "status": row.get('status')}
            })
        except Exception as e:
            log.warning(f"Could not format date for calendar event: {row['id']}. Error: {e}")

    if calendar_events:
        calendar_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title",
                              "right": "dayGridMonth,timeGridWeek,timeGridDay"},
            "height": "auto",
        }
        calendar(events=calendar_events, options=calendar_options)
    else:
        st.warning("Found tasks with due dates, but could not format them for the calendar.")
else:
    st.warning("No tasks with valid due dates to display on the calendar.")