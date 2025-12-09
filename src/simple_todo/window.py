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
    
    def __init__(self, todo_list: TodoList, on_edit_list):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.todo_list = todo_list
        self.on_edit_list = on_edit_list
        
        self.set_margin_start(8)
        self.set_margin_end(4)
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        
        # List name label - wrap text but not too aggressively
        self.label = Gtk.Label(label=todo_list.name)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.FILL)
        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_xalign(0)  # Left align text
        self.label.set_natural_wrap_mode(Gtk.NaturalWrapMode.NONE)
        self.append(self.label)
        
        # Right side container for badge and edit button (minimal width)
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        right_box.set_valign(Gtk.Align.CENTER)
        right_box.set_halign(Gtk.Align.END)
        
        # Task count badge (completed/total format)
        completed = len(todo_list.get_completed_tasks())
        total = len(todo_list.tasks)
        if total > 0:
            self.count_label = Gtk.Label(label=f"{completed}/{total}")
            self.count_label.add_css_class("badge")
            right_box.append(self.count_label)
        
        # Edit button (hidden by default, shown when selected)
        self.edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
        self.edit_btn.add_css_class("flat")
        self.edit_btn.add_css_class("compact-button")
        self.edit_btn.set_tooltip_text("Edit list")
        self.edit_btn.set_visible(False)
        self.edit_btn.connect("clicked", self._on_edit_clicked)
        right_box.append(self.edit_btn)
        
        self.append(right_box)
    
    def set_selected(self, selected: bool):
        """Show or hide the edit button based on selection state."""
        self.edit_btn.set_visible(selected)
    
    def _on_edit_clicked(self, btn):
        self.on_edit_list(self.todo_list)


