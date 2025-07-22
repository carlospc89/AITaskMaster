import streamlit as st
import json
import os
from datetime import datetime, timedelta

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

def main():
    st.set_page_config(page_title="Task Manager", page_icon="📋", layout="wide")
    st.title("📋 Task Manager")
    
    # Simple tabs
    tab1, tab2 = st.tabs(["Dashboard", "Add Task"])
    
    with tab1:
        st.header("Dashboard")
        st.write(f"Total tasks: {len(st.session_state.tasks)}")
        
        if st.session_state.tasks:
            for i, task in enumerate(st.session_state.tasks):
                st.write(f"{i+1}. {task['title']} - {task['status']}")
        else:
            st.write("No tasks yet")
    
    with tab2:
        st.header("Add Task")
        
        with st.form("add_task"):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            if st.form_submit_button("Add Task"):
                if title:
                    new_task = {
                        'id': len(st.session_state.tasks) + 1,
                        'title': title,
                        'description': description,
                        'priority': priority,
                        'status': 'Not Started',
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.session_state.tasks.append(new_task)
                    st.success(f"Task '{title}' added successfully!")
                else:
                    st.error("Please enter a task title")

if __name__ == "__main__":
    main()