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
        
        # Debug information
        st.write(f"Session state contents: {st.session_state}")
        
        if st.session_state.tasks:
            st.success("Tasks found!")
            for i, task in enumerate(st.session_state.tasks):
                st.write(f"{i+1}. {task['title']} - {task['status']}")
        else:
            st.info("No tasks yet. Go to Add Task tab to create one.")
            
        # Add test task button for debugging
        if st.button("Add Test Task"):
            test_task = {
                'id': len(st.session_state.tasks) + 1,
                'title': 'Test Task',
                'description': 'This is a test task',
                'priority': 'Medium',
                'status': 'Not Started',
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            st.session_state.tasks.append(test_task)
            st.success("Test task added!")
            st.rerun()
    
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
                    st.write(f"Current tasks count: {len(st.session_state.tasks)}")
                    st.write(f"Latest task: {new_task}")
                else:
                    st.error("Please enter a task title")

if __name__ == "__main__":
    main()