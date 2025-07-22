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
    
    # Initialize tab tracking for auto-refresh
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "dashboard"
    if "last_task_count" not in st.session_state:
        st.session_state.last_task_count = 0
    
    # Simple tabs with automatic refresh detection
    tab1, tab2 = st.tabs(["🏠 Dashboard", "➕ Add Task"])
    
    with tab1:
        # Auto-refresh when switching to dashboard and task count changed
        current_task_count = len(st.session_state.tasks)
        if st.session_state.active_tab != "dashboard" and current_task_count != st.session_state.last_task_count:
            st.session_state.last_task_count = current_task_count
            st.rerun()
        
        st.session_state.active_tab = "dashboard"
        
        st.header("🏠 Dashboard")
        
        # Auto-refresh indicator
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric("Total Tasks", len(st.session_state.tasks))
        with col2:
            completed = len([t for t in st.session_state.tasks if t['status'] == 'Completed'])
            st.metric("Completed", completed)
        with col3:
            if st.button("🔄 Refresh", help="Refresh dashboard"):
                st.rerun()
        
        if st.session_state.tasks:
            st.success(f"Found {len(st.session_state.tasks)} tasks")
            
            # Display tasks in a nice format
            for i, task in enumerate(st.session_state.tasks):
                with st.expander(f"📋 {task['title']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**Description:** {task['description']}")
                    with col2:
                        st.write(f"**Priority:** {task['priority']}")
                    with col3:
                        st.write(f"**Status:** {task['status']}")
                    st.write(f"**Created:** {task['created_date']}")
        else:
            st.info("No tasks yet. Go to Add Task tab to create one.")
            
        # Add test task button for debugging
        if st.button("Add Test Task"):
            test_task = {
                'id': len(st.session_state.tasks) + 1,
                'title': f'Test Task #{len(st.session_state.tasks) + 1}',
                'description': 'This is a test task created from dashboard',
                'priority': 'Medium',
                'status': 'Not Started',
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            st.session_state.tasks.append(test_task)
            st.success("Test task added!")
            st.rerun()
    
    with tab2:
        # Track when add task tab is accessed
        st.session_state.active_tab = "add_task"
        
        st.header("Add Task")
        
        with st.form("add_task"):
            title = st.text_input("Task Title", placeholder="Enter a clear task title...")
            description = st.text_area("Description", placeholder="Add details about this task...")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
            
            if st.form_submit_button("✅ Add Task"):
                if title:
                    new_task = {
                        'id': len(st.session_state.tasks) + 1,
                        'title': title,
                        'description': description,
                        'priority': priority,
                        'status': status,
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.session_state.tasks.append(new_task)
                    st.success(f"✅ Task '{title}' added successfully!")
                    st.balloons()  # Visual feedback
                    
                    # Auto-switch to dashboard to show the new task
                    st.info("💡 Switch to Dashboard tab to see your new task!")
                else:
                    st.error("Please enter a task title")

if __name__ == "__main__":
    main()