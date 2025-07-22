import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class VisualizationManager:
    def __init__(self):
        self.color_map = {
            'Critical': '#FF0000',
            'High': '#FF6B6B',
            'Medium': '#4ECDC4',
            'Low': '#45B7D1'
        }
        
        self.status_colors = {
            'Not Started': '#95A5A6',
            'In Progress': '#3498DB',
            'Completed': '#2ECC71',
            'On Hold': '#F39C12'
        }
    
    def create_gantt_chart(self, tasks: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create a Gantt chart for task timeline visualization."""
        if not tasks:
            return None
        
        # Filter tasks with due dates
        tasks_with_dates = [t for t in tasks if t.get('due_date')]
        
        if not tasks_with_dates:
            return None
        
        gantt_data = []
        
        for task in tasks_with_dates:
            try:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
                estimated_hours = float(task.get('estimated_hours', 1.0))
                
                # Calculate start date (working backwards from due date)
                # Assume 8 hours per working day
                working_days = max(1, estimated_hours / 8)
                start_date = due_date - timedelta(days=working_days)
                
                gantt_data.append({
                    'Task': task.get('title', 'Untitled'),
                    'Start': start_date,
                    'Finish': due_date,
                    'Priority': task.get('priority', 'Medium'),
                    'Status': task.get('status', 'Not Started'),
                    'Category': task.get('category', 'Other'),
                    'Hours': estimated_hours
                })
            except:
                continue
        
        if not gantt_data:
            return None
        
        df = pd.DataFrame(gantt_data)
        
        # Create Gantt chart
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Priority",
            color_discrete_map=self.color_map,
            title="Project Timeline - Gantt Chart",
            hover_data=["Status", "Category", "Hours"]
        )
        
        # Customize layout
        fig.update_layout(
            height=max(400, len(gantt_data) * 40),
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            showlegend=True,
            hovermode='y unified'
        )
        
        # Add status indicators
        for i, row in df.iterrows():
            status_color = self.status_colors.get(row['Status'], '#95A5A6')
            fig.add_shape(
                type="rect",
                x0=row['Start'],
                x1=row['Finish'],
                y0=i - 0.4,
                y1=i + 0.4,
                line=dict(color=status_color, width=2),
                fillcolor=status_color,
                opacity=0.3
            )
        
        return fig
    
    def create_calendar_view(self, tasks: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> Optional[go.Figure]:
        """Create a calendar view of tasks."""
        if not tasks:
            return None
        
        # Filter tasks within date range
        tasks_in_range = []
        for task in tasks:
            if task.get('due_date'):
                try:
                    task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    if start_date <= task_date <= end_date:
                        tasks_in_range.append(task)
                except:
                    continue
        
        if not tasks_in_range:
            return None
        
        # Create calendar data
        calendar_data = []
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Group tasks by date
        tasks_by_date = {}
        for task in tasks_in_range:
            task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
            if task_date not in tasks_by_date:
                tasks_by_date[task_date] = []
            tasks_by_date[task_date].append(task)
        
        # Create heatmap data
        weeks = []
        days = []
        values = []
        hover_texts = []
        
        for date in date_range:
            week = date.isocalendar()[1]  # ISO week number
            day = date.weekday()  # Monday = 0, Sunday = 6
            
            task_count = len(tasks_by_date.get(date, []))
            task_hours = sum([float(t.get('estimated_hours', 0)) for t in tasks_by_date.get(date, [])])
            
            weeks.append(week)
            days.append(day)
            values.append(task_hours)
            
            # Create hover text
            if task_count > 0:
                task_titles = [t.get('title', 'Untitled') for t in tasks_by_date[date]]
                hover_text = f"Date: {date}<br>Tasks: {task_count}<br>Hours: {task_hours:.1f}<br>" + "<br>".join(task_titles[:3])
                if task_count > 3:
                    hover_text += f"<br>... and {task_count - 3} more"
            else:
                hover_text = f"Date: {date}<br>No tasks"
            
            hover_texts.append(hover_text)
        
        # Create calendar heatmap
        fig = go.Figure(data=go.Scatter(
            x=weeks,
            y=days,
            mode='markers',
            marker=dict(
                size=20,
                color=values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Hours")
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Task Calendar View",
            xaxis_title="Week",
            yaxis_title="Day of Week",
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ),
            height=400
        )
        
        return fig
    
    def create_priority_distribution_chart(self, tasks: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create priority distribution visualization."""
        if not tasks:
            return None
        
        priority_counts = {}
        for task in tasks:
            priority = task.get('priority', 'Medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        if not priority_counts:
            return None
        
        fig = px.pie(
            values=list(priority_counts.values()),
            names=list(priority_counts.keys()),
            title="Task Priority Distribution",
            color_discrete_map=self.color_map
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        return fig
    
    def create_status_tracking_chart(self, tasks: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create status tracking visualization."""
        if not tasks:
            return None
        
        status_counts = {}
        for task in tasks:
            status = task.get('status', 'Not Started')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if not status_counts:
            return None
        
        fig = px.bar(
            x=list(status_counts.keys()),
            y=list(status_counts.values()),
            title="Task Status Distribution",
            color=list(status_counts.keys()),
            color_discrete_map=self.status_colors
        )
        
        fig.update_layout(
            xaxis_title="Status",
            yaxis_title="Number of Tasks",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_workload_analysis_chart(self, tasks: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create workload analysis by category."""
        if not tasks:
            return None
        
        category_hours = {}
        for task in tasks:
            category = task.get('category', 'Other')
            hours = float(task.get('estimated_hours', 0))
            category_hours[category] = category_hours.get(category, 0) + hours
        
        if not category_hours:
            return None
        
        fig = px.bar(
            x=list(category_hours.keys()),
            y=list(category_hours.values()),
            title="Workload Distribution by Category (Hours)",
            color=list(category_hours.values()),
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="Total Hours",
            height=400
        )
        
        return fig
    
    def calculate_daily_workload(self, tasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate daily workload for timeline visualization."""
        daily_workload = {}
        
        for task in tasks:
            if task.get('due_date') and task.get('status') != 'Completed':
                due_date = task['due_date']
                hours = float(task.get('estimated_hours', 0))
                daily_workload[due_date] = daily_workload.get(due_date, 0) + hours
        
        return daily_workload
    
    def create_burndown_chart(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, List]]:
        """Create burndown chart data."""
        if not tasks:
            return None
        
        # Get tasks with created dates
        tasks_with_dates = [t for t in tasks if t.get('created_date')]
        
        if not tasks_with_dates:
            return None
        
        # Sort by created date
        tasks_with_dates.sort(key=lambda x: x.get('created_date', ''))
        
        # Calculate cumulative data
        dates = []
        remaining_tasks = []
        completed_tasks = []
        
        all_dates = set()
        for task in tasks_with_dates:
            all_dates.add(task.get('created_date'))
            if task.get('completed_date'):
                all_dates.add(task.get('completed_date'))
        
        sorted_dates = sorted(all_dates)
        
        for date in sorted_dates:
            # Count tasks created by this date
            total_by_date = len([t for t in tasks_with_dates if t.get('created_date') <= date])
            
            # Count tasks completed by this date
            completed_by_date = len([t for t in tasks_with_dates 
                                   if t.get('completed_date') and t.get('completed_date') <= date])
            
            remaining_by_date = total_by_date - completed_by_date
            
            dates.append(date)
            remaining_tasks.append(remaining_by_date)
            completed_tasks.append(completed_by_date)
        
        return {
            'dates': dates,
            'remaining_tasks': remaining_tasks,
            'completed_tasks': completed_tasks
        }
    
    def create_delegation_performance_chart(self, delegations: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create delegation performance visualization."""
        if not delegations:
            return None
        
        # Calculate completion rates by delegate
        delegate_stats = {}
        for delegation in delegations:
            delegate = delegation.get('delegate_to', 'Unknown')
            if delegate not in delegate_stats:
                delegate_stats[delegate] = {'total': 0, 'completed': 0}
            
            delegate_stats[delegate]['total'] += 1
            if delegation.get('status') == 'Completed':
                delegate_stats[delegate]['completed'] += 1
        
        if not delegate_stats:
            return None
        
        delegates = list(delegate_stats.keys())
        completion_rates = [
            (delegate_stats[d]['completed'] / delegate_stats[d]['total'] * 100)
            for d in delegates
        ]
        total_tasks = [delegate_stats[d]['total'] for d in delegates]
        
        fig = go.Figure(data=[
            go.Bar(
                x=delegates,
                y=completion_rates,
                text=[f"{rate:.1f}% ({delegate_stats[d]['completed']}/{delegate_stats[d]['total']})" 
                      for d, rate in zip(delegates, completion_rates)],
                textposition='auto',
                marker_color='lightblue',
                name='Completion Rate'
            )
        ])
        
        fig.update_layout(
            title="Delegation Performance by Team Member",
            xaxis_title="Team Member",
            yaxis_title="Completion Rate (%)",
            height=400,
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    
    def create_timeline_overview(self, tasks: List[Dict[str, Any]], delegations: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create comprehensive timeline overview."""
        if not tasks and not delegations:
            return None
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Tasks Timeline', 'Delegations Timeline'),
            vertical_spacing=0.1,
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
        )
        
        # Tasks timeline
        if tasks:
            task_dates = []
            task_counts = []
            
            # Count tasks by due date
            tasks_by_date = {}
            for task in tasks:
                if task.get('due_date'):
                    date = task['due_date']
                    tasks_by_date[date] = tasks_by_date.get(date, 0) + 1
            
            sorted_dates = sorted(tasks_by_date.keys())
            task_dates = sorted_dates
            task_counts = [tasks_by_date[date] for date in sorted_dates]
            
            fig.add_trace(
                go.Scatter(
                    x=task_dates,
                    y=task_counts,
                    mode='lines+markers',
                    name='Tasks Due',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
        
        # Delegations timeline
        if delegations:
            delegation_dates = []
            delegation_counts = []
            
            # Count delegations by due date
            delegations_by_date = {}
            for delegation in delegations:
                if delegation.get('due_date'):
                    date = delegation['due_date']
                    delegations_by_date[date] = delegations_by_date.get(date, 0) + 1
            
            sorted_dates = sorted(delegations_by_date.keys())
            delegation_dates = sorted_dates
            delegation_counts = [delegations_by_date[date] for date in sorted_dates]
            
            fig.add_trace(
                go.Scatter(
                    x=delegation_dates,
                    y=delegation_counts,
                    mode='lines+markers',
                    name='Delegations Due',
                    line=dict(color='green')
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            title="Timeline Overview",
            height=600,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Number of Tasks", row=1, col=1)
        fig.update_yaxes(title_text="Number of Delegations", row=2, col=1)
        
        return fig
