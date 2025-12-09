#!/usr/bin/env python3
"""Entry point for the Simple Todo application."""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

from . import __app_id__
from .window import MainWindow


class SimpleTodoApp(Adw.Application):
    """Main GTK4 application class."""
    
    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
    
    def do_activate(self):
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = MainWindow(self)
        win.present()


def main():
    """Application entry point."""
    app = SimpleTodoApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

