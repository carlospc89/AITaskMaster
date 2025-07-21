"""
Database management for AI Task & Delegation Manager
Uses SQLite for persistent local storage
"""

import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import os

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(50), default='Medium')
    category = Column(String(100))
    status = Column(String(50), default='Not Started')
    due_date = Column(String(20))  # Store as string for compatibility
    created_date = Column(String(20))
    assignee = Column(String(100))
    estimated_hours = Column(Float, default=1.0)
    actual_hours = Column(Float, default=0.0)
    created_by_ai = Column(Boolean, default=False)
    urgency_score = Column(Float, default=0.0)
    completion_percentage = Column(Integer, default=0)
    notes = Column(Text)
    
    # Relationship with delegations
    delegations = relationship("Delegation", back_populates="task")

class Delegation(Base):
    __tablename__ = 'delegations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    delegated_to = Column(String(100), nullable=False)
    delegated_by = Column(String(100))
    delegation_date = Column(String(20))
    status = Column(String(50), default='Pending')
    instructions = Column(Text)
    deadline = Column(String(20))
    feedback = Column(Text)
    completion_date = Column(String(20))
    
    # Relationship with task
    task = relationship("Task", back_populates="delegations")

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_date = Column(String(20))

class DatabaseManager:
    """Manages SQLite database operations for persistent storage"""
    
    def __init__(self, db_path="data/tasks.db"):
        """Initialize database connection and create tables if needed"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f"Database initialized at: {os.path.abspath(db_path)}")
    
    def close(self):
        """Close database connection"""
        if self.session:
            self.session.close()
    
    # Task operations
    def save_task(self, task_data):
        """Save or update a task in the database"""
        try:
            # Check if task has an ID (update) or is new (insert)
            if 'id' in task_data and task_data['id']:
                # Update existing task
                task = self.session.query(Task).filter(Task.id == task_data['id']).first()
                if task:
                    for key, value in task_data.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                else:
                    # Create new task with specified ID
                    task = Task(**task_data)
                    self.session.add(task)
            else:
                # Create new task
                task_data.pop('id', None)  # Remove ID if present
                task = Task(**task_data)
                self.session.add(task)
            
            self.session.commit()
            return task.id
        except Exception as e:
            self.session.rollback()
            print(f"Error saving task: {e}")
            return None
    
    def get_all_tasks(self):
        """Retrieve all tasks from database"""
        try:
            tasks = self.session.query(Task).all()
            return [self._task_to_dict(task) for task in tasks]
        except Exception as e:
            print(f"Error retrieving tasks: {e}")
            return []
    
    def get_task_by_id(self, task_id):
        """Retrieve a specific task by ID"""
        try:
            task = self.session.query(Task).filter(Task.id == task_id).first()
            return self._task_to_dict(task) if task else None
        except Exception as e:
            print(f"Error retrieving task {task_id}: {e}")
            return None
    
    def delete_task(self, task_id):
        """Delete a task and its associated delegations"""
        try:
            # Delete associated delegations first
            self.session.query(Delegation).filter(Delegation.task_id == task_id).delete()
            
            # Delete the task
            task = self.session.query(Task).filter(Task.id == task_id).first()
            if task:
                self.session.delete(task)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting task {task_id}: {e}")
            return False
    
    # Delegation operations
    def save_delegation(self, delegation_data):
        """Save or update a delegation in the database"""
        try:
            if 'id' in delegation_data and delegation_data['id']:
                # Update existing delegation
                delegation = self.session.query(Delegation).filter(Delegation.id == delegation_data['id']).first()
                if delegation:
                    for key, value in delegation_data.items():
                        if hasattr(delegation, key):
                            setattr(delegation, key, value)
                else:
                    delegation = Delegation(**delegation_data)
                    self.session.add(delegation)
            else:
                # Create new delegation
                delegation_data.pop('id', None)
                delegation = Delegation(**delegation_data)
                self.session.add(delegation)
            
            self.session.commit()
            return delegation.id
        except Exception as e:
            self.session.rollback()
            print(f"Error saving delegation: {e}")
            return None
    
    def get_all_delegations(self):
        """Retrieve all delegations from database"""
        try:
            delegations = self.session.query(Delegation).all()
            return [self._delegation_to_dict(delegation) for delegation in delegations]
        except Exception as e:
            print(f"Error retrieving delegations: {e}")
            return []
    
    def get_delegations_for_task(self, task_id):
        """Retrieve delegations for a specific task"""
        try:
            delegations = self.session.query(Delegation).filter(Delegation.task_id == task_id).all()
            return [self._delegation_to_dict(delegation) for delegation in delegations]
        except Exception as e:
            print(f"Error retrieving delegations for task {task_id}: {e}")
            return []
    
    def delete_delegation(self, delegation_id):
        """Delete a delegation"""
        try:
            delegation = self.session.query(Delegation).filter(Delegation.id == delegation_id).first()
            if delegation:
                self.session.delete(delegation)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting delegation {delegation_id}: {e}")
            return False
    
    # Settings operations
    def save_setting(self, key, value):
        """Save a setting to the database"""
        try:
            # Convert value to JSON string if it's not already a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            setting = self.session.query(Settings).filter(Settings.key == key).first()
            if setting:
                setting.value = value
                setting.updated_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                setting = Settings(
                    key=key,
                    value=value,
                    updated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                self.session.add(setting)
            
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error saving setting {key}: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """Retrieve a setting from the database"""
        try:
            setting = self.session.query(Settings).filter(Settings.key == key).first()
            if setting:
                # Try to parse JSON, fall back to string if it fails
                try:
                    return json.loads(setting.value)
                except (json.JSONDecodeError, TypeError):
                    return setting.value
            return default
        except Exception as e:
            print(f"Error retrieving setting {key}: {e}")
            return default
    
    def get_all_settings(self):
        """Retrieve all settings as a dictionary"""
        try:
            settings = self.session.query(Settings).all()
            result = {}
            for setting in settings:
                try:
                    result[setting.key] = json.loads(setting.value)
                except (json.JSONDecodeError, TypeError):
                    result[setting.key] = setting.value
            return result
        except Exception as e:
            print(f"Error retrieving settings: {e}")
            return {}
    
    # Utility methods
    def _task_to_dict(self, task):
        """Convert Task object to dictionary"""
        if not task:
            return None
        
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'category': task.category,
            'status': task.status,
            'due_date': task.due_date,
            'created_date': task.created_date,
            'assignee': task.assignee,
            'estimated_hours': task.estimated_hours,
            'actual_hours': task.actual_hours,
            'created_by_ai': task.created_by_ai,
            'urgency_score': task.urgency_score,
            'completion_percentage': task.completion_percentage,
            'notes': task.notes
        }
    
    def _delegation_to_dict(self, delegation):
        """Convert Delegation object to dictionary"""
        if not delegation:
            return None
        
        return {
            'id': delegation.id,
            'task_id': delegation.task_id,
            'delegated_to': delegation.delegated_to,
            'delegated_by': delegation.delegated_by,
            'delegation_date': delegation.delegation_date,
            'status': delegation.status,
            'instructions': delegation.instructions,
            'deadline': delegation.deadline,
            'feedback': delegation.feedback,
            'completion_date': delegation.completion_date
        }
    
    def clear_all_data(self):
        """Clear all data from the database"""
        try:
            self.session.query(Delegation).delete()
            self.session.query(Task).delete()
            self.session.commit()
            print("All data cleared from database")
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error clearing data: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            task_count = self.session.query(Task).count()
            delegation_count = self.session.query(Delegation).count()
            completed_tasks = self.session.query(Task).filter(Task.status == 'Completed').count()
            ai_generated_tasks = self.session.query(Task).filter(Task.created_by_ai == True).count()
            
            return {
                'total_tasks': task_count,
                'total_delegations': delegation_count,
                'completed_tasks': completed_tasks,
                'ai_generated_tasks': ai_generated_tasks,
                'database_path': os.path.abspath(self.db_path),
                'database_size': f"{os.path.getsize(self.db_path) / 1024:.1f} KB" if os.path.exists(self.db_path) else "0 KB"
            }
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}

# Migration function to convert from JSON to SQLite
def migrate_from_json_to_db(data_handler, db_manager):
    """Migrate existing JSON data to SQLite database"""
    try:
        print("Starting migration from JSON to SQLite...")
        
        # Migrate tasks
        json_tasks = data_handler.load_tasks()
        for task in json_tasks:
            # Ensure created_date is set
            if 'created_date' not in task:
                task['created_date'] = datetime.now().strftime('%Y-%m-%d')
            db_manager.save_task(task)
        
        # Migrate delegations
        json_delegations = data_handler.load_delegations()
        for delegation in json_delegations:
            # Ensure delegation_date is set
            if 'delegation_date' not in delegation:
                delegation['delegation_date'] = datetime.now().strftime('%Y-%m-%d')
            db_manager.save_delegation(delegation)
        
        # Migrate settings
        json_settings = data_handler.load_settings()
        for key, value in json_settings.items():
            db_manager.save_setting(key, value)
        
        print(f"Migration completed: {len(json_tasks)} tasks, {len(json_delegations)} delegations migrated")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False