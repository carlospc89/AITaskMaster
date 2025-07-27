# In task_assistant/jira_handler.py
import pandas as pd
import os
from .logger_config import log


def process_jira_csv(file_path: str) -> list[dict]:
    """
    Reads a Jira CSV export, filters for tasks assigned to the user,
    and maps the columns to our application's task format.
    """
    try:
        df = pd.read_csv(file_path)
        log.info(f"Successfully loaded Jira CSV from {file_path}")
    except Exception as e:
        log.error(f"Failed to read CSV file: {e}")
        return []

    jira_user = os.getenv("JIRA_USER_NAME")
    if not jira_user:
        log.warning("JIRA_USER_NAME not set in .env file. Cannot filter tasks.")
        return []

    user_tasks_df = df[df['Assignee'] == jira_user].copy()
    log.info(f"Found {len(user_tasks_df)} tasks assigned to {jira_user}.")

    status_mapping = {
        "to do": "To Do",
        "in progress": "In Progress",
        "done": "Done",
        "closed": "Done",
        "blocked": "Blocked",
    }

    tasks = []
    for _, row in user_tasks_df.iterrows():
        # MODIFIED: Changed strftime format to YYYY-MM-DD for consistency
        due_date = pd.to_datetime(row.get('Due date')).strftime('%Y-%m-%d') if pd.notna(row.get('Due date')) else None

        jira_status = row.get('Status', '').lower()
        app_status = status_mapping.get(jira_status, "To Do")

        tasks.append({
            "task": row.get('Summary'),
            "project": row.get('Project name'),
            "due_date": due_date,
            "status": app_status,
        })

    return tasks