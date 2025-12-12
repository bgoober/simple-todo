# Simple Todo List

A simple, minimal, lightweight to-do list desktop application for Ubuntu/Linux, built with GTK4 and Python.

## Features

- **Multiple Lists**: Create and manage multiple to-do lists
- **Full CRUD**: Add, edit, delete tasks within each list
- **Completion Tracking**: Check off completed tasks (moved to "Completed" section)
- **Un-check Tasks**: Move completed tasks back to active "To Do" section
- **Local Storage**: All data stored securely in `~/.local/share/simple-todo/`
- **No Internet Required**: 100% offline, no cloud sync, no telemetry

## Security

- **Strict Snap Confinement**: Sandboxed with minimal permissions
- **Local Data Only**: No network access, all data stays on your machine
- **Atomic Saves**: Data writes are atomic to prevent corruption

## Installation

### Option 1: Install from Snap Store (Recommended)

```bash
sudo snap install simple-todo
```

### Option 2: Build and Install Locally

#### Prerequisites

Install the required system dependencies:

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-dev gir1.2-adw-1 snapcraft
```

#### Build the Snap

```bash
cd /path/to/simple-todo
snapcraft
```

#### Install the Built Snap

```bash
sudo snap install simple-todo_1.0.0_amd64.snap --dangerous
```

(The `--dangerous` flag is required for locally-built snaps that aren't signed)

### Option 3: Run Without Installing (Development)

```bash
# Install dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-dev gir1.2-adw-1

# Run from source
cd /path/to/simple-todo
python3 -m simple_todo.main
```

Or create a convenience script:

```bash
cd /path/to/simple-todo/src
python3 -c "from simple_todo.main import main; main()"
```

## Usage

1. **Launch** the application from your application menu or run `simple-todo`
2. **Create a List**: Click the "+" button in the header bar
3. **Add Tasks**: Type in the text field and press Enter or click "Add"
4. **Complete Tasks**: Click the checkbox to mark a task as complete
5. **Edit Tasks**: Click the pencil icon next to a task
6. **Delete Tasks**: Click the trash icon next to a task
7. **Manage Lists**: Use "Rename List" or "Delete List" buttons at the bottom

## Data Storage

Your to-do data is stored in:

```
~/.local/share/simple-todo/data.json
```

The data format is plain JSON, human-readable, and easy to backup:

```json
{
  "lists": [
    {
      "id": "uuid",
      "name": "My List",
      "tasks": [
        {
          "id": "uuid",
          "title": "Task description",
          "completed": false,
          "created_at": "2024-01-01T12:00:00"
        }
      ]
    }
  ]
}
```

## Project Structure

```
simple-todo/
├── src/simple_todo/
│   ├── __init__.py      # Package metadata
│   ├── main.py          # Application entry point
│   ├── window.py        # GTK4 UI implementation
│   ├── storage.py       # JSON data persistence
│   └── models.py        # Data models (Task, TodoList)
├── data/
│   └── *.desktop        # Desktop entry file
├── snap/
│   └── snapcraft.yaml   # Snap packaging config
├── requirements.txt
└── README.md
```

## License

MIT License - Feel free to use, modify, and distribute.

## Contributing

This is intentionally a minimal application. Feature requests that add complexity will likely be declined to maintain simplicity.

Bug fixes and security improvements are welcome!

