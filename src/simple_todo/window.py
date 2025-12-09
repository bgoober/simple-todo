"""Main window for the Simple Todo application."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango

from .storage import Storage
from .models import TodoList, Task


class TaskRow(Gtk.Box):
    """A row widget representing a single task."""
    
    def __init__(self, task: Task, on_toggle, on_edit, on_delete):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.task = task
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        # Checkbox
        self.check = Gtk.CheckButton()
        self.check.set_active(task.completed)
        self.check.connect("toggled", self._on_check_toggled)
        self.append(self.check)
        
        # Task label
        self.label = Gtk.Label(label=task.title)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        if task.completed:
            self.label.add_css_class("dim-label")
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_strikethrough_new(True))
            self.label.set_attributes(attrs)
        self.append(self.label)
        
        # Edit button
        edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
        edit_btn.add_css_class("flat")
        edit_btn.set_tooltip_text("Edit task")
        edit_btn.connect("clicked", self._on_edit_clicked)
        self.append(edit_btn)
        
        # Delete button
        delete_btn = Gtk.Button(icon_name="user-trash-symbolic")
        delete_btn.add_css_class("flat")
        delete_btn.add_css_class("destructive-action")
        delete_btn.set_tooltip_text("Delete task")
        delete_btn.connect("clicked", self._on_delete_clicked)
        self.append(delete_btn)
    
    def _on_check_toggled(self, check):
        self.on_toggle(self.task.id)
    
    def _on_edit_clicked(self, btn):
        self.on_edit(self.task)
    
    def _on_delete_clicked(self, btn):
        self.on_delete(self.task.id)


class ListRow(Gtk.Box):
    """A row widget representing a to-do list in the sidebar."""
    
    def __init__(self, todo_list: TodoList):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.todo_list = todo_list
        
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        
        # List name label
        self.label = Gtk.Label(label=todo_list.name)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.append(self.label)
        
        # Task count badge
        pending = len(todo_list.get_pending_tasks())
        if pending > 0:
            count_label = Gtk.Label(label=str(pending))
            count_label.add_css_class("badge")
            self.append(count_label)


class MainWindow(Adw.ApplicationWindow):
    """Main application window with list sidebar and task panel."""
    
    def __init__(self, app):
        super().__init__(application=app)
        self.storage = Storage()
        self.current_list: TodoList | None = None
        
        self.set_title("Simple Todo")
        self.set_default_size(800, 600)
        
        self._build_ui()
        self._load_lists()
        self._apply_css()
    
    def _apply_css(self):
        """Apply custom CSS styles."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .badge {
                background-color: @accent_bg_color;
                color: @accent_fg_color;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 0.85em;
                font-weight: bold;
            }
            .task-section-header {
                font-weight: bold;
                font-size: 0.9em;
                color: @dim_color;
                padding: 8px 12px;
            }
            .completed-section {
                opacity: 0.7;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _build_ui(self):
        """Build the main UI layout."""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Simple Todo"))
        
        # New list button in header
        new_list_btn = Gtk.Button(icon_name="list-add-symbolic")
        new_list_btn.set_tooltip_text("New List")
        new_list_btn.connect("clicked", self._on_new_list)
        header.pack_start(new_list_btn)
        
        main_box.append(header)
        
        # Paned container for sidebar and content
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        main_box.append(paned)
        
        # Left sidebar for lists
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(200, -1)
        sidebar_box.add_css_class("sidebar")
        
        # Lists header
        lists_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lists_header.set_margin_start(12)
        lists_header.set_margin_end(12)
        lists_header.set_margin_top(12)
        lists_header.set_margin_bottom(8)
        
        lists_label = Gtk.Label(label="Lists")
        lists_label.set_hexpand(True)
        lists_label.set_halign(Gtk.Align.START)
        lists_label.add_css_class("heading")
        lists_header.append(lists_label)
        
        sidebar_box.append(lists_header)
        
        # Scrollable list of lists
        scroll_lists = Gtk.ScrolledWindow()
        scroll_lists.set_vexpand(True)
        scroll_lists.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.lists_box = Gtk.ListBox()
        self.lists_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.lists_box.add_css_class("navigation-sidebar")
        self.lists_box.connect("row-selected", self._on_list_selected)
        scroll_lists.set_child(self.lists_box)
        
        sidebar_box.append(scroll_lists)
        paned.set_start_child(sidebar_box)
        
        # Right content area for tasks
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_hexpand(True)
        
        # Task input area
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        input_box.set_margin_start(12)
        input_box.set_margin_end(12)
        input_box.set_margin_top(12)
        input_box.set_margin_bottom(8)
        
        self.task_entry = Gtk.Entry()
        self.task_entry.set_hexpand(True)
        self.task_entry.set_placeholder_text("Add a new task...")
        self.task_entry.connect("activate", self._on_add_task)
        input_box.append(self.task_entry)
        
        add_btn = Gtk.Button(label="Add")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_task)
        input_box.append(add_btn)
        
        content_box.append(input_box)
        
        # Scrollable task list
        scroll_tasks = Gtk.ScrolledWindow()
        scroll_tasks.set_vexpand(True)
        scroll_tasks.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.tasks_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll_tasks.set_child(self.tasks_container)
        
        content_box.append(scroll_tasks)
        
        # List action buttons at bottom
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_box.set_margin_start(12)
        action_box.set_margin_end(12)
        action_box.set_margin_bottom(12)
        action_box.set_halign(Gtk.Align.END)
        
        self.rename_btn = Gtk.Button(label="Rename List")
        self.rename_btn.connect("clicked", self._on_rename_list)
        action_box.append(self.rename_btn)
        
        self.delete_list_btn = Gtk.Button(label="Delete List")
        self.delete_list_btn.add_css_class("destructive-action")
        self.delete_list_btn.connect("clicked", self._on_delete_list)
        action_box.append(self.delete_list_btn)
        
        content_box.append(action_box)
        
        paned.set_end_child(content_box)
        paned.set_position(220)
        
        # Placeholder when no list selected
        self.placeholder = Adw.StatusPage()
        self.placeholder.set_title("No List Selected")
        self.placeholder.set_description("Select a list from the sidebar or create a new one")
        self.placeholder.set_icon_name("view-list-symbolic")
        
        self._update_content_visibility()
    
    def _update_content_visibility(self):
        """Show placeholder or content based on selection."""
        has_list = self.current_list is not None
        self.task_entry.set_sensitive(has_list)
        self.rename_btn.set_sensitive(has_list)
        self.delete_list_btn.set_sensitive(has_list)
    
    def _load_lists(self):
        """Load all lists into the sidebar."""
        # Clear existing
        while True:
            row = self.lists_box.get_row_at_index(0)
            if row is None:
                break
            self.lists_box.remove(row)
        
        # Add lists
        lists = self.storage.get_lists()
        for todo_list in lists:
            row = Gtk.ListBoxRow()
            row.set_child(ListRow(todo_list))
            row.todo_list = todo_list
            self.lists_box.append(row)
        
        # Select first list if available
        if lists and self.current_list is None:
            first_row = self.lists_box.get_row_at_index(0)
            if first_row:
                self.lists_box.select_row(first_row)
    
    def _load_tasks(self):
        """Load tasks for the current list."""
        # Clear existing
        while True:
            child = self.tasks_container.get_first_child()
            if child is None:
                break
            self.tasks_container.remove(child)
        
        if not self.current_list:
            return
        
        # Pending tasks section
        pending = self.current_list.get_pending_tasks()
        if pending:
            header = Gtk.Label(label="To Do")
            header.add_css_class("task-section-header")
            header.set_halign(Gtk.Align.START)
            self.tasks_container.append(header)
            
            for task in pending:
                row = TaskRow(
                    task,
                    on_toggle=self._on_toggle_task,
                    on_edit=self._on_edit_task,
                    on_delete=self._on_delete_task
                )
                self.tasks_container.append(row)
        
        # Completed tasks section
        completed = self.current_list.get_completed_tasks()
        if completed:
            header = Gtk.Label(label="Completed")
            header.add_css_class("task-section-header")
            header.set_halign(Gtk.Align.START)
            header.set_margin_top(16)
            self.tasks_container.append(header)
            
            completed_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            completed_box.add_css_class("completed-section")
            
            for task in completed:
                row = TaskRow(
                    task,
                    on_toggle=self._on_toggle_task,
                    on_edit=self._on_edit_task,
                    on_delete=self._on_delete_task
                )
                completed_box.append(row)
            
            self.tasks_container.append(completed_box)
    
    def _on_list_selected(self, listbox, row):
        """Handle list selection."""
        if row:
            self.current_list = row.todo_list
        else:
            self.current_list = None
        self._update_content_visibility()
        self._load_tasks()
    
    def _on_new_list(self, btn):
        """Create a new list."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="New List",
            body="Enter a name for the new list (leave empty for auto-naming):"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("List name (optional)")
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        
        def on_response(dialog, response):
            if response == "create":
                name = entry.get_text().strip() or None
                new_list = self.storage.create_list(name)
                self._load_lists()
                # Select the new list
                for i in range(100):  # Max 100 lists
                    row = self.lists_box.get_row_at_index(i)
                    if row is None:
                        break
                    if row.todo_list.id == new_list.id:
                        self.lists_box.select_row(row)
                        break
            dialog.destroy()
        
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("create"))
        dialog.present()
    
    def _on_rename_list(self, btn):
        """Rename the current list."""
        if not self.current_list:
            return
        
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Rename List",
            body="Enter a new name for the list:"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("rename", "Rename")
        dialog.set_response_appearance("rename", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("rename")
        
        entry = Gtk.Entry()
        entry.set_text(self.current_list.name)
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        
        def on_response(dialog, response):
            if response == "rename":
                name = entry.get_text().strip()
                if name:
                    self.storage.rename_list(self.current_list.id, name)
                    self.current_list.name = name
                    self._load_lists()
                    # Re-select current list
                    for i in range(100):
                        row = self.lists_box.get_row_at_index(i)
                        if row is None:
                            break
                        if row.todo_list.id == self.current_list.id:
                            self.lists_box.select_row(row)
                            break
            dialog.destroy()
        
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("rename"))
        dialog.present()
    
    def _on_delete_list(self, btn):
        """Delete the current list."""
        if not self.current_list:
            return
        
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Delete List?",
            body=f"Are you sure you want to delete \"{self.current_list.name}\"? This action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        def on_response(dialog, response):
            if response == "delete":
                self.storage.delete_list(self.current_list.id)
                self.current_list = None
                self._load_lists()
                self._load_tasks()
                self._update_content_visibility()
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_add_task(self, widget):
        """Add a new task to the current list."""
        if not self.current_list:
            return
        
        title = self.task_entry.get_text().strip()
        if not title:
            return
        
        self.storage.add_task(self.current_list.id, title)
        self.task_entry.set_text("")
        
        # Refresh to get updated list from storage
        self.current_list = self.storage.get_list(self.current_list.id)
        self._load_tasks()
        self._load_lists()  # Update task counts
    
    def _on_toggle_task(self, task_id: str):
        """Toggle task completion."""
        if not self.current_list:
            return
        
        self.storage.toggle_task(self.current_list.id, task_id)
        self.current_list = self.storage.get_list(self.current_list.id)
        self._load_tasks()
        self._load_lists()  # Update task counts
    
    def _on_edit_task(self, task: Task):
        """Edit a task."""
        if not self.current_list:
            return
        
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Edit Task",
            body="Update the task description:"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        
        entry = Gtk.Entry()
        entry.set_text(task.title)
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        
        def on_response(dialog, response):
            if response == "save":
                title = entry.get_text().strip()
                if title:
                    self.storage.update_task(self.current_list.id, task.id, title)
                    self.current_list = self.storage.get_list(self.current_list.id)
                    self._load_tasks()
            dialog.destroy()
        
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("save"))
        dialog.present()
    
    def _on_delete_task(self, task_id: str):
        """Delete a task."""
        if not self.current_list:
            return
        
        self.storage.delete_task(self.current_list.id, task_id)
        self.current_list = self.storage.get_list(self.current_list.id)
        self._load_tasks()
        self._load_lists()  # Update task counts

