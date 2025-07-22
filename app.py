import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Import our custom modules
from ai_processor import AIProcessor
from data_handler import DataHandler
from task_manager import TaskManager
from visualization import VisualizationManager
from utils import format_date, get_priority_color

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    if 'delegations' not in st.session_state:
        st.session_state.delegations = []
    if 'extracted_items' not in st.session_state:
        st.session_state.extracted_items = []
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "dashboard"
    if 'last_task_count' not in st.session_state:
        st.session_state.last_task_count = 0
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'ai_backend': 'ollama',
            'ollama_model': 'mistral:latest',
            'categories': ['Development', 'Management', 'Research', 'Documentation', 'Testing', 'Other'],
            'delegates': ['John Smith', 'Sarah Connor', 'Mike Johnson', 'Lisa Anderson'],
            'default_priority': 'Medium'
        }
    if 'data_handler' not in st.session_state:
        st.session_state.data_handler = DataHandler()
        # Load existing data
        st.session_state.tasks = st.session_state.data_handler.load_tasks()
        st.session_state.delegations = st.session_state.data_handler.load_delegations()
        st.session_state.settings.update(st.session_state.data_handler.load_settings())

def save_all_data():
    """Save all data to persistent storage"""
    if hasattr(st.session_state, 'data_handler'):
        st.session_state.data_handler.save_tasks(st.session_state.tasks)
        st.session_state.data_handler.save_delegations(st.session_state.delegations)
        st.session_state.data_handler.save_settings(st.session_state.settings)

