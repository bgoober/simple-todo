"""Storage layer for persisting to-do lists to JSON."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from .models import TodoList, Task


class Storage:
    """Handles reading and writing to-do data to JSON file."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize storage with optional custom data directory."""
        if data_dir is None:
            # Use XDG data directory standard
            xdg_data = os.environ.get("XDG_DATA_HOME", 
                                       os.path.expanduser("~/.local/share"))
            self.data_dir = Path(xdg_data) / "simple-todo"
        else:
            self.data_dir = data_dir
        
        self.data_file = self.data_dir / "data.json"
        self._ensure_data_dir()
        self._lists: list[TodoList] = []
        self._load()
    
    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load(self) -> None:
        """Load data from JSON file."""
        if not self.data_file.exists():
            self._lists = []
            return
        
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._lists = [TodoList.from_dict(lst) for lst in data.get("lists", [])]
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, start fresh
            self._lists = []
    
    def _save(self) -> None:
        """Save data to JSON file with atomic write."""
        data = {
            "lists": [lst.to_dict() for lst in self._lists]
        }
        
        # Atomic write: write to temp file, then rename
        # This prevents data corruption if write is interrupted
        self._ensure_data_dir()
        fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.data_file)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def get_lists(self) -> list[TodoList]:
        """Return all to-do lists."""
        return self._lists.copy()
    
    def get_list(self, list_id: str) -> Optional[TodoList]:
        """Get a specific list by ID."""
        for lst in self._lists:
            if lst.id == list_id:
                return lst
        return None
    
    def create_list(self, name: Optional[str] = None) -> TodoList:
        """Create a new to-do list with optional name."""
        if not name or not name.strip():
            # Auto-generate name: List 1, List 2, etc.
            existing_nums = set()
            for lst in self._lists:
                if lst.name.startswith("List "):
                    try:
                        num = int(lst.name[5:])
                        existing_nums.add(num)
                    except ValueError:
                        pass
            
            # Find the next available number
            num = 1
            while num in existing_nums:
                num += 1
            name = f"List {num}"
        
        new_list = TodoList(name=name.strip())
        self._lists.append(new_list)
        self._save()
        return new_list
    
    def delete_list(self, list_id: str) -> bool:
        """Delete a list by ID. Returns True if found and deleted."""
        for i, lst in enumerate(self._lists):
            if lst.id == list_id:
                del self._lists[i]
                self._save()
                return True
        return False
    
    def rename_list(self, list_id: str, new_name: str) -> bool:
        """Rename a list. Returns True if found and renamed."""
        lst = self.get_list(list_id)
        if lst and new_name.strip():
            lst.name = new_name.strip()
            self._save()
            return True
        return False
    
    def add_task(self, list_id: str, title: str) -> Optional[Task]:
        """Add a task to a list. Returns the task if successful."""
        lst = self.get_list(list_id)
        if lst and title.strip():
            task = lst.add_task(title.strip())
            self._save()
            return task
        return None
    
    def update_task(self, list_id: str, task_id: str, title: str) -> bool:
        """Update a task's title. Returns True if successful."""
        lst = self.get_list(list_id)
        if lst:
            task = lst.get_task(task_id)
            if task and title.strip():
                task.title = title.strip()
                self._save()
                return True
        return False
    
    def delete_task(self, list_id: str, task_id: str) -> bool:
        """Delete a task from a list. Returns True if successful."""
        lst = self.get_list(list_id)
        if lst and lst.remove_task(task_id):
            self._save()
            return True
        return False
    
    def toggle_task(self, list_id: str, task_id: str) -> bool:
        """Toggle a task's completion status. Returns True if successful."""
        lst = self.get_list(list_id)
        if lst:
            task = lst.get_task(task_id)
            if task:
                task.completed = not task.completed
                self._save()
                return True
        return False

