import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ai_processor import AIProcessor
from task_manager import TaskManager
from visualization import VisualizationManager
from data_handler import DataHandler
from utils import format_date, get_priority_color, calculate_urgency_score

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'delegations' not in st.session_state:
    st.session_state.delegations = []
if 'ai_processor' not in st.session_state:
    st.session_state.ai_processor = AIProcessor()
if 'task_manager' not in st.session_state:
    st.session_state.task_manager = TaskManager()
if 'viz_manager' not in st.session_state:
    st.session_state.viz_manager = VisualizationManager()
if 'data_handler' not in st.session_state:
    st.session_state.data_handler = DataHandler()

# Load existing data
st.session_state.tasks = st.session_state.data_handler.load_tasks()
st.session_state.delegations = st.session_state.data_handler.load_delegations()

def main():
    st.set_page_config(
        page_title="AI Task & Delegation Manager",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎯 AI-Powered Task & Delegation Manager")
    st.markdown("*Automated action item extraction, prioritization, and timeline visualization for tech leadership*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["Dashboard", "AI Action Item Extraction", "Task Management", "Delegation Tracking", "Timeline & Analytics", "Data Management"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "AI Action Item Extraction":
        show_ai_extraction()
    elif page == "Task Management":
        show_task_management()
    elif page == "Delegation Tracking":
        show_delegation_tracking()
    elif page == "Timeline & Analytics":
        show_timeline_analytics()
    elif page == "Data Management":
        show_data_management()

def show_dashboard():
    st.header("📊 Executive Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_tasks = len(st.session_state.tasks)
    completed_tasks = len([t for t in st.session_state.tasks if t.get('status') == 'Completed'])
    overdue_tasks = len([t for t in st.session_state.tasks if t.get('due_date') and 
                        datetime.strptime(t['due_date'], '%Y-%m-%d') < datetime.now() and 
                        t.get('status') != 'Completed'])
    active_delegations = len([d for d in st.session_state.delegations if d.get('status') != 'Completed'])
    
    with col1:
        st.metric("Total Tasks", total_tasks)
    with col2:
        st.metric("Completed", completed_tasks, f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%")
    with col3:
        st.metric("Overdue", overdue_tasks, delta_color="inverse")
    with col4:
        st.metric("Active Delegations", active_delegations)
    
    # Quick insights
    st.subheader("🔍 AI Insights")
    if st.session_state.tasks:
        insights = st.session_state.ai_processor.generate_insights(st.session_state.tasks, st.session_state.delegations)
        if insights:
            for insight in insights:
                st.info(insight)
    else:
        st.info("Add some tasks to see AI-generated insights about your workload.")
    
    # Recent activity
    st.subheader("📋 Recent Tasks")
    if st.session_state.tasks:
        recent_tasks = sorted(st.session_state.tasks, key=lambda x: x.get('created_date', ''), reverse=True)[:5]
        for task in recent_tasks:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{task['title']}**")
                st.caption(task.get('description', 'No description'))
            with col2:
                priority_color = get_priority_color(task.get('priority', 'Medium'))
                st.markdown(f"<span style='color: {priority_color}'>{task.get('priority', 'Medium')}</span>", unsafe_allow_html=True)
            with col3:
                st.write(task.get('status', 'Not Started'))
    else:
        st.info("No tasks yet. Use the AI Action Item Extraction to get started!")

def show_ai_extraction():
    st.header("🤖 AI Action Item Extraction")
    st.markdown("Paste your meeting notes or text to automatically extract action items, set priorities, and create tasks.")
    
    # Input methods
    input_method = st.radio("Input Method:", ["Text Input", "File Upload"])
    
    text_content = ""
    
    if input_method == "Text Input":
        text_content = st.text_area(
            "Meeting Notes or Text:",
            height=200,
            placeholder="Paste your meeting notes here. The AI will automatically extract action items, deadlines, and priorities..."
        )
    else:
        uploaded_file = st.file_uploader("Upload a text file", type=['txt', 'md'])
        if uploaded_file:
            text_content = str(uploaded_file.read(), "utf-8")
            st.text_area("File Content:", text_content, height=200, disabled=True)
    
    # AI processing options
    col1, col2 = st.columns(2)
    with col1:
        auto_categorize = st.checkbox("Auto-categorize by project", value=True)
    with col2:
        auto_delegate = st.checkbox("Suggest delegations", value=True)
    
    if st.button("🚀 Extract Action Items", type="primary"):
        if text_content.strip():
            with st.spinner("AI is processing your text..."):
                try:
                    # Extract action items using AI
                    extracted_items = st.session_state.ai_processor.extract_action_items(
                        text_content, auto_categorize, auto_delegate
                    )
                    
                    if extracted_items:
                        st.success(f"Found {len(extracted_items)} action items!")
                        
                        # Display extracted items for review
                        st.subheader("📝 Extracted Action Items")
                        
                        for i, item in enumerate(extracted_items):
                            with st.expander(f"Action Item {i+1}: {item['title']}", expanded=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    item['title'] = st.text_input(f"Title {i+1}", item['title'], key=f"title_{i}")
                                    item['description'] = st.text_area(f"Description {i+1}", item.get('description', ''), key=f"desc_{i}")
                                    item['category'] = st.selectbox(f"Category {i+1}", 
                                        ["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"],
                                        index=["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"].index(item.get('category', 'Other')),
                                        key=f"cat_{i}")
                                
                                with col2:
                                    item['priority'] = st.selectbox(f"Priority {i+1}", 
                                        ["Critical", "High", "Medium", "Low"],
                                        index=["Critical", "High", "Medium", "Low"].index(item.get('priority', 'Medium')),
                                        key=f"priority_{i}")
                                    item['due_date'] = st.date_input(f"Due Date {i+1}", 
                                        value=datetime.strptime(item['due_date'], '%Y-%m-%d').date() if item.get('due_date') else None,
                                        key=f"due_{i}")
                                    item['estimated_hours'] = st.number_input(f"Estimated Hours {i+1}", 
                                        min_value=0.5, max_value=40.0, step=0.5, 
                                        value=float(item.get('estimated_hours', 1.0)), key=f"hours_{i}")
                                
                                # Delegation suggestion
                                if item.get('suggested_delegate'):
                                    st.info(f"💡 AI suggests delegating to: {item['suggested_delegate']}")
                                    if st.checkbox(f"Create delegation for {item['suggested_delegate']}", key=f"delegate_{i}"):
                                        item['create_delegation'] = True
                                        item['delegate_to'] = st.text_input(f"Delegate to", item['suggested_delegate'], key=f"delegate_to_{i}")
                        
                        # Batch actions
                        st.subheader("🎯 Batch Actions")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✅ Add All Tasks"):
                                for item in extracted_items:
                                    # Convert to task format
                                    task = {
                                        'id': len(st.session_state.tasks) + 1,
                                        'title': item['title'],
                                        'description': item.get('description', ''),
                                        'priority': item.get('priority', 'Medium'),
                                        'status': 'Not Started',
                                        'category': item.get('category', 'Other'),
                                        'due_date': str(item['due_date']) if item.get('due_date') else None,
                                        'estimated_hours': item.get('estimated_hours', 1.0),
                                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                                        'created_by_ai': True
                                    }
                                    st.session_state.tasks.append(task)
                                    
                                    # Create delegation if requested
                                    if item.get('create_delegation'):
                                        delegation = {
                                            'id': len(st.session_state.delegations) + 1,
                                            'task_title': item['title'],
                                            'delegate_to': item.get('delegate_to', ''),
                                            'status': 'Assigned',
                                            'due_date': str(item['due_date']) if item.get('due_date') else None,
                                            'created_date': datetime.now().strftime('%Y-%m-%d'),
                                            'notes': f"Auto-created from AI extraction: {item.get('description', '')}"
                                        }
                                        st.session_state.delegations.append(delegation)
                                
                                # Save data
                                st.session_state.data_handler.save_tasks(st.session_state.tasks)
                                st.session_state.data_handler.save_delegations(st.session_state.delegations)
                                
                                st.success("All tasks added successfully!")
                                st.rerun()
                        
                        with col2:
                            if st.button("📅 Add to Calendar"):
                                calendar_entries = st.session_state.task_manager.generate_calendar_entries(extracted_items)
                                st.success("Calendar entries generated! (Feature ready for integration)")
                        
                        with col3:
                            if st.button("📤 Export Tasks"):
                                csv_data = pd.DataFrame(extracted_items).to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv_data,
                                    file_name=f"extracted_tasks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                    mime="text/csv"
                                )
                    else:
                        st.warning("No action items found in the provided text.")
                        
                except Exception as e:
                    st.error(f"Error processing text: {str(e)}")
        else:
            st.warning("Please provide some text to process.")

def show_task_management():
    st.header("📋 Task Management")
    
    # Task creation form
    with st.expander("➕ Create New Task", expanded=False):
        with st.form("new_task_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Task Title*")
                description = st.text_area("Description")
                category = st.selectbox("Category", 
                    ["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"])
            
            with col2:
                priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
                due_date = st.date_input("Due Date")
                estimated_hours = st.number_input("Estimated Hours", min_value=0.5, max_value=40.0, step=0.5, value=1.0)
            
            if st.form_submit_button("Create Task"):
                if title:
                    new_task = {
                        'id': len(st.session_state.tasks) + 1,
                        'title': title,
                        'description': description,
                        'priority': priority,
                        'status': 'Not Started',
                        'category': category,
                        'due_date': str(due_date),
                        'estimated_hours': estimated_hours,
                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                        'created_by_ai': False
                    }
                    st.session_state.tasks.append(new_task)
                    st.session_state.data_handler.save_tasks(st.session_state.tasks)
                    st.success("Task created successfully!")
                    st.rerun()
                else:
                    st.error("Please provide a task title.")
    
    # Task filters
    st.subheader("🔍 Filter Tasks")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "Not Started", "In Progress", "Completed", "On Hold"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])
    with col3:
        category_filter = st.selectbox("Category", ["All", "Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"])
    with col4:
        sort_by = st.selectbox("Sort by", ["Due Date", "Priority", "Created Date", "Title"])
    
    # Apply filters
    filtered_tasks = st.session_state.tasks.copy()
    
    if status_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('status') == status_filter]
    if priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('priority') == priority_filter]
    if category_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('category') == category_filter]
    
    # Sort tasks
    if sort_by == "Due Date":
        filtered_tasks.sort(key=lambda x: x.get('due_date', '9999-12-31'))
    elif sort_by == "Priority":
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        filtered_tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'Medium'), 2))
    elif sort_by == "Created Date":
        filtered_tasks.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    else:  # Title
        filtered_tasks.sort(key=lambda x: x.get('title', '').lower())
    
    # Display tasks
    st.subheader(f"📝 Tasks ({len(filtered_tasks)} found)")
    
    if filtered_tasks:
        for i, task in enumerate(filtered_tasks):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{task['title']}**")
                    if task.get('description'):
                        st.caption(task['description'])
                    
                    # Show AI badge if created by AI
                    if task.get('created_by_ai'):
                        st.caption("🤖 Created by AI")
                
                with col2:
                    priority_color = get_priority_color(task.get('priority', 'Medium'))
                    st.markdown(f"<span style='color: {priority_color}'>●</span> {task.get('priority', 'Medium')}", 
                              unsafe_allow_html=True)
                    if task.get('due_date'):
                        st.caption(f"Due: {format_date(task['due_date'])}")
                
                with col3:
                    new_status = st.selectbox(
                        "Status",
                        ["Not Started", "In Progress", "Completed", "On Hold"],
                        index=["Not Started", "In Progress", "Completed", "On Hold"].index(task.get('status', 'Not Started')),
                        key=f"status_{task['id']}"
                    )
                    if new_status != task.get('status'):
                        task['status'] = new_status
                        if new_status == 'Completed':
                            task['completed_date'] = datetime.now().strftime('%Y-%m-%d')
                        st.session_state.data_handler.save_tasks(st.session_state.tasks)
                        st.rerun()
                
                with col4:
                    if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                        st.session_state[f"editing_{task['id']}"] = True
                        st.rerun()
                    
                    if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                        st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task['id']]
                        st.session_state.data_handler.save_tasks(st.session_state.tasks)
                        st.success("Task deleted!")
                        st.rerun()
                
                # Edit form
                if st.session_state.get(f"editing_{task['id']}", False):
                    with st.form(f"edit_task_{task['id']}"):
                        st.write("**Edit Task**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_title = st.text_input("Title", task['title'])
                            new_description = st.text_area("Description", task.get('description', ''))
                            new_category = st.selectbox("Category", 
                                ["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"],
                                index=["Strategic", "Technical", "Meeting", "Review", "Administrative", "Other"].index(task.get('category', 'Other')))
                        
                        with col2:
                            new_priority = st.selectbox("Priority", 
                                ["Critical", "High", "Medium", "Low"],
                                index=["Critical", "High", "Medium", "Low"].index(task.get('priority', 'Medium')))
                            new_due_date = st.date_input("Due Date", 
                                value=datetime.strptime(task['due_date'], '%Y-%m-%d').date() if task.get('due_date') else None)
                            new_estimated_hours = st.number_input("Estimated Hours", 
                                min_value=0.5, max_value=40.0, step=0.5, 
                                value=float(task.get('estimated_hours', 1.0)))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save Changes"):
                                task.update({
                                    'title': new_title,
                                    'description': new_description,
                                    'priority': new_priority,
                                    'category': new_category,
                                    'due_date': str(new_due_date) if new_due_date else None,
                                    'estimated_hours': new_estimated_hours
                                })
                                st.session_state.data_handler.save_tasks(st.session_state.tasks)
                                st.session_state[f"editing_{task['id']}"] = False
                                st.success("Task updated!")
                                st.rerun()
                        
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"editing_{task['id']}"] = False
                                st.rerun()
                
                st.divider()
    else:
        st.info("No tasks match the current filters.")

