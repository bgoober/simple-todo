"""Data models for the Simple Todo application."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """Represents a single task in a to-do list."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            completed=data.get("completed", False),
            created_at=data.get("created_at", datetime.now().isoformat())
        )


@dataclass
class TodoList:
    """Represents a to-do list containing multiple tasks."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: list[Task] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert list to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "tasks": [task.to_dict() for task in self.tasks]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TodoList":
        """Create a TodoList from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])]
        )
    
    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not completed."""
        return [t for t in self.tasks if not t.completed]
    
    def get_completed_tasks(self) -> list[Task]:
        """Return tasks that are completed."""
        return [t for t in self.tasks if t.completed]
    
    def add_task(self, title: str) -> Task:
        """Add a new task to the list."""
        task = Task(title=title)
        self.tasks.append(task)
        return task
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

