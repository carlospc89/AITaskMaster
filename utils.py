from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import re

def format_date(date_str: str, format_type: str = "short") -> str:
    """Format date string for display."""
    if not date_str:
        return "No date"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        if format_type == "short":
            return date_obj.strftime('%m/%d/%y')
        elif format_type == "medium":
            return date_obj.strftime('%b %d, %Y')
        elif format_type == "long":
            return date_obj.strftime('%B %d, %Y')
        elif format_type == "relative":
            return get_relative_date(date_obj)
        else:
            return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return date_str

def get_relative_date(date_obj: datetime) -> str:
    """Get relative date description (e.g., 'Today', 'Tomorrow', '3 days ago')."""
    now = datetime.now()
    diff = (date_obj.date() - now.date()).days
    
    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Tomorrow"
    elif diff == -1:
        return "Yesterday"
    elif diff > 1:
        if diff <= 7:
            return f"In {diff} days"
        else:
            return f"In {diff // 7} week{'s' if diff // 7 > 1 else ''}"
    else:  # diff < -1
        abs_diff = abs(diff)
        if abs_diff <= 7:
            return f"{abs_diff} days ago"
        else:
            return f"{abs_diff // 7} week{'s' if abs_diff // 7 > 1 else ''} ago"

def get_priority_color(priority: str) -> str:
    """Get color code for priority level."""
    color_map = {
        'Critical': '#FF6B6B',  # Red
        'High': '#FF8E53',      # Orange
        'Medium': '#4ECDC4',    # Teal
        'Low': '#45B7D1'        # Blue
    }
    return color_map.get(priority, '#95A5A6')  # Default gray

def get_status_color(status: str) -> str:
    """Get color code for task status."""
    color_map = {
        'Not Started': '#95A5A6',   # Gray
        'In Progress': '#3498DB',   # Blue
        'Completed': '#2ECC71',     # Green
        'On Hold': '#F39C12',       # Yellow
        'Cancelled': '#E74C3C'      # Red
    }
    return color_map.get(status, '#95A5A6')

def calculate_urgency_score(task: Dict[str, Any]) -> float:
    """Calculate urgency score based on due date, priority, and other factors."""
    score = 0.0
    
    # Priority weight (40% of score)
    priority_weights = {
        'Critical': 4,
        'High': 3,
        'Medium': 2,
        'Low': 1
    }
    priority = task.get('priority', 'Medium')
    score += priority_weights.get(priority, 2) * 10
    
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

def is_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    if not task.get('due_date') or task.get('status') == 'Completed':
        return False
    
    try:
        due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
        return due_date.date() < datetime.now().date()
    except:
        return False

def get_days_until_due(task: Dict[str, Any]) -> Optional[int]:
    """Get number of days until task is due."""
    if not task.get('due_date'):
        return None
    
    try:
        due_date = datetime.strptime(task['due_date'], '%Y-%m-%d')
        return (due_date.date() - datetime.now().date()).days
    except:
        return None

def clean_text(text: str) -> str:
    """Clean and normalize text input."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-.,!?:;()[\]{}@#$%&*+=<>/\\|`~]', '', text)
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_id() -> int:
    """Generate a simple ID based on timestamp."""
    return int(datetime.now().timestamp() * 1000)

def format_duration(hours: float) -> str:
    """Format duration in hours to human-readable format."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}m"
    elif hours < 8:
        return f"{hours:.1f}h"
    else:
        days = hours / 8
        if days >= 1:
            return f"{days:.1f}d"
        else:
            return f"{hours:.1f}h"

def calculate_completion_percentage(tasks: List[Dict[str, Any]]) -> float:
    """Calculate completion percentage for a list of tasks."""
    if not tasks:
        return 0.0
    
    completed_tasks = len([t for t in tasks if t.get('status') == 'Completed'])
    return (completed_tasks / len(tasks)) * 100

def get_workload_status(total_hours: float, available_hours: float = 8.0) -> Dict[str, Any]:
    """Get workload status and recommendations."""
    if total_hours == 0:
        return {
            'status': 'no_tasks',
            'message': 'No tasks scheduled',
            'color': '#95A5A6',
            'utilization': 0
        }
    
    utilization = (total_hours / available_hours) * 100
    
    if utilization <= 50:
        return {
            'status': 'light',
            'message': 'Light workload',
            'color': '#2ECC71',
            'utilization': utilization
        }
    elif utilization <= 80:
        return {
            'status': 'normal',
            'message': 'Normal workload',
            'color': '#3498DB',
            'utilization': utilization
        }
    elif utilization <= 100:
        return {
            'status': 'busy',
            'message': 'Busy day',
            'color': '#F39C12',
            'utilization': utilization
        }
    else:
        return {
            'status': 'overloaded',
            'message': 'Overloaded',
            'color': '#E74C3C',
            'utilization': utilization
        }

