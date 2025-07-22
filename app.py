import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Simple in-memory storage that persists across tabs
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'delegations' not in st.session_state:
    st.session_state.delegations = []
if 'extracted_items' not in st.session_state:
    st.session_state.extracted_items = []

def save_tasks_to_file():
    """Save tasks to JSON file for persistence"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/tasks.json", "w") as f:
            json.dump(st.session_state.tasks, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving tasks: {e}")
        return False

def load_tasks_from_file():
    """Load tasks from JSON file"""
    try:
        if os.path.exists("data/tasks.json"):
            with open("data/tasks.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading tasks: {e}")
    return []

def generate_task_id():
    """Generate next task ID"""
    if not st.session_state.tasks:
        return 1
    return max([task.get('id', 0) for task in st.session_state.tasks]) + 1

def extract_action_items_simple(text):
    """Simple text-based extraction without AI for testing"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    items = []
    
    for i, line in enumerate(lines[:5]):  # Limit to 5 items
        if len(line) > 10:  # Skip very short lines
            items.append({
                'title': f"Complete {line[:50]}..." if len(line) > 50 else f"Complete {line}",
                'description': line,
                'priority': 'Medium',
                'category': 'Other',
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'estimated_hours': 2.0
            })
    
    return items

def main():
    st.set_page_config(
        page_title="Task Manager",
        page_icon="📋",
        layout="wide"
    )
    
    # Load tasks from file on startup
    if not st.session_state.tasks:
        st.session_state.tasks = load_tasks_from_file()
    
    st.title("📋 Simple Task Manager")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Extract Tasks", "All Tasks"])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_extraction()
    
    with tab3:
        show_all_tasks()

def show_dashboard():
    st.header("Dashboard")
    
    if st.session_state.tasks:
        total_tasks = len(st.session_state.tasks)
        completed_tasks = len([t for t in st.session_state.tasks if t.get('status') == 'Completed'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tasks", total_tasks)
        with col2:
            st.metric("Completed", completed_tasks)
        with col3:
            st.metric("Remaining", total_tasks - completed_tasks)
        
        # Recent tasks
        st.subheader("Recent Tasks")
        for task in st.session_state.tasks[-5:]:
            st.write(f"• {task['title']} - {task.get('status', 'Not Started')}")
    else:
        st.info("No tasks yet. Go to 'Extract Tasks' to add some.")
        
        # Add sample task button
        if st.button("Add Sample Task"):
            sample_task = {
                'id': generate_task_id(),
                'title': 'Review quarterly planning documents',
                'description': 'Review and provide feedback on Q4 planning',
                'priority': 'High',
                'status': 'Not Started',
                'category': 'Strategic',
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'estimated_hours': 3.0,
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            st.session_state.tasks.append(sample_task)
            save_tasks_to_file()
            st.success("Sample task added!")
            st.rerun()

def show_extraction():
    st.header("Extract Action Items")
    
    text_input = st.text_area(
        "Meeting Notes:",
        height=200,
        placeholder="Paste your meeting notes here..."
    )
    
    if st.button("Extract Action Items", type="primary"):
        if text_input.strip():
            # Extract items
            items = extract_action_items_simple(text_input)
            st.session_state.extracted_items = items
            
            if items:
                st.success(f"Found {len(items)} action items!")
                
                # Show extracted items
                st.subheader("Extracted Items")
                
                for i, item in enumerate(items):
                    with st.expander(f"Task {i+1}: {item['title']}", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            item['title'] = st.text_input(f"Title", item['title'], key=f"title_{i}")
                            item['description'] = st.text_area(f"Description", item['description'], key=f"desc_{i}")
                        
                        with col2:
                            item['priority'] = st.selectbox(f"Priority", 
                                ["Critical", "High", "Medium", "Low"], 
                                index=["Critical", "High", "Medium", "Low"].index(item['priority']),
                                key=f"priority_{i}")
                            item['category'] = st.selectbox(f"Category",
                                ["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"],
                                index=["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"].index(item['category']),
                                key=f"category_{i}")
                
                # Add all button
                if st.button("Add All Tasks", type="primary"):
                    added_count = 0
                    for item in st.session_state.extracted_items:
                        task = {
                            'id': generate_task_id(),
                            'title': item['title'],
                            'description': item['description'],
                            'priority': item['priority'],
                            'status': 'Not Started',
                            'category': item['category'],
                            'due_date': item['due_date'],
                            'estimated_hours': item['estimated_hours'],
                            'created_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        st.session_state.tasks.append(task)
                        added_count += 1
                    
                    # Save to file
                    if save_tasks_to_file():
                        st.success(f"Successfully added {added_count} tasks!")
                        st.session_state.extracted_items = []  # Clear extracted items
                        st.balloons()
                    else:
                        st.error("Failed to save tasks")
            else:
                st.warning("No action items found")
        else:
            st.warning("Please enter some text")

def show_all_tasks():
    st.header("All Tasks")
    
    if st.session_state.tasks:
        # Display tasks in a table
        df = pd.DataFrame(st.session_state.tasks)
        st.dataframe(df, use_container_width=True)
        
        # Task management
        st.subheader("Manage Tasks")
        
        for i, task in enumerate(st.session_state.tasks):
            with st.expander(f"{task['title']} ({task.get('status', 'Not Started')})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_status = st.selectbox(
                        "Status", 
                        ["Not Started", "In Progress", "Completed"],
                        index=["Not Started", "In Progress", "Completed"].index(task.get('status', 'Not Started')),
                        key=f"status_{task['id']}"
                    )
                
                with col2:
                    if st.button(f"Update Task {task['id']}", key=f"update_{task['id']}"):
                        st.session_state.tasks[i]['status'] = new_status
                        save_tasks_to_file()
                        st.success("Task updated!")
                        st.rerun()
        
        # Export tasks
        if st.button("Export Tasks to CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"tasks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No tasks to display. Go to 'Extract Tasks' to add some.")

if __name__ == "__main__":
    main()