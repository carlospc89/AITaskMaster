import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class TaskManager:
    def __init__(self):
        self.priority_weights = {
            'Critical': 4,
            'High': 3,
            'Medium': 2,
            'Low': 1
        }
    
    def calculate_urgency_score(self, task: Dict[str, Any]) -> float:
        """Calculate urgency score based on due date, priority, and other factors."""
        score = 0.0
        
        # Priority weight (40% of score)
        priority = task.get('priority', 'Medium')
        score += self.priority_weights.get(priority, 2) * 10
        
        # Due date urgency (40% of score)
        if task.get('due_date'):
            try:
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
                days_until_due = (due_date - datetime.now()).days
                
                if days_until_due <= 0:  # Overdue
                    score += 40
                elif days_until_due <= 1:
                    score += 35
                elif days_until_due <= 3:
                    score += 25
                elif days_until_due <= 7:
                    score += 15
                elif days_until_due <= 14:
                    score += 10
                else:
                    score += 5
            except:
                score += 5  # Default if date parsing fails
        
        # Category importance (10% of score)
        category_weights = {
            'Strategic': 4,
            'Technical': 3,
            'Meeting': 2,
            'Review': 2,
            'Administrative': 1,
            'Other': 1
        }
        category = task.get('category', 'Other')
        score += category_weights.get(category, 1) * 2.5
        
        # Estimated hours factor (10% of score)
        # Longer tasks get slightly higher urgency to prevent postponement
        estimated_hours = float(task.get('estimated_hours', 1.0))
        if estimated_hours > 8:
            score += 5
        elif estimated_hours > 4:
            score += 3
        else:
            score += 1
        
        return min(score, 100)  # Cap at 100
    
    def auto_prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Automatically prioritize tasks based on multiple factors."""
        for task in tasks:
            urgency_score = self.calculate_urgency_score(task)
            
            # Map urgency score to priority
            if urgency_score >= 80:
                task['priority'] = 'Critical'
            elif urgency_score >= 60:
                task['priority'] = 'High'
            elif urgency_score >= 40:
                task['priority'] = 'Medium'
            else:
                task['priority'] = 'Low'
            
            task['urgency_score'] = urgency_score
        
        return sorted(tasks, key=lambda x: x.get('urgency_score', 0), reverse=True)
    
    def suggest_task_breakdown(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest breaking down large tasks into smaller subtasks."""
        estimated_hours = float(task.get('estimated_hours', 1.0))
        
        if estimated_hours <= 4:
            return []  # No breakdown needed for small tasks
        
        # Simple breakdown suggestions based on task category
        category = task.get('category', 'Other')
        title = task.get('title', '')
        description = task.get('description', '')
        
        subtasks = []
        
        if category == 'Strategic':
            subtasks = [
                {'title': f"{title} - Research & Analysis", 'hours': estimated_hours * 0.3},
                {'title': f"{title} - Planning & Design", 'hours': estimated_hours * 0.4},
                {'title': f"{title} - Implementation", 'hours': estimated_hours * 0.2},
                {'title': f"{title} - Review & Finalization", 'hours': estimated_hours * 0.1}
            ]
        elif category == 'Technical':
            subtasks = [
                {'title': f"{title} - Requirements Analysis", 'hours': estimated_hours * 0.2},
                {'title': f"{title} - Technical Design", 'hours': estimated_hours * 0.3},
                {'title': f"{title} - Development", 'hours': estimated_hours * 0.4},
                {'title': f"{title} - Testing & Documentation", 'hours': estimated_hours * 0.1}
            ]
        elif category == 'Review':
            subtasks = [
                {'title': f"{title} - Initial Review", 'hours': estimated_hours * 0.4},
                {'title': f"{title} - Detailed Analysis", 'hours': estimated_hours * 0.4},
                {'title': f"{title} - Feedback & Follow-up", 'hours': estimated_hours * 0.2}
            ]
        else:
            # Generic breakdown
            num_parts = min(4, max(2, int(estimated_hours / 2)))
            hours_per_part = estimated_hours / num_parts
            
            for i in range(num_parts):
                subtasks.append({
                    'title': f"{title} - Part {i+1}",
                    'hours': hours_per_part
                })
        
        # Add metadata to subtasks
        for i, subtask in enumerate(subtasks):
            subtask.update({
                'description': f"Subtask {i+1} of: {description}",
                'priority': task.get('priority', 'Medium'),
                'category': category,
                'parent_task_id': task.get('id'),
                'estimated_hours': round(subtask['hours'], 1)
            })
        
        return subtasks
    
    def calculate_daily_capacity(self, tasks: List[Dict[str, Any]], date: datetime) -> Dict[str, Any]:
        """Calculate daily workload capacity and recommendations."""
        date_str = date.strftime('%Y-%m-%d')
        
        # Get tasks due on this date
        due_tasks = [t for t in tasks if t.get('due_date') == date_str and t.get('status') != 'Completed']
        
        total_hours = sum([float(t.get('estimated_hours', 0)) for t in due_tasks])
        
        # Assume 8-hour working day with 20% buffer for meetings/interruptions
        available_hours = 6.4
        
        capacity_analysis = {
            'date': date_str,
            'total_required_hours': total_hours,
            'available_hours': available_hours,
            'utilization_percentage': (total_hours / available_hours * 100) if available_hours > 0 else 0,
            'tasks_count': len(due_tasks),
            'status': 'normal'
        }
        
        # Determine status
        if total_hours > available_hours * 1.2:
            capacity_analysis['status'] = 'overloaded'
            capacity_analysis['recommendation'] = 'Consider rescheduling some tasks or delegating'
        elif total_hours > available_hours:
            capacity_analysis['status'] = 'at_capacity'
            capacity_analysis['recommendation'] = 'Day is fully booked, avoid adding more tasks'
        elif total_hours < available_hours * 0.5:
            capacity_analysis['status'] = 'underutilized'
            capacity_analysis['recommendation'] = 'Opportunity to advance future tasks'
        else:
            capacity_analysis['recommendation'] = 'Well-balanced workload'
        
        return capacity_analysis
    
    def generate_calendar_entries(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate calendar entries for tasks with optimal time allocation."""
        calendar_entries = []
        
        # Sort tasks by priority and due date
        sorted_tasks = sorted(tasks, key=lambda x: (
            ['Critical', 'High', 'Medium', 'Low'].index(x.get('priority', 'Medium')),
            x.get('due_date', '9999-12-31')
        ))
        
        for task in sorted_tasks:
            if task.get('status') == 'Completed':
                continue
            
            due_date = task.get('due_date')
            if not due_date:
                continue
            
            estimated_hours = float(task.get('estimated_hours', 1.0))
            
            # Suggest optimal time based on task category and priority
            category = task.get('category', 'Other')
            priority = task.get('priority', 'Medium')
            
            # Time of day preferences
            if category == 'Strategic' or priority == 'Critical':
                suggested_time = '09:00'  # Morning for important strategic work
            elif category == 'Technical':
                suggested_time = '10:00'  # Late morning for deep work
            elif category == 'Meeting':
                suggested_time = '14:00'  # Afternoon for collaborative work
            elif category == 'Administrative':
                suggested_time = '16:00'  # Late afternoon for admin tasks
            else:
                suggested_time = '11:00'  # Default mid-morning
            
            calendar_entry = {
                'task_id': task.get('id'),
                'title': task.get('title'),
                'description': task.get('description', ''),
                'start_date': due_date,
                'start_time': suggested_time,
                'duration_hours': estimated_hours,
                'priority': priority,
                'category': category,
                'calendar_format': {
                    'summary': f"[{priority}] {task.get('title')}",
                    'description': f"Category: {category}\nEstimated time: {estimated_hours}h\n\n{task.get('description', '')}",
                    'start': f"{due_date}T{suggested_time}:00",
                    'end': self._calculate_end_time(due_date, suggested_time, estimated_hours)
                }
            }
            
            calendar_entries.append(calendar_entry)
        
        return calendar_entries
    
    def _calculate_end_time(self, date: str, start_time: str, duration_hours: float) -> str:
        """Calculate end time for calendar entry."""
        try:
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(hours=duration_hours)
            return end_datetime.strftime("%Y-%m-%dT%H:%M:00")
        except:
            return f"{date}T{start_time}:00"
    
    def calculate_productivity_metrics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate various productivity metrics."""
        if not tasks:
            return {}
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status') == 'Completed'])
        
        # Completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Average completion time (for completed tasks with created and completed dates)
        completion_times = []
        for task in tasks:
            if task.get('status') == 'Completed' and task.get('created_date') and task.get('completed_date'):
                try:
                    created = datetime.strptime(task['created_date'], '%Y-%m-%d')
                    completed_date = datetime.strptime(task['completed_date'], '%Y-%m-%d')
                    completion_times.append((completed_date - created).days)
                except:
                    continue
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None
        
        # Priority distribution
        priority_distribution = {}
        for task in tasks:
            priority = task.get('priority', 'Medium')
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        # Overdue tasks
        overdue_tasks = 0
        for task in tasks:
            if task.get('due_date') and task.get('status') != 'Completed':
                try:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
                    if due_date < datetime.now():
                        overdue_tasks += 1
                except:
                    continue
        
        # Workload distribution by category
        category_workload = {}
        for task in tasks:
            category = task.get('category', 'Other')
            hours = float(task.get('estimated_hours', 0))
            category_workload[category] = category_workload.get(category, 0) + hours
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 1),
            'average_completion_time_days': round(avg_completion_time, 1) if avg_completion_time else None,
            'overdue_tasks': overdue_tasks,
            'priority_distribution': priority_distribution,
            'category_workload_hours': category_workload,
            'total_estimated_hours': sum([float(t.get('estimated_hours', 0)) for t in tasks]),
            'completed_hours': sum([float(t.get('estimated_hours', 0)) for t in tasks if t.get('status') == 'Completed'])
        }
    
    def suggest_task_optimizations(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Suggest optimizations for task management."""
        suggestions = []
        
        if not tasks:
            return ["Start by adding some tasks to get optimization suggestions."]
        
        metrics = self.calculate_productivity_metrics(tasks)
        
        # Completion rate suggestions
        if metrics.get('completion_rate', 0) < 50:
            suggestions.append("📈 Low completion rate detected. Consider breaking large tasks into smaller, manageable chunks.")
        
        # Overdue tasks
        if metrics.get('overdue_tasks', 0) > 0:
            suggestions.append(f"⏰ {metrics['overdue_tasks']} overdue tasks need immediate attention. Consider rescheduling or delegating.")
        
        # Priority distribution analysis
        priority_dist = metrics.get('priority_distribution', {})
        critical_count = priority_dist.get('Critical', 0)
        high_count = priority_dist.get('High', 0)
        
        if critical_count > 5:
            suggestions.append("🔥 Too many critical tasks. Review priorities and consider if all are truly critical.")
        
        if critical_count + high_count > len(tasks) * 0.7:
            suggestions.append("⚡ Most tasks are high priority. This may indicate poor prioritization or unrealistic expectations.")
        
        # Category workload analysis
        category_workload = metrics.get('category_workload_hours', {})
        if category_workload:
            max_category = max(category_workload, key=category_workload.get)
            max_hours = category_workload[max_category]
            total_hours = metrics.get('total_estimated_hours', 1)
            
            if max_hours > total_hours * 0.6:
                suggestions.append(f"📊 {max_category} tasks dominate your workload ({max_hours:.1f}h). Consider delegating or redistributing.")
        
        # Task size analysis
        large_tasks = [t for t in tasks if float(t.get('estimated_hours', 0)) > 8]
        if large_tasks:
            suggestions.append(f"📋 {len(large_tasks)} tasks require 8+ hours. Break them down for better progress tracking.")
        
        # Delegation opportunities
        admin_tasks = [t for t in tasks if t.get('category') == 'Administrative' and t.get('status') != 'Completed']
        if len(admin_tasks) > 3:
            suggestions.append("👥 Consider delegating administrative tasks to focus on strategic priorities.")
        
        if not suggestions:
            suggestions.append("✅ Your task management looks well-optimized! Keep up the good work.")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def calculate_avg_completion_time(self, tasks: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average completion time for tasks."""
        completion_times = []
        for task in tasks:
            if task.get('status') == 'Completed' and task.get('created_date') and task.get('completed_date'):
                try:
                    created = datetime.strptime(task['created_date'], '%Y-%m-%d')
                    completed_date = datetime.strptime(task['completed_date'], '%Y-%m-%d')
                    completion_times.append((completed_date - created).days)
                except:
                    continue
        
        return sum(completion_times) / len(completion_times) if completion_times else None
    
    def calculate_productivity_score(self, tasks: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate overall productivity score."""
        if not tasks:
            return None
        
        metrics = self.calculate_productivity_metrics(tasks)
        
        # Weighted scoring
        completion_weight = 0.4
        timeliness_weight = 0.3
        efficiency_weight = 0.3
        
        # Completion score
        completion_score = metrics.get('completion_rate', 0)
        
        # Timeliness score (inverse of overdue percentage)
        overdue_percentage = (metrics.get('overdue_tasks', 0) / metrics.get('total_tasks', 1)) * 100
        timeliness_score = max(0, 100 - overdue_percentage * 2)  # Penalize overdue tasks heavily
        
        # Efficiency score (based on task size and completion time)
        avg_completion = metrics.get('average_completion_time_days')
        if avg_completion and avg_completion > 0:
            efficiency_score = max(0, 100 - (avg_completion - 3) * 10)  # Optimal is ~3 days
        else:
            efficiency_score = 100  # No data means assume good efficiency
        
        # Calculate weighted score
        productivity_score = (
            completion_score * completion_weight +
            timeliness_score * timeliness_weight +
            efficiency_score * efficiency_weight
        )
        
        return min(100, max(0, productivity_score))