def render_dashboard():
    """Render the main dashboard tab"""
    # Auto-refresh when switching to dashboard and task count changed
    current_task_count = len(st.session_state.tasks)
    if st.session_state.active_tab != "dashboard" and current_task_count != st.session_state.last_task_count:
        st.session_state.last_task_count = current_task_count
        st.rerun()
    
    st.session_state.active_tab = "dashboard"
    
    st.header("🏠 Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", len(st.session_state.tasks))
    with col2:
        completed = len([t for t in st.session_state.tasks if t['status'] == 'Completed'])
        st.metric("Completed", completed)
    with col3:
        urgent_priority = len([t for t in st.session_state.tasks if t.get('priority') in ['High', 'Critical']])
        st.metric("Urgent Tasks", urgent_priority)
    with col4:
        if st.button("🔄 Refresh", help="Refresh dashboard"):
            st.rerun()
    
    if st.session_state.tasks:
        # Recent tasks
        st.subheader("📋 Recent Tasks")
        recent_tasks = sorted(st.session_state.tasks, 
                             key=lambda x: x.get('created_date', ''), reverse=True)[:5]
        
        for task in recent_tasks:
            with st.expander(f"📋 {task['title']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Description:** {task.get('description', 'No description')}")
                with col2:
                    priority_color = get_priority_color(task.get('priority', 'Medium'))
                    st.markdown(f"**Priority:** <span style='color: {priority_color}'>{task.get('priority', 'Medium')}</span>", 
                               unsafe_allow_html=True)
                with col3:
                    st.write(f"**Status:** {task.get('status', 'Not Started')}")
                
                # Show additional details
                if task.get('due_date'):
                    st.write(f"**Due Date:** {task['due_date']}")
                if task.get('delegated_to'):
                    st.write(f"**Assigned to:** {task['delegated_to']}")
                st.write(f"**Created:** {task.get('created_date', 'Unknown')}")
        
        # Quick visualizations
        st.subheader("📊 Quick Overview")
        
        # Status distribution
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = {}
            for task in st.session_state.tasks:
                status = task.get('status', 'Not Started')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                fig = px.pie(values=list(status_counts.values()), 
                           names=list(status_counts.keys()),
                           title="Task Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            priority_counts = {}
            for task in st.session_state.tasks:
                priority = task.get('priority', 'Medium')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            if priority_counts:
                fig = px.bar(x=list(priority_counts.keys()), 
                           y=list(priority_counts.values()),
                           title="Priority Distribution",
                           color=list(priority_counts.keys()),
                           color_discrete_map={'Critical': '#FF0000', 'High': '#FF6B6B', 'Medium': '#4ECDC4', 'Low': '#45B7D1'})
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks yet. Use the 'Extract Tasks' or 'Add Task' tabs to get started!")
        
        # Quick start buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Extract from Meeting Notes", help="Extract tasks from text"):
                st.session_state.active_tab = "extract"
                st.rerun()
        with col2:
            if st.button("➕ Add Manual Task", help="Add a task manually"):
                st.session_state.active_tab = "add_task"
                st.rerun()

def render_extract_tasks():
    """Render AI-powered task extraction tab"""
    st.session_state.active_tab = "extract"
    
    st.header("🤖 AI Task Extraction")
    
    # AI Backend selection
    col1, col2 = st.columns([2, 1])
    with col1:
        backend = st.selectbox("AI Backend", 
                              options=['ollama', 'perplexity', 'openai'], 
                              index=['ollama', 'perplexity', 'openai'].index(st.session_state.settings['ai_backend']))
        if backend != st.session_state.settings['ai_backend']:
            st.session_state.settings['ai_backend'] = backend
            save_all_data()
    
    with col2:
        if backend == 'ollama':
            model = st.text_input("Ollama Model", value=st.session_state.settings.get('ollama_model', 'mistral:latest'))
            if model != st.session_state.settings.get('ollama_model'):
                st.session_state.settings['ollama_model'] = model
                save_all_data()
    
    # Initialize AI processor
    ai_processor = AIProcessor(backend=backend, settings=st.session_state.settings)
    
    # Status indicator
    if ai_processor.api_available:
        st.success(f"✅ {backend.title()} AI is available")
    else:
        st.warning(f"⚠️ {backend.title()} AI is not available. Using fallback extraction.")
        if backend == 'ollama':
            st.info("Make sure Ollama is running locally with the specified model installed.")
        elif backend in ['perplexity', 'openai']:
            st.info(f"Please provide the {backend.upper()}_API_KEY environment variable.")
    
    # Text input
    st.subheader("📄 Input Text")
    text_input = st.text_area(
        "Paste your meeting notes, emails, or any text containing action items:",
        height=200,
        placeholder="Example:\n\nMeeting Notes - Project Alpha\n- John needs to complete the API documentation by Friday\n- Sarah will review the security protocols\n- We need to schedule user testing for next week\n- Mike should update the deployment scripts"
    )
    
    # Extraction options
    with st.expander("⚙️ Extraction Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            max_items = st.number_input("Maximum items to extract", min_value=1, max_value=20, value=10)
            auto_delegate = st.checkbox("Auto-suggest delegation", value=True)
        with col2:
            priority_options = ['Low', 'Medium', 'High', 'Critical']
            current_default = st.session_state.settings.get('default_priority', 'Medium')
            priority_index = priority_options.index(current_default) if current_default in priority_options else 1
            default_priority = st.selectbox("Default priority", priority_options, 
                                              index=priority_index)
            categorize = st.checkbox("Auto-categorize tasks", value=True)
    
    # Extract button
    if st.button("🚀 Extract Action Items", disabled=not text_input.strip()):
        with st.spinner("🤖 AI is analyzing your text and extracting action items..."):
            try:
                # Extract items
                extracted = ai_processor.extract_action_items(
                    text_input,
                    categories=st.session_state.settings['categories'],
                    delegates=st.session_state.settings['delegates'],
                    max_items=max_items
                )
                
                if extracted:
                    st.session_state.extracted_items = extracted
                    st.success(f"✅ Found {len(extracted)} action items!")
                    st.balloons()
                else:
                    st.warning("No action items found in the provided text.")
                    
            except Exception as e:
                st.error(f"Error during extraction: {str(e)}")
    
    # Display extracted items
    if st.session_state.extracted_items:
        st.subheader("📋 Extracted Action Items")
        
        # Select all/none buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Select All"):
                for i in range(len(st.session_state.extracted_items)):
                    st.session_state[f"select_item_{i}"] = True
                st.rerun()
        with col2:
            if st.button("❌ Select None"):
                for i in range(len(st.session_state.extracted_items)):
                    st.session_state[f"select_item_{i}"] = False
                st.rerun()
        
        # Edit extracted items
        edited_items = []
        for i, item in enumerate(st.session_state.extracted_items):
            with st.expander(f"📋 {item['title']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Editable fields
                    title = st.text_input(f"Title {i+1}", value=item['title'], key=f"title_{i}")
                    description = st.text_area(f"Description {i+1}", value=item.get('description', ''), key=f"desc_{i}")
                    
                    col1a, col1b = st.columns(2)
                    with col1a:
                        priority_options = ['Low', 'Medium', 'High', 'Critical']
                        item_priority = item.get('priority', 'Medium')
                        priority_index = priority_options.index(item_priority) if item_priority in priority_options else 1
                        priority = st.selectbox(f"Priority {i+1}", priority_options, 
                                              index=priority_index,
                                              key=f"priority_{i}")
                        category = st.selectbox(f"Category {i+1}", st.session_state.settings['categories'],
                                              index=st.session_state.settings['categories'].index(item.get('category', 'Other')) 
                                              if item.get('category', 'Other') in st.session_state.settings['categories'] else 0,
                                              key=f"category_{i}")
                    with col1b:
                        delegate = st.selectbox(f"Delegate to {i+1}", ['None'] + st.session_state.settings['delegates'],
                                              index=0 if not item.get('delegated_to') else 
                                              st.session_state.settings['delegates'].index(item['delegated_to']) + 1 
                                              if item.get('delegated_to') in st.session_state.settings['delegates'] else 0,
                                              key=f"delegate_{i}")
                        due_date = st.date_input(f"Due Date {i+1}", value=None, key=f"due_{i}")
                
                with col2:
                    selected = st.checkbox(f"Include", value=True, key=f"select_item_{i}")
                
                # Build edited item
                edited_item = {
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'category': category,
                    'delegated_to': delegate if delegate != 'None' else None,
                    'due_date': due_date.strftime('%Y-%m-%d') if due_date else None,
                    'status': 'Not Started',
                    'created_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                if selected:
                    edited_items.append(edited_item)
        
        # Add selected items
        if st.button("➕ Add Selected Tasks", disabled=not edited_items):
            # Add to task list
            for item in edited_items:
                item['id'] = len(st.session_state.tasks) + 1
                st.session_state.tasks.append(item)
            
            # Save to persistent storage
            save_all_data()
            
            st.success(f"✅ Added {len(edited_items)} tasks successfully!")
            st.session_state.extracted_items = []  # Clear extracted items
            st.balloons()
            
            # Auto-refresh dashboard
            st.session_state.last_task_count = len(st.session_state.tasks)

def render_manage_tasks():
    """Render task management tab"""
    st.session_state.active_tab = "manage"
    
    st.header("📋 Manage Tasks")
    
    if not st.session_state.tasks:
        st.info("No tasks available. Use 'Extract Tasks' or 'Add Task' to get started.")
        return
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   options=['All'] + list(set([t.get('status', 'Not Started') for t in st.session_state.tasks])))
    with col2:
        priority_filter = st.selectbox("Filter by Priority", 
                                     options=['All'] + ['Critical', 'High', 'Medium', 'Low'])
    with col3:
        category_filter = st.selectbox("Filter by Category", 
                                     options=['All'] + st.session_state.settings['categories'])
    with col4:
        delegate_filter = st.selectbox("Filter by Delegate", 
                                     options=['All'] + st.session_state.settings['delegates'])
    
    # Filter tasks
    filtered_tasks = st.session_state.tasks.copy()
    if status_filter != 'All':
        filtered_tasks = [t for t in filtered_tasks if t.get('status') == status_filter]
    if priority_filter != 'All':
        filtered_tasks = [t for t in filtered_tasks if t.get('priority') == priority_filter]
    if category_filter != 'All':
        filtered_tasks = [t for t in filtered_tasks if t.get('category') == category_filter]
    if delegate_filter != 'All':
        filtered_tasks = [t for t in filtered_tasks if t.get('delegated_to') == delegate_filter]
    
    st.write(f"Showing {len(filtered_tasks)} of {len(st.session_state.tasks)} tasks")
    
    # Task list
    for i, task in enumerate(filtered_tasks):
        with st.expander(f"📋 {task['title']}", expanded=False):
            # Find original task index
            original_idx = next(idx for idx, t in enumerate(st.session_state.tasks) if t.get('id') == task.get('id'))
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Editable fields
                new_title = st.text_input(f"Title", value=task['title'], key=f"edit_title_{task.get('id', i)}")
                new_desc = st.text_area(f"Description", value=task.get('description', ''), key=f"edit_desc_{task.get('id', i)}")
                
                col1a, col1b = st.columns(2)
                with col1a:
                    new_status = st.selectbox(f"Status", ['Not Started', 'In Progress', 'Completed', 'On Hold'],
                                            index=['Not Started', 'In Progress', 'Completed', 'On Hold'].index(task.get('status', 'Not Started')),
                                            key=f"edit_status_{task.get('id', i)}")
                    priority_options = ['Low', 'Medium', 'High', 'Critical']
                    task_priority = task.get('priority', 'Medium')
                    priority_index = priority_options.index(task_priority) if task_priority in priority_options else 1
                    new_priority = st.selectbox(f"Priority", priority_options,
                                              index=priority_index,
                                              key=f"edit_priority_{task.get('id', i)}")
                with col1b:
                    new_category = st.selectbox(f"Category", st.session_state.settings['categories'],
                                              index=st.session_state.settings['categories'].index(task.get('category', 'Other')) 
                                              if task.get('category', 'Other') in st.session_state.settings['categories'] else 0,
                                              key=f"edit_category_{task.get('id', i)}")
                    current_delegate = task.get('delegated_to', 'None')
                    delegate_options = ['None'] + st.session_state.settings['delegates']
                    delegate_index = delegate_options.index(current_delegate) if current_delegate in delegate_options else 0
                    new_delegate = st.selectbox(f"Delegate", delegate_options,
                                              index=delegate_index,
                                              key=f"edit_delegate_{task.get('id', i)}")
            
            with col2:
                # Due date
                current_due = datetime.strptime(task['due_date'], '%Y-%m-%d').date() if task.get('due_date') else None
                new_due = st.date_input(f"Due Date", value=current_due, key=f"edit_due_{task.get('id', i)}")
                
                # Action buttons
                col2a, col2b = st.columns(2)
                with col2a:
                    if st.button(f"💾 Save", key=f"save_{task.get('id', i)}"):
                        # Update task
                        st.session_state.tasks[original_idx].update({
                            'title': new_title,
                            'description': new_desc,
                            'status': new_status,
                            'priority': new_priority,
                            'category': new_category,
                            'delegated_to': new_delegate if new_delegate != 'None' else None,
                            'due_date': new_due.strftime('%Y-%m-%d') if new_due else None
                        })
                        save_all_data()
                        st.success("Task updated!")
                        st.rerun()
                
                with col2b:
                    if st.button(f"🗑️ Delete", key=f"delete_{task.get('id', i)}"):
                        st.session_state.tasks.pop(original_idx)
                        save_all_data()
                        st.success("Task deleted!")
                        st.rerun()
    
    # Bulk actions
    if filtered_tasks:
        st.subheader("🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Export Filtered Tasks"):
                df = pd.DataFrame(filtered_tasks)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("✅ Mark All as Complete"):
                for task in filtered_tasks:
                    original_idx = next(idx for idx, t in enumerate(st.session_state.tasks) if t.get('id') == task.get('id'))
                    st.session_state.tasks[original_idx]['status'] = 'Completed'
                save_all_data()
                st.success(f"Marked {len(filtered_tasks)} tasks as completed!")
                st.rerun()

def render_analytics():
    """Render analytics and visualization tab"""
    st.session_state.active_tab = "analytics"
    
    st.header("📊 Analytics & Insights")
    
    if not st.session_state.tasks:
        st.info("No tasks available for analytics. Add some tasks first!")
        return
    
    # Initialize visualization manager
    viz_manager = VisualizationManager()
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_tasks = len(st.session_state.tasks)
    completed_tasks = len([t for t in st.session_state.tasks if t.get('status') == 'Completed'])
    high_priority = len([t for t in st.session_state.tasks if t.get('priority') in ['High', 'Critical']])
    overdue_tasks = 0
    
    # Calculate overdue tasks
    today = datetime.now().date()
    for task in st.session_state.tasks:
        if task.get('due_date') and task.get('status') != 'Completed':
            try:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                if due_date < today:
                    overdue_tasks += 1
            except:
                pass
    
    with col1:
        st.metric("Total Tasks", total_tasks)
    with col2:
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    with col3:
        st.metric("High Priority", high_priority)
    with col4:
        st.metric("Overdue Tasks", overdue_tasks, delta=f"-{overdue_tasks}" if overdue_tasks > 0 else None)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Distribution")
        status_fig = viz_manager.create_status_distribution(st.session_state.tasks)
        if status_fig:
            st.plotly_chart(status_fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Priority Breakdown")
        priority_fig = viz_manager.create_priority_distribution(st.session_state.tasks)
        if priority_fig:
            st.plotly_chart(priority_fig, use_container_width=True)
    
    # Timeline view
    st.subheader("📅 Timeline View")
    timeline_fig = viz_manager.create_gantt_chart(st.session_state.tasks)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("Add due dates to tasks to see the timeline view.")
    
    # Category analysis
    st.subheader("📂 Category Analysis")
    category_fig = viz_manager.create_category_analysis(st.session_state.tasks)
    if category_fig:
        st.plotly_chart(category_fig, use_container_width=True)

def render_settings():
    """Render settings tab"""
    st.session_state.active_tab = "settings"
    
    st.header("⚙️ Settings")
    
    # AI Settings
    st.subheader("🤖 AI Configuration")
    with st.expander("AI Backend Settings", expanded=True):
        backend = st.selectbox("Default AI Backend", 
                              options=['ollama', 'perplexity', 'openai'], 
                              index=['ollama', 'perplexity', 'openai'].index(st.session_state.settings['ai_backend']))
        
        if backend == 'ollama':
            model = st.text_input("Ollama Model", value=st.session_state.settings.get('ollama_model', 'mistral:latest'))
            st.session_state.settings['ollama_model'] = model
        
        st.session_state.settings['ai_backend'] = backend
    
    # Task Settings
    st.subheader("📋 Task Settings")
    with st.expander("Default Task Settings", expanded=True):
        priority_options = ['Low', 'Medium', 'High', 'Critical']
        current_default = st.session_state.settings.get('default_priority', 'Medium')
        priority_index = priority_options.index(current_default) if current_default in priority_options else 1
        default_priority = st.selectbox("Default Priority", priority_options,
                                      index=priority_index)
        st.session_state.settings['default_priority'] = default_priority
    
    # Categories Management
    st.subheader("📂 Categories")
    with st.expander("Manage Categories", expanded=False):
        categories = st.text_area("Categories (one per line)", 
                                value='\n'.join(st.session_state.settings['categories']),
                                height=150)
        new_categories = [cat.strip() for cat in categories.split('\n') if cat.strip()]
        if new_categories != st.session_state.settings['categories']:
            st.session_state.settings['categories'] = new_categories
    
    # Delegates Management  
    st.subheader("👥 Team Members")
    with st.expander("Manage Team Members", expanded=False):
        delegates = st.text_area("Team Members (one per line)",
                                value='\n'.join(st.session_state.settings['delegates']),
                                height=150)
        new_delegates = [delegate.strip() for delegate in delegates.split('\n') if delegate.strip()]
        if new_delegates != st.session_state.settings['delegates']:
            st.session_state.settings['delegates'] = new_delegates
    
    # Data Management
    st.subheader("💾 Data Management")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings"):
            save_all_data()
            st.success("Settings saved!")
    
    with col2:
        if st.button("📤 Export All Data"):
            all_data = {
                'tasks': st.session_state.tasks,
                'delegations': st.session_state.delegations,
                'settings': st.session_state.settings,
                'export_date': datetime.now().isoformat()
            }
            json_str = json.dumps(all_data, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"task_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        uploaded_file = st.file_uploader("📥 Import Data", type=['json'])
        if uploaded_file is not None:
            try:
                import_data = json.loads(uploaded_file.read())
                st.session_state.tasks = import_data.get('tasks', [])
                st.session_state.delegations = import_data.get('delegations', [])
                st.session_state.settings.update(import_data.get('settings', {}))
                save_all_data()
                st.success("Data imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

def main():
    """Main application function"""
    st.set_page_config(
        page_title="AI Task Manager",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    st.title("🤖 AI Task & Delegation Manager")
    st.markdown("*Intelligent task extraction, management, and team collaboration*")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard", 
        "🤖 Extract Tasks", 
        "📋 Manage Tasks", 
        "📊 Analytics",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_extract_tasks()
    
    with tab3:
        render_manage_tasks()
    
    with tab4:
        render_analytics()
    
    with tab5:
        render_settings()

if __name__ == "__main__":
    main()