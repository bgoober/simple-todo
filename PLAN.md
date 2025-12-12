# Simple To-Do List Desktop Application - Development Plan

> This document outlines the architecture and implementation plan for the Simple Todo List application.

## Overview

Create a secure, minimal GTK4 + Python to-do list desktop application packaged as a Snap, with local JSON storage for multiple lists and full CRUD + completion tracking for tasks.

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| UI Framework | GTK4 + Python (PyGObject) | Native Ubuntu look, mature, secure, lightweight |
| Data Storage | JSON file | Simple, human-readable, no external dependencies |
| Storage Location | `~/.local/share/simple-todo/` | XDG-compliant, persists across sessions |
| Packaging | Snap | Ubuntu-native, automatic updates, sandboxed |

## Application Architecture

### File Structure

```
simple-todo/
├── src/
│   └── simple_todo/
│       ├── __init__.py         # Package metadata
│       ├── main.py             # Entry point, GTK application setup
│       ├── window.py           # Main window UI
│       ├── storage.py          # JSON data persistence
│       └── models.py           # Task and List data structures
├── data/
│   └── com.github.simpletodo.desktop   # Desktop entry
├── snap/
│   └── snapcraft.yaml          # Snap packaging configuration
├── setup.py                    # Python package setup
├── requirements.txt            # Dependencies documentation
├── README.md                   # User documentation
└── PLAN.md                     # This file
```

### Data Model

```json
{
  "lists": [
    {
      "id": "uuid-string",
      "name": "List 1",
      "tasks": [
        {
          "id": "uuid-string",
          "title": "Task description",
          "completed": false,
          "created_at": "ISO-timestamp"
        }
      ]
    }
  ]
}
```

## Core Features

### 1. List Management
- Sidebar with list of all to-do lists
- "+" button to create new list (auto-named "List 1", "List 2", etc. if no name given)
- Buttons to delete/rename lists
- Deletion removes list from JSON and updates UI

### 2. Task Management
- Main panel shows tasks for selected list
- Tasks split into two sections: "To Do" (top) and "Completed" (bottom)
- Text entry + button to add new tasks
- Each task has: checkbox, title text, edit button, delete button

### 3. Task Completion Flow
- Clicking checkbox on incomplete task → moves to "Completed" section
- Clicking checkbox on completed task → moves back to "To Do" section
- Visual distinction (strikethrough, dimmed) for completed tasks

## Security Considerations

1. **Snap Confinement**: Strict confinement with only necessary permissions
   - `home` plug for data storage access
   - No network access required
2. **Input Validation**: All user inputs are stripped/sanitized before storage
3. **Safe File Operations**: Atomic writes to prevent data corruption
4. **No External Dependencies**: All processing done locally, no network calls

## UI Design

- Clean, minimal GTK4 Adwaita styling
- Two-pane layout: sidebar (lists) + main area (tasks)
- Header bar with app title and "New List" button
- Responsive to window resizing

## Implementation Checklist

- [x] Set up project structure and Python package
- [x] Implement Task and List data models (`models.py`)
- [x] Implement JSON storage with atomic writes (`storage.py`)
- [x] Build main window UI (`window.py`)
- [x] Implement list sidebar with add/delete/rename functionality
- [x] Implement task panel with CRUD and completion toggling
- [x] Create Snap packaging (`snapcraft.yaml`)
- [x] Create documentation (`README.md`)

## Building and Running

### Development (without Snap)

```bash
# Install dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-dev gir1.2-adw-1

# Run from source
cd src
python3 -c "from simple_todo.main import main; main()"
```

### Build Snap Package

```bash
# Install snapcraft
sudo snap install snapcraft --classic

# Build the snap
snapcraft

# Install locally
sudo snap install simple-todo_1.0.0_amd64.snap --dangerous
```

### Publish to Snap Store

1. Create an account at https://snapcraft.io/
2. Run `snapcraft login`
3. Run `snapcraft register minimal-todo-list`
4. Run `snapcraft upload minimal-todo-list_1.0.0_amd64.snap`