class MainWindow(Adw.ApplicationWindow):
    """Main application window with list sidebar and task panel."""
    
    SIDEBAR_WIDTH = 175
    
    def __init__(self, app):
        super().__init__(application=app)
        self.storage = Storage()
        self.current_list: TodoList | None = None
        self.sidebar_expanded = True
        
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
            .sidebar-container {
                border-right: 1px solid @borders;
            }
            .compact-button {
                min-height: 0;
                min-width: 0;
                padding: 2px;
                margin: 0;
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
        
        # Sidebar toggle button in header
        self.sidebar_toggle_btn = Gtk.Button(icon_name="sidebar-show-symbolic")
        self.sidebar_toggle_btn.set_tooltip_text("Toggle Sidebar")
        self.sidebar_toggle_btn.connect("clicked", self._on_toggle_sidebar)
        header.pack_start(self.sidebar_toggle_btn)
        
        # New list button in header
        new_list_btn = Gtk.Button(icon_name="list-add-symbolic")
        new_list_btn.set_tooltip_text("New List")
        new_list_btn.connect("clicked", self._on_new_list)
        header.pack_start(new_list_btn)
        
        main_box.append(header)
        
        # Paned container for sidebar and content (draggable divider)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_vexpand(True)
        self.paned.set_shrink_start_child(False)  # Prevent sidebar from completely shrinking
        self.paned.set_shrink_end_child(False)    # Prevent content from completely shrinking
        main_box.append(self.paned)
        
        # Left sidebar for lists
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar_box.set_size_request(150, -1)  # Minimum width
        self.sidebar_box.add_css_class("sidebar")
        self.sidebar_box.add_css_class("sidebar-container")
        
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
        
        self.sidebar_box.append(lists_header)
        
        # Scrollable list of lists
        scroll_lists = Gtk.ScrolledWindow()
        scroll_lists.set_vexpand(True)
        scroll_lists.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.lists_box = Gtk.ListBox()
        self.lists_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.lists_box.add_css_class("navigation-sidebar")
        self.lists_box.connect("row-selected", self._on_list_selected)
        scroll_lists.set_child(self.lists_box)
        
        self.sidebar_box.append(scroll_lists)
        self.paned.set_start_child(self.sidebar_box)
        
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
        self.task_entry.set_max_length(256)  # Enforce task title limit
        self.task_entry.connect("activate", self._on_add_task)
        input_box.append(self.task_entry)
        
        add_btn = Gtk.Button(label="Add")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_task)
        input_box.append(add_btn)
        
        content_box.append(input_box)
        
        # Active list name header (centered, below input)
        self.active_list_label = Gtk.Label(label="")
        self.active_list_label.set_halign(Gtk.Align.CENTER)
        self.active_list_label.add_css_class("title-4")
        self.active_list_label.set_margin_top(4)
        self.active_list_label.set_margin_bottom(8)
        content_box.append(self.active_list_label)
        
        # Scrollable task list
        scroll_tasks = Gtk.ScrolledWindow()
        scroll_tasks.set_vexpand(True)
        scroll_tasks.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.tasks_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll_tasks.set_child(self.tasks_container)
        
        content_box.append(scroll_tasks)
        
        self.paned.set_end_child(content_box)
        self.paned.set_position(self.SIDEBAR_WIDTH)  # Initial sidebar width
        
        # Placeholder when no list selected
        self.placeholder = Adw.StatusPage()
        self.placeholder.set_title("No List Selected")
        self.placeholder.set_description("Select a list from the sidebar or create a new one")
        self.placeholder.set_icon_name("view-list-symbolic")
        
        self._update_content_visibility()
    
    def _on_toggle_sidebar(self, btn):
        """Toggle sidebar visibility."""
        self.sidebar_expanded = not self.sidebar_expanded
        
        if self.sidebar_expanded:
            # Show sidebar and restore to default width (175)
            self.sidebar_box.set_visible(True)
            self.paned.set_position(self.SIDEBAR_WIDTH)
            self.sidebar_toggle_btn.set_icon_name("sidebar-show-symbolic")
        else:
            # Completely collapse sidebar to 0
            self.paned.set_position(0)
            self.sidebar_box.set_visible(False)
            self.sidebar_toggle_btn.set_icon_name("sidebar-show-right-symbolic")
    
    def _update_content_visibility(self):
        """Show placeholder or content based on selection."""
        has_list = self.current_list is not None
        self.task_entry.set_sensitive(has_list)
        
        # Update active list name header
        if has_list:
            self.active_list_label.set_label(self.current_list.name)
            self.active_list_label.set_visible(True)
        else:
            self.active_list_label.set_label("")
            self.active_list_label.set_visible(False)
    
    def _load_lists(self):
        """Load all lists into the sidebar."""
        # Remember current selection
        current_id = self.current_list.id if self.current_list else None
        
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
            list_row = ListRow(todo_list, on_edit_list=self._on_edit_list)
            row.set_child(list_row)
            row.todo_list = todo_list
            row.list_row_widget = list_row
            self.lists_box.append(row)
        
        # Re-select previous list or first list
        if lists:
            selected = False
            if current_id:
                for i in range(len(lists)):
                    row = self.lists_box.get_row_at_index(i)
                    if row and row.todo_list.id == current_id:
                        self.lists_box.select_row(row)
                        selected = True
                        break
            
            if not selected and self.current_list is None:
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
        # Update edit button visibility for all rows
        for i in range(100):  # Max lists
            list_row = self.lists_box.get_row_at_index(i)
            if list_row is None:
                break
            if hasattr(list_row, 'list_row_widget'):
                list_row.list_row_widget.set_selected(list_row == row)
        
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
            body="Enter a name for the new list (max 32 chars, leave empty for auto-naming):"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("List name (optional)")
        entry.set_max_length(32)  # Enforce character limit in UI
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
            dialog.close()
        
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("create"))
        dialog.present()
    
    def _on_edit_list(self, todo_list: TodoList):
        """Show edit options for a list (rename/delete)."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=f"Edit \"{todo_list.name}\"",
            body="What would you like to do with this list?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("rename", "Rename")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        def on_response(dialog, response):
            dialog.close()
            if response == "rename":
                self._show_rename_dialog(todo_list)
            elif response == "delete":
                self._show_delete_dialog(todo_list)
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _show_rename_dialog(self, todo_list: TodoList):
        """Show rename dialog for a list."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Rename List",
            body="Enter a new name for the list (max 32 characters):"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("rename", "Rename")
        dialog.set_response_appearance("rename", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("rename")
        
        entry = Gtk.Entry()
        entry.set_text(todo_list.name)
        entry.set_max_length(32)  # Enforce character limit in UI
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        dialog.set_extra_child(entry)
        
        def on_response(dialog, response):
            if response == "rename":
                name = entry.get_text().strip()
                if name:
                    success = self.storage.rename_list(todo_list.id, name)
                    if success:
                        if self.current_list and self.current_list.id == todo_list.id:
                            self.current_list = self.storage.get_list(todo_list.id)
                            self._update_content_visibility()  # Update header label
                        self._load_lists()
                    else:
                        # Show error - name is likely a duplicate
                        self._show_error_dialog("Could not rename list. The name may already be in use.")
            dialog.close()
        
        dialog.connect("response", on_response)
        entry.connect("activate", lambda e: dialog.response("rename"))
        dialog.present()
    
    def _show_error_dialog(self, message: str):
        """Show an error message dialog."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Error",
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()
    
    def _show_delete_dialog(self, todo_list: TodoList):
        """Show delete confirmation dialog for a list."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Delete List?",
            body=f"Are you sure you want to delete \"{todo_list.name}\"? This action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        
        def on_response(dialog, response):
            if response == "delete":
                self.storage.delete_list(todo_list.id)
                if self.current_list and self.current_list.id == todo_list.id:
                    self.current_list = None
                self._load_lists()
                self._load_tasks()
                self._update_content_visibility()
            dialog.close()
        
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
        entry.set_max_length(256)  # Enforce task title limit
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
            dialog.close()
        
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