def show_delegation_tracking():
    st.header("👥 Delegation Tracking")
    
    # Create new delegation
    with st.expander("➕ Create New Delegation", expanded=False):
        with st.form("new_delegation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                task_title = st.text_input("Task/Project Title*")
                delegate_to = st.text_input("Delegate To*")
                due_date = st.date_input("Due Date")
            
            with col2:
                priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
                status = st.selectbox("Status", ["Assigned", "In Progress", "Review", "Completed"])
                notes = st.text_area("Notes/Instructions")
            
            if st.form_submit_button("Create Delegation"):
                if task_title and delegate_to:
                    new_delegation = {
                        'id': len(st.session_state.delegations) + 1,
                        'task_title': task_title,
                        'delegate_to': delegate_to,
                        'priority': priority,
                        'status': status,
                        'due_date': str(due_date),
                        'notes': notes,
                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.session_state.delegations.append(new_delegation)
                    st.session_state.data_handler.save_delegations(st.session_state.delegations)
                    st.success("Delegation created successfully!")
                    st.rerun()
                else:
                    st.error("Please provide task title and delegate name.")
    
    # Delegation filters
    st.subheader("🔍 Filter Delegations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "Assigned", "In Progress", "Review", "Completed"], key="del_status")
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="del_priority")
    with col3:
        delegate_filter = st.selectbox("Delegate", 
            ["All"] + list(set([d.get('delegate_to', '') for d in st.session_state.delegations if d.get('delegate_to')])))
    
    # Apply filters
    filtered_delegations = st.session_state.delegations.copy()
    
    if status_filter != "All":
        filtered_delegations = [d for d in filtered_delegations if d.get('status') == status_filter]
    if priority_filter != "All":
        filtered_delegations = [d for d in filtered_delegations if d.get('priority') == priority_filter]
    if delegate_filter != "All":
        filtered_delegations = [d for d in filtered_delegations if d.get('delegate_to') == delegate_filter]
    
    # Display delegations
    st.subheader(f"👥 Delegations ({len(filtered_delegations)} found)")
    
    if filtered_delegations:
        for delegation in filtered_delegations:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{delegation['task_title']}**")
                    st.caption(f"Delegated to: {delegation.get('delegate_to', 'Unknown')}")
                    if delegation.get('notes'):
                        st.caption(f"Notes: {delegation['notes']}")
                
                with col2:
                    priority_color = get_priority_color(delegation.get('priority', 'Medium'))
                    st.markdown(f"<span style='color: {priority_color}'>●</span> {delegation.get('priority', 'Medium')}", 
                              unsafe_allow_html=True)
                    if delegation.get('due_date'):
                        st.caption(f"Due: {format_date(delegation['due_date'])}")
                
                with col3:
                    new_status = st.selectbox(
                        "Status",
                        ["Assigned", "In Progress", "Review", "Completed"],
                        index=["Assigned", "In Progress", "Review", "Completed"].index(delegation.get('status', 'Assigned')),
                        key=f"del_status_{delegation['id']}"
                    )
                    if new_status != delegation.get('status'):
                        delegation['status'] = new_status
                        delegation['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                        if new_status == 'Completed':
                            delegation['completed_date'] = datetime.now().strftime('%Y-%m-%d')
                        st.session_state.data_handler.save_delegations(st.session_state.delegations)
                        st.rerun()
                
                with col4:
                    if st.button("🔔", key=f"remind_{delegation['id']}", help="Send reminder"):
                        st.success(f"Reminder sent to {delegation.get('delegate_to', 'Unknown')}!")
                    
                    if st.button("🗑️", key=f"del_delete_{delegation['id']}", help="Delete delegation"):
                        st.session_state.delegations = [d for d in st.session_state.delegations if d['id'] != delegation['id']]
                        st.session_state.data_handler.save_delegations(st.session_state.delegations)
                        st.success("Delegation deleted!")
                        st.rerun()
                
                st.divider()
    else:
        st.info("No delegations match the current filters.")
    
    # Delegation analytics
    if st.session_state.delegations:
        st.subheader("📊 Delegation Analytics")
        
        # Status distribution
        status_counts = {}
        for delegation in st.session_state.delegations:
            status = delegation.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            if status_counts:
                fig = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="Delegation Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Delegate performance
            delegate_performance = {}
            for delegation in st.session_state.delegations:
                delegate = delegation.get('delegate_to', 'Unknown')
                if delegate not in delegate_performance:
                    delegate_performance[delegate] = {'total': 0, 'completed': 0}
                delegate_performance[delegate]['total'] += 1
                if delegation.get('status') == 'Completed':
                    delegate_performance[delegate]['completed'] += 1
            
            if delegate_performance:
                delegates = list(delegate_performance.keys())
                completion_rates = [
                    (delegate_performance[d]['completed'] / delegate_performance[d]['total'] * 100)
                    for d in delegates
                ]
                
                fig = px.bar(
                    x=delegates,
                    y=completion_rates,
                    title="Delegate Completion Rate (%)",
                    labels={'x': 'Delegate', 'y': 'Completion Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)

def show_timeline_analytics():
    st.header("📈 Timeline & Analytics")
    
    # Timeline view selector
    view_type = st.selectbox("View Type", ["Gantt Chart", "Calendar View", "Analytics Dashboard"])
    
    if view_type == "Gantt Chart":
        st.subheader("📊 Project Timeline - Gantt Chart")
        
        if st.session_state.tasks:
            gantt_fig = st.session_state.viz_manager.create_gantt_chart(st.session_state.tasks)
            if gantt_fig:
                st.plotly_chart(gantt_fig, use_container_width=True)
            else:
                st.info("Add due dates to your tasks to see the Gantt chart.")
        else:
            st.info("No tasks available for timeline visualization.")
    
    elif view_type == "Calendar View":
        st.subheader("📅 Calendar View")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date())
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=30))
        
        if st.session_state.tasks:
            calendar_fig = st.session_state.viz_manager.create_calendar_view(
                st.session_state.tasks, start_date, end_date
            )
            if calendar_fig:
                st.plotly_chart(calendar_fig, use_container_width=True)
        else:
            st.info("No tasks available for calendar view.")
    
    else:  # Analytics Dashboard
        st.subheader("📊 Analytics Dashboard")
        
        if st.session_state.tasks:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_hours = sum([float(t.get('estimated_hours', 0)) for t in st.session_state.tasks])
            completed_hours = sum([float(t.get('estimated_hours', 0)) for t in st.session_state.tasks if t.get('status') == 'Completed'])
            avg_completion_time = st.session_state.task_manager.calculate_avg_completion_time(st.session_state.tasks)
            productivity_score = st.session_state.task_manager.calculate_productivity_score(st.session_state.tasks)
            
            with col1:
                st.metric("Total Estimated Hours", f"{total_hours:.1f}")
            with col2:
                st.metric("Completed Hours", f"{completed_hours:.1f}")
            with col3:
                st.metric("Avg Completion Time", f"{avg_completion_time:.1f} days" if avg_completion_time else "N/A")
            with col4:
                st.metric("Productivity Score", f"{productivity_score:.1f}%" if productivity_score else "N/A")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Priority distribution
                priority_counts = {}
                for task in st.session_state.tasks:
                    priority = task.get('priority', 'Medium')
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                if priority_counts:
                    fig = px.pie(
                        values=list(priority_counts.values()),
                        names=list(priority_counts.keys()),
                        title="Task Priority Distribution",
                        color_discrete_map={
                            'Critical': '#FF6B6B',
                            'High': '#FF8E53',
                            'Medium': '#4ECDC4',
                            'Low': '#45B7D1'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Category distribution
                category_counts = {}
                for task in st.session_state.tasks:
                    category = task.get('category', 'Other')
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                if category_counts:
                    fig = px.bar(
                        x=list(category_counts.keys()),
                        y=list(category_counts.values()),
                        title="Tasks by Category",
                        labels={'x': 'Category', 'y': 'Number of Tasks'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Workload analysis
            st.subheader("📊 Workload Analysis")
            
            # Daily workload
            daily_workload = st.session_state.viz_manager.calculate_daily_workload(st.session_state.tasks)
            if daily_workload:
                fig = px.line(
                    x=list(daily_workload.keys()),
                    y=list(daily_workload.values()),
                    title="Daily Workload (Estimated Hours)",
                    labels={'x': 'Date', 'y': 'Hours'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Burndown chart
            burndown_data = st.session_state.viz_manager.create_burndown_chart(st.session_state.tasks)
            if burndown_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=burndown_data['dates'],
                    y=burndown_data['remaining_tasks'],
                    mode='lines+markers',
                    name='Remaining Tasks',
                    line=dict(color='#FF6B6B')
                ))
                fig.update_layout(
                    title="Task Burndown Chart",
                    xaxis_title="Date",
                    yaxis_title="Remaining Tasks"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No tasks available for analytics.")

def show_data_management():
    st.header("💾 Data Management")
    
    # Export data
    st.subheader("📤 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Tasks (CSV)"):
            if st.session_state.tasks:
                df = pd.DataFrame(st.session_state.tasks)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download Tasks CSV",
                    data=csv_data,
                    file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No tasks to export.")
    
    with col2:
        if st.button("Export Delegations (CSV)"):
            if st.session_state.delegations:
                df = pd.DataFrame(st.session_state.delegations)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download Delegations CSV",
                    data=csv_data,
                    file_name=f"delegations_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No delegations to export.")
    
    # Import data
    st.subheader("📥 Import Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Import Tasks**")
        uploaded_tasks = st.file_uploader("Upload tasks CSV file", type=['csv'], key="tasks_upload")
        if uploaded_tasks:
            try:
                df = pd.read_csv(uploaded_tasks)
                st.write("Preview:")
                st.dataframe(df.head())
                
                if st.button("Import Tasks"):
                    imported_tasks = df.to_dict('records')
                    # Assign new IDs to avoid conflicts
                    for i, task in enumerate(imported_tasks):
                        task['id'] = len(st.session_state.tasks) + i + 1
                    
                    st.session_state.tasks.extend(imported_tasks)
                    st.session_state.data_handler.save_tasks(st.session_state.tasks)
                    st.success(f"Successfully imported {len(imported_tasks)} tasks!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing tasks: {str(e)}")
    
    with col2:
        st.write("**Import Delegations**")
        uploaded_delegations = st.file_uploader("Upload delegations CSV file", type=['csv'], key="delegations_upload")
        if uploaded_delegations:
            try:
                df = pd.read_csv(uploaded_delegations)
                st.write("Preview:")
                st.dataframe(df.head())
                
                if st.button("Import Delegations"):
                    imported_delegations = df.to_dict('records')
                    # Assign new IDs to avoid conflicts
                    for i, delegation in enumerate(imported_delegations):
                        delegation['id'] = len(st.session_state.delegations) + i + 1
                    
                    st.session_state.delegations.extend(imported_delegations)
                    st.session_state.data_handler.save_delegations(st.session_state.delegations)
                    st.success(f"Successfully imported {len(imported_delegations)} delegations!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing delegations: {str(e)}")
    
    # Data statistics
    st.subheader("📊 Data Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", len(st.session_state.tasks))
    with col2:
        st.metric("Total Delegations", len(st.session_state.delegations))
    with col3:
        ai_tasks = len([t for t in st.session_state.tasks if t.get('created_by_ai')])
        st.metric("AI-Generated Tasks", ai_tasks)
    with col4:
        manual_tasks = len(st.session_state.tasks) - ai_tasks
        st.metric("Manual Tasks", manual_tasks)
    
    # Clear data
    st.subheader("🗑️ Clear Data")
    st.warning("⚠️ These actions cannot be undone!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Clear All Tasks", type="secondary"):
            if st.session_state.tasks:
                st.session_state.tasks = []
                st.session_state.data_handler.save_tasks(st.session_state.tasks)
                st.success("All tasks cleared!")
                st.rerun()
    
    with col2:
        if st.button("Clear All Delegations", type="secondary"):
            if st.session_state.delegations:
                st.session_state.delegations = []
                st.session_state.data_handler.save_delegations(st.session_state.delegations)
                st.success("All delegations cleared!")
                st.rerun()
    
    with col3:
        if st.button("Clear Everything", type="secondary"):
            st.session_state.tasks = []
            st.session_state.delegations = []
            st.session_state.data_handler.save_tasks(st.session_state.tasks)
            st.session_state.data_handler.save_delegations(st.session_state.delegations)
            st.success("All data cleared!")
            st.rerun()

if __name__ == "__main__":
    main()