def sort_tasks_by_priority(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort tasks by priority and urgency."""
    priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    
    return sorted(tasks, key=lambda x: (
        priority_order.get(x.get('priority', 'Medium'), 2),
        get_days_until_due(x) or 999,  # Tasks without due dates go to the end
        x.get('title', '').lower()
    ))

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for categorization."""
    if not text:
        return []
    
    # Common keywords for different categories
    category_keywords = {
        'strategic': ['strategy', 'strategic', 'planning', 'roadmap', 'vision', 'goals', 'objectives', 'direction'],
        'technical': ['code', 'development', 'programming', 'technical', 'architecture', 'design', 'implementation', 'bug', 'feature'],
        'meeting': ['meeting', 'call', 'discussion', 'sync', 'standup', 'review', 'presentation', 'demo'],
        'administrative': ['admin', 'paperwork', 'documentation', 'report', 'filing', 'compliance', 'process', 'procedure']
    }
    
    text_lower = text.lower()
    found_keywords = []
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
    
    return list(set(found_keywords))  # Remove duplicates

def suggest_category(text: str) -> str:
    """Suggest category based on text content."""
    keywords = extract_keywords(text)
    
    category_scores = {
        'Strategic': 0,
        'Technical': 0,
        'Meeting': 0,
        'Administrative': 0,
        'Review': 0,
        'Other': 0
    }
    
    # Score based on keywords
    strategic_keywords = ['strategy', 'strategic', 'planning', 'roadmap', 'vision', 'goals', 'objectives']
    technical_keywords = ['code', 'development', 'programming', 'technical', 'architecture', 'design', 'implementation']
    meeting_keywords = ['meeting', 'call', 'discussion', 'sync', 'standup', 'presentation', 'demo']
    admin_keywords = ['admin', 'paperwork', 'documentation', 'report', 'filing', 'compliance', 'process']
    review_keywords = ['review', 'feedback', 'evaluation', 'assessment', 'analysis', 'audit']
    
    for keyword in keywords:
        if keyword in strategic_keywords:
            category_scores['Strategic'] += 1
        elif keyword in technical_keywords:
            category_scores['Technical'] += 1
        elif keyword in meeting_keywords:
            category_scores['Meeting'] += 1
        elif keyword in admin_keywords:
            category_scores['Administrative'] += 1
        elif keyword in review_keywords:
            category_scores['Review'] += 1
    
    # Return category with highest score, default to 'Other'
    max_score = max(category_scores.values())
    if max_score == 0:
        return 'Other'
    
    return max(category_scores, key=category_scores.get)

def estimate_task_duration(text: str, category: str = 'Other') -> float:
    """Estimate task duration based on text content and category."""
    if not text:
        return 1.0
    
    # Base estimates by category (in hours)
    base_estimates = {
        'Strategic': 4.0,
        'Technical': 6.0,
        'Meeting': 1.0,
        'Administrative': 2.0,
        'Review': 2.0,
        'Other': 2.0
    }
    
    base_estimate = base_estimates.get(category, 2.0)
    
    # Adjust based on text complexity indicators
    text_lower = text.lower()
    
    # Complexity indicators
    complex_indicators = ['complex', 'detailed', 'comprehensive', 'thorough', 'extensive', 'complete']
    simple_indicators = ['simple', 'quick', 'brief', 'short', 'basic', 'minimal']
    
    complexity_score = 0
    for indicator in complex_indicators:
        if indicator in text_lower:
            complexity_score += 1
    
    for indicator in simple_indicators:
        if indicator in text_lower:
            complexity_score -= 1
    
    # Adjust estimate based on complexity
    if complexity_score > 0:
        base_estimate *= (1 + complexity_score * 0.5)
    elif complexity_score < 0:
        base_estimate *= max(0.5, 1 + complexity_score * 0.3)
    
    # Round to reasonable increments
    if base_estimate <= 1:
        return round(base_estimate * 2) / 2  # Round to 0.5 hour increments
    elif base_estimate <= 4:
        return round(base_estimate)  # Round to hour increments
    else:
        return round(base_estimate / 2) * 2  # Round to 2-hour increments
    
def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_week_range(date_obj: datetime) -> tuple:
    """Get the start and end dates of the week containing the given date."""
    # Monday = 0, Sunday = 6
    days_since_monday = date_obj.weekday()
    start_of_week = date_obj - timedelta(days=days_since_monday)
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week.date(), end_of_week.date()

def get_month_range(date_obj: datetime) -> tuple:
    """Get the start and end dates of the month containing the given date."""
    start_of_month = date_obj.replace(day=1).date()
    
    # Get the last day of the month
    if date_obj.month == 12:
        end_of_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = date_obj.replace(month=date_obj.month + 1, day=1) - timedelta(days=1)
    
    return start_of_month, end_of_month.date()
