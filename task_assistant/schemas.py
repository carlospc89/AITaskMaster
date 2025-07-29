# task_assistant/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Task(BaseModel):
    """Represents a single action item."""
    task_description: str = Field(description="The full, detailed description of the task.", alias="task")
    project: Optional[str] = Field(description="The project this task belongs to.", default=None)
    due_date: Optional[str] = Field(description="The due date of the task in YYYY-MM-DD format.", default=None)
    status: str = Field(description="The current status of the task.", default="To Do")
    # THIS IS THE CHANGE: Add the optional dependency field
    depends_on_id: Optional[int] = Field(description="The ID of the task that this task depends on.", default=None)

class TaskList(BaseModel):
    """Represents a list of action items."""
    tasks: List[Task]