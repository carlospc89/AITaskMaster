import json
import os
from typing import List, Dict, Any
from datetime import datetime
from database import DatabaseManager, migrate_from_json_to_db

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
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Check for existing JSON data and migrate if needed
        self._check_and_migrate_data()
    
    def _check_and_migrate_data(self):
        """Check for existing JSON data and migrate to database if found"""
        try:
            # Check if we have existing JSON data but empty database
            db_task_count = len(self.db_manager.get_all_tasks())
            
            if db_task_count == 0:
                # Check for JSON files
                json_tasks_exist = os.path.exists(self.tasks_file)
                json_delegations_exist = os.path.exists(self.delegations_file)
                json_settings_exist = os.path.exists(self.settings_file)
                
                if json_tasks_exist or json_delegations_exist or json_settings_exist:
                    print("Found existing JSON data. Migrating to database...")
                    if migrate_from_json_to_db(self, self.db_manager):
                        # Backup JSON files after successful migration
                        self._backup_json_files()
                        print("Migration completed successfully!")
                    else:
                        print("Migration failed, keeping JSON files as backup")
        except Exception as e:
            print(f"Migration check failed: {e}")
    
    def _backup_json_files(self):
        """Backup JSON files after migration"""
        backup_dir = os.path.join("data", "json_backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        for file_path in [self.tasks_file, self.delegations_file, self.settings_file]:
            if os.path.exists(file_path):
                backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}.backup")
                os.rename(file_path, backup_path)
                print(f"Backed up {file_path} to {backup_path}")
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> bool:
        """Save tasks to database."""
        try:
            # Save each task individually to the database
            for task in tasks:
                if 'created_date' not in task:
                    task['created_date'] = datetime.now().strftime('%Y-%m-%d')
                self.db_manager.save_task(task)
            return True
        except Exception as e:
            print(f"Error saving tasks: {e}")
            return False
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from database."""
        try:
            return self.db_manager.get_all_tasks()
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []
    
    def save_single_task(self, task: Dict[str, Any]) -> int:
        """Save a single task to database and return its ID"""
        if 'created_date' not in task:
            task['created_date'] = datetime.now().strftime('%Y-%m-%d')
        return self.db_manager.save_task(task)
    
    def get_task_by_id(self, task_id: int) -> Dict[str, Any]:
        """Get a specific task by ID"""
        return self.db_manager.get_task_by_id(task_id)
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID"""
        return self.db_manager.delete_task(task_id)
    
    def save_delegations(self, delegations: List[Dict[str, Any]]) -> bool:
        """Save delegations to database."""
        try:
            # Save each delegation individually to the database
            for delegation in delegations:
                if 'delegation_date' not in delegation:
                    delegation['delegation_date'] = datetime.now().strftime('%Y-%m-%d')
                self.db_manager.save_delegation(delegation)
            return True
        except Exception as e:
            print(f"Error saving delegations: {e}")
            return False
    
    def load_delegations(self) -> List[Dict[str, Any]]:
        """Load delegations from database."""
        try:
            return self.db_manager.get_all_delegations()
        except Exception as e:
            print(f"Error loading delegations: {e}")
            return []
    
    def save_single_delegation(self, delegation: Dict[str, Any]) -> int:
        """Save a single delegation to database and return its ID"""
        if 'delegation_date' not in delegation:
            delegation['delegation_date'] = datetime.now().strftime('%Y-%m-%d')
        return self.db_manager.save_delegation(delegation)
    
    def get_delegations_for_task(self, task_id: int) -> List[Dict[str, Any]]:
        """Get delegations for a specific task"""
        return self.db_manager.get_delegations_for_task(task_id)
    
    def delete_delegation(self, delegation_id: int) -> bool:
        """Delete a delegation by ID"""
        return self.db_manager.delete_delegation(delegation_id)
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save application settings to database."""
        try:
            # Save each setting individually
            for key, value in settings.items():
                self.db_manager.save_setting(key, value)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """Load application settings from database."""
        try:
            settings = self.db_manager.get_all_settings()
            if not settings:
                return self.get_default_settings()
            return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            'ai_backend': 'perplexity',
            'auto_save': True,
            'ai_suggestions_enabled': True,
            'default_task_duration': 1.0,
            'working_hours_per_day': 8,
            'extraction_temperature': 0.1,
            'max_tokens': 1000,
            'categories': ['Strategic', 'Technical', 'Meeting', 'Review', 'Administrative', 'Other'],
            'delegates': ['Developer', 'Designer', 'QA Engineer', 'Marketing Team', 'Technical Writer', 'Project Manager'],
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
        """Get statistics about stored data from database."""
        try:
            return self.db_manager.get_database_stats()
        except Exception as e:
            print(f"Error getting data statistics: {e}")
            return {}
    
    def clear_all_data(self) -> bool:
        """Clear all data from database."""
        return self.db_manager.clear_all_data()
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create backup of SQLite database."""
        try:
            import shutil
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join("data", "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"database_backup_{timestamp}.db")
            
            shutil.copy2(self.db_manager.db_path, backup_path)
            print(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"Error backing up database: {e}")
            return False
