"""Storage layer for persisting to-do lists to JSON."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from .models import TodoList, Task


# Constants for input validation
MAX_LIST_NAME_LENGTH = 32
MAX_TASK_TITLE_LENGTH = 256


def sanitize_input(text: str, max_length: int) -> str:
    """Sanitize user input for safe storage.
    
    - Strips leading/trailing whitespace
    - Removes control characters (except newlines for tasks)
    - Limits length
    - Removes null bytes
    """
    if not text:
        return ""
    
    # Remove null bytes and control characters (ASCII 0-31 except tab/newline/carriage return)
    # For list names, we remove all control chars; for tasks we might keep newlines
    sanitized = "".join(
        char for char in text 
        if ord(char) >= 32 or char in '\t'
    )
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    # Collapse multiple spaces into one
    sanitized = re.sub(r' +', ' ', sanitized)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    return sanitized


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
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    
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
            # Set restrictive permissions (owner read/write only)
            os.fchmod(fd, 0o600)
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
    
    def _get_existing_names(self) -> set[str]:
        """Return a set of all existing list names (lowercase for comparison)."""
        return {lst.name.lower() for lst in self._lists}
    
    def _get_next_list_number(self) -> int:
        """Find the next available number for auto-naming.
        
        Looks at all existing "List N" names and returns max(N) + 1.
        """
        max_num = 0
        for lst in self._lists:
            if lst.name.startswith("List "):
                try:
                    num = int(lst.name[5:])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
        return max_num + 1
    
    def _generate_unique_name(self) -> str:
        """Generate a unique auto-name for a new list."""
        existing_names = self._get_existing_names()
        num = self._get_next_list_number()
        
        # Keep incrementing until we find a unique name
        while f"list {num}".lower() in existing_names:
            num += 1
        
        return f"List {num}"
    
    def create_list(self, name: Optional[str] = None) -> TodoList:
        """Create a new to-do list with optional name."""
        if not name or not name.strip():
            # Auto-generate unique name
            name = self._generate_unique_name()
        else:
            # Sanitize user-provided name
            name = sanitize_input(name, MAX_LIST_NAME_LENGTH)
            
            # Ensure uniqueness (case-insensitive)
            existing_names = self._get_existing_names()
            if name.lower() in existing_names:
                # Append a number to make it unique
                base_name = name
                counter = 2
                while f"{base_name} ({counter})".lower() in existing_names:
                    counter += 1
                name = f"{base_name} ({counter})"
                # Re-check length after appending
                if len(name) > MAX_LIST_NAME_LENGTH:
                    # Truncate base name to fit
                    suffix = f" ({counter})"
                    name = base_name[:MAX_LIST_NAME_LENGTH - len(suffix)] + suffix
        
        new_list = TodoList(name=name)
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
        if not lst:
            return False
        
        # Sanitize the new name
        new_name = sanitize_input(new_name, MAX_LIST_NAME_LENGTH)
        if not new_name:
            return False
        
        # Check for uniqueness (excluding the current list)
        existing_names = {l.name.lower() for l in self._lists if l.id != list_id}
        if new_name.lower() in existing_names:
            return False  # Name already taken
        
        lst.name = new_name
        self._save()
        return True
    
    def add_task(self, list_id: str, title: str) -> Optional[Task]:
        """Add a task to a list. Returns the task if successful."""
        lst = self.get_list(list_id)
        if not lst:
            return None
        
        # Sanitize the task title
        title = sanitize_input(title, MAX_TASK_TITLE_LENGTH)
        if not title:
            return None
        
        task = lst.add_task(title)
        self._save()
        return task
    
    def update_task(self, list_id: str, task_id: str, title: str) -> bool:
        """Update a task's title. Returns True if successful."""
        lst = self.get_list(list_id)
        if not lst:
            return False
        
        task = lst.get_task(task_id)
        if not task:
            return False
        
        # Sanitize the task title
        title = sanitize_input(title, MAX_TASK_TITLE_LENGTH)
        if not title:
            return False
        
        task.title = title
        self._save()
        return True
    
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

