import json
import os
from typing import List, Dict, Any
from datetime import datetime

class DataHandler:
    def __init__(self):
        self.tasks_file = "tasks_data.json"
        self.delegations_file = "delegations_data.json"
        self.settings_file = "settings.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.tasks_file = os.path.join("data", self.tasks_file)
        self.delegations_file = os.path.join("data", self.delegations_file)
        self.settings_file = os.path.join("data", self.settings_file)
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> bool:
        """Save tasks to JSON file."""
        try:
            # Add timestamp
            data = {
                'tasks': tasks,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from JSON file."""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data formats
                if isinstance(data, dict) and 'tasks' in data:
                    return data['tasks']
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                return []
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []
    
    def save_delegations(self, delegations: List[Dict[str, Any]]) -> bool:
        """Save delegations to JSON file."""
        try:
            # Add timestamp
            data = {
                'delegations': delegations,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.delegations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving delegations: {e}")
            return False
    
    def load_delegations(self) -> List[Dict[str, Any]]:
        """Load delegations from JSON file."""
        try:
            if os.path.exists(self.delegations_file):
                with open(self.delegations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data formats
                if isinstance(data, dict) and 'delegations' in data:
                    return data['delegations']
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                return []
        except Exception as e:
            print(f"Error loading delegations: {e}")
            return []
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save application settings."""
        try:
            data = {
                'settings': settings,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """Load application settings."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'settings' in data:
                    return data['settings']
                else:
                    return self.get_default_settings()
            else:
                return self.get_default_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            'auto_save': True,
            'ai_suggestions_enabled': True,
            'default_task_duration': 1.0,
            'working_hours_per_day': 8,
            'notification_preferences': {
                'overdue_tasks': True,
                'approaching_deadlines': True,
                'delegation_updates': True
            },
            'display_preferences': {
                'tasks_per_page': 20,
                'default_sort': 'due_date',
                'show_completed_tasks': False
            },
            'calendar_integration': {
                'enabled': False,
                'calendar_type': 'google',
                'sync_frequency': 'daily'
            }
        }
    
    def backup_data(self) -> bool:
        """Create backup of all data files."""
        try:
            backup_dir = os.path.join("data", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup tasks
            if os.path.exists(self.tasks_file):
                backup_tasks_file = os.path.join(backup_dir, f"tasks_backup_{timestamp}.json")
                with open(self.tasks_file, 'r', encoding='utf-8') as src:
                    with open(backup_tasks_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Backup delegations
            if os.path.exists(self.delegations_file):
                backup_delegations_file = os.path.join(backup_dir, f"delegations_backup_{timestamp}.json")
                with open(self.delegations_file, 'r', encoding='utf-8') as src:
                    with open(backup_delegations_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Backup settings
            if os.path.exists(self.settings_file):
                backup_settings_file = os.path.join(backup_dir, f"settings_backup_{timestamp}.json")
                with open(self.settings_file, 'r', encoding='utf-8') as src:
                    with open(backup_settings_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_from_backup(self, backup_timestamp: str) -> bool:
        """Restore data from backup."""
        try:
            backup_dir = os.path.join("data", "backups")
            
            # Restore tasks
            backup_tasks_file = os.path.join(backup_dir, f"tasks_backup_{backup_timestamp}.json")
            if os.path.exists(backup_tasks_file):
                with open(backup_tasks_file, 'r', encoding='utf-8') as src:
                    with open(self.tasks_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Restore delegations
            backup_delegations_file = os.path.join(backup_dir, f"delegations_backup_{backup_timestamp}.json")
            if os.path.exists(backup_delegations_file):
                with open(backup_delegations_file, 'r', encoding='utf-8') as src:
                    with open(self.delegations_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Restore settings
            backup_settings_file = os.path.join(backup_dir, f"settings_backup_{backup_timestamp}.json")
            if os.path.exists(backup_settings_file):
                with open(backup_settings_file, 'r', encoding='utf-8') as src:
                    with open(self.settings_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            return True
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def export_data_csv(self, data_type: str) -> str:
        """Export data to CSV format."""
        try:
            if data_type == 'tasks':
                tasks = self.load_tasks()
                if not tasks:
                    return ""
                
                import pandas as pd
                df = pd.DataFrame(tasks)
                return df.to_csv(index=False)
            
            elif data_type == 'delegations':
                delegations = self.load_delegations()
                if not delegations:
                    return ""
                
                import pandas as pd
                df = pd.DataFrame(delegations)
                return df.to_csv(index=False)
            
            else:
                return ""
                
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return ""
    
    def import_data_csv(self, csv_content: str, data_type: str) -> bool:
        """Import data from CSV format."""
        try:
            import pandas as pd
            from io import StringIO
            
            df = pd.read_csv(StringIO(csv_content))
            data = df.to_dict('records')
            
            if data_type == 'tasks':
                # Validate and clean task data
                cleaned_tasks = []
                for task in data:
                    # Ensure required fields
                    if 'title' in task and task['title']:
                        cleaned_task = {
                            'id': task.get('id', len(self.load_tasks()) + len(cleaned_tasks) + 1),
                            'title': str(task['title']),
                            'description': str(task.get('description', '')),
                            'priority': task.get('priority', 'Medium'),
                            'status': task.get('status', 'Not Started'),
                            'category': task.get('category', 'Other'),
                            'due_date': task.get('due_date'),
                            'estimated_hours': float(task.get('estimated_hours', 1.0)),
                            'created_date': task.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                            'created_by_ai': bool(task.get('created_by_ai', False))
                        }
                        cleaned_tasks.append(cleaned_task)
                
                # Append to existing tasks
                existing_tasks = self.load_tasks()
                existing_tasks.extend(cleaned_tasks)
                return self.save_tasks(existing_tasks)
            
            elif data_type == 'delegations':
                # Validate and clean delegation data
                cleaned_delegations = []
                for delegation in data:
                    if 'task_title' in delegation and 'delegate_to' in delegation:
                        cleaned_delegation = {
                            'id': delegation.get('id', len(self.load_delegations()) + len(cleaned_delegations) + 1),
                            'task_title': str(delegation['task_title']),
                            'delegate_to': str(delegation['delegate_to']),
                            'priority': delegation.get('priority', 'Medium'),
                            'status': delegation.get('status', 'Assigned'),
                            'due_date': delegation.get('due_date'),
                            'notes': str(delegation.get('notes', '')),
                            'created_date': delegation.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                            'last_updated': delegation.get('last_updated', datetime.now().strftime('%Y-%m-%d'))
                        }
                        cleaned_delegations.append(cleaned_delegation)
                
                # Append to existing delegations
                existing_delegations = self.load_delegations()
                existing_delegations.extend(cleaned_delegations)
                return self.save_delegations(existing_delegations)
            
            return False
            
        except Exception as e:
            print(f"Error importing from CSV: {e}")
            return False
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        try:
            tasks = self.load_tasks()
            delegations = self.load_delegations()
            
            stats = {
                'tasks': {
                    'total_count': len(tasks),
                    'by_status': {},
                    'by_priority': {},
                    'by_category': {},
                    'ai_generated': len([t for t in tasks if t.get('created_by_ai')])
                },
                'delegations': {
                    'total_count': len(delegations),
                    'by_status': {},
                    'by_delegate': {}
                },
                'storage': {
                    'tasks_file_size': os.path.getsize(self.tasks_file) if os.path.exists(self.tasks_file) else 0,
                    'delegations_file_size': os.path.getsize(self.delegations_file) if os.path.exists(self.delegations_file) else 0,
                    'settings_file_size': os.path.getsize(self.settings_file) if os.path.exists(self.settings_file) else 0
                }
            }
            
            # Calculate task statistics
            for task in tasks:
                # Status distribution
                status = task.get('status', 'Unknown')
                stats['tasks']['by_status'][status] = stats['tasks']['by_status'].get(status, 0) + 1
                
                # Priority distribution
                priority = task.get('priority', 'Unknown')
                stats['tasks']['by_priority'][priority] = stats['tasks']['by_priority'].get(priority, 0) + 1
                
                # Category distribution
                category = task.get('category', 'Unknown')
                stats['tasks']['by_category'][category] = stats['tasks']['by_category'].get(category, 0) + 1
            
            # Calculate delegation statistics
            for delegation in delegations:
                # Status distribution
                status = delegation.get('status', 'Unknown')
                stats['delegations']['by_status'][status] = stats['delegations']['by_status'].get(status, 0) + 1
                
                # Delegate distribution
                delegate = delegation.get('delegate_to', 'Unknown')
                stats['delegations']['by_delegate'][delegate] = stats['delegations']['by_delegate'].get(delegate, 0) + 1
            
            return stats
            
        except Exception as e:
            print(f"Error getting data statistics: {e}")
            return {}
