"""Tkinter-based GUI for Minecraft RCON client.

Provides a graphical interface with connection management, command execution,
player list monitoring, and datapack viewing.
"""

from __future__ import annotations

import datetime
import os
import re
import tempfile
import tkinter as tk
from threading import Thread
from tkinter import messagebox, scrolledtext
from typing import Any

from mcrconpy.core import Rcon as RconPy

# Try orjson for 6x faster JSON serialization
try:
    import orjson  # type: ignore[import-not-found]

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    import json

CONFIG_FILE = "rcon_config.json"
LOG_FILE = "rcon_log.txt"


class RconGUI:
    """Main GUI application for RCON client."""

    def __init__(self) -> None:
        """Initialize GUI components and load configuration."""
        self.root = tk.Tk()
        self.root.title("Minecraft RCON GUI")

        self.rcon_client: RconPy | None = None
        self.config: dict[str, Any] = self.load_config()
        self.dark_mode: bool = True

        # UI Components (initialized in setup_ui)
        self.address_entry: tk.Entry
        self.port_entry: tk.Entry
        self.password_entry: tk.Entry
        self.command_entry: tk.Entry
        self.send_button: tk.Button
        self.output_box: scrolledtext.ScrolledText
        self.player_list_box: tk.Listbox
        self.datapack_list_box: tk.Listbox
        self.show_password_var: tk.BooleanVar
        self.player_frame: tk.Frame

        # Cache for theme-able widgets (populated in setup_ui)
        self._themeable_widgets: list[tuple[tk.Widget, str]] = []

        # Auto-refresh failure tracking for backoff
        self._refresh_failures = 0
        self._refresh_interval = 5000  # milliseconds

        self.setup_ui()
        self.apply_theme()

    def load_config(self) -> dict[str, Any]:
        """Load RCON configuration from JSON file.

        Returns:
            dict: Configuration data or empty dict if load fails.
        """
        if not os.path.exists(CONFIG_FILE):
            return {}

        try:
            with open(CONFIG_FILE, "rb") as f:
                if HAS_ORJSON:
                    data: dict[str, Any] = orjson.loads(f.read())
                    return data
                else:
                    data_json: dict[str, Any] = json.load(f)
                    return data_json
        except (OSError, ValueError):
            return {}
        except Exception:
            # Catches orjson.JSONDecodeError when orjson is available
            return {}

    def save_config(self, address: str, port: int, password: str) -> None:
        """Save RCON configuration atomically to prevent corruption.

        Args:
            address: Server hostname or IP.
            port: RCON port number.
            password: RCON password.
        """
        config = {"address": address, "port": port, "password": password}

        # Atomic write using temp file
        try:
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(CONFIG_FILE) or ".", suffix=".tmp"
            )
            with os.fdopen(fd, "wb") as f:
                if HAS_ORJSON:
                    f.write(orjson.dumps(config, option=orjson.OPT_INDENT_2))
                else:
                    f.write(json.dumps(config, indent=2).encode("utf-8"))

            # Atomic rename (POSIX compliant)
            os.replace(temp_path, CONFIG_FILE)
        except OSError as e:
            self.log_message(f"Failed to save config atomically: {e}")
            # Attempt to clean up the temporary file if it was created, but prioritize
            # not corrupting the original config file.
            if "temp_path" in locals():
                try:
                    os.remove(temp_path)
                except OSError:
                    pass  # Ignore errors during cleanup of temp file

    def log_message(self, message: str) -> None:
        """Append timestamped message to log file.

        Args:
            message: Log message content.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except OSError:
            pass  # Fail silently if logging fails

    def connect_to_server(self) -> None:
        """Establish RCON connection and initialize UI state."""
        address = self.address_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Port must be an integer.")
            return

        password = self.password_entry.get().strip()
        if not address or not password:
            messagebox.showwarning(
                "Input Error", "Please enter the address and password."
            )
            return

        try:
            # Initialize RconPy
            self.rcon_client = RconPy(address, port, password)
            self.rcon_client.connect()
            self.rcon_client.login()

            if not self.rcon_client.is_login():
                raise ConnectionError("Login failed (Incorrect password?)")

            messagebox.showinfo("Success", "Connected to server successfully!")
            self.log_message(f"Connected to {address}:{port}")
            self.send_button.config(state=tk.NORMAL)
            self.command_entry.config(state=tk.NORMAL)
            self.save_config(address, port, password)
            self.fetch_player_list()
            self.fetch_datapacks()

            # Start auto-refresh
            self.auto_refresh()

        except (OSError, ConnectionError, TimeoutError) as e:
            self.rcon_client = None
            messagebox.showerror("Error", f"Failed to connect:\n{e}")
            self.log_message(f"Connection error: {e}")

    def send_command(self, event: tk.Event[Any] | None = None) -> None:
        """Send RCON command in background thread to prevent UI freezing.

        Args:
            event: Optional tkinter event (for Enter key binding).
        """
        if not self.rcon_client:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        command = self.command_entry.get().strip()
        if not command:
            return

        # Run in a separate thread to prevent UI freezing
        def run_cmd() -> None:
            try:
                if not self.rcon_client:
                    return
                response = self.rcon_client.command(command)
                self.root.after(0, lambda: self.update_output(command, response))
                if command.lower().startswith("list") and response:
                    self.root.after(0, lambda: self.update_player_list(response))
            except (OSError, ConnectionError, TimeoutError) as exc:
                # Convert exception to string immediately for lambda capture
                error_msg = str(exc)
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Error", f"Failed to send command:\n{error_msg}"
                    ),
                )
                self.root.after(
                    0, lambda: self.log_message(f"Command error: {error_msg}")
                )

        Thread(target=run_cmd, daemon=True).start()

    def update_output(self, command: str, response: str | None) -> None:
        """Update output box with command and response.

        Args:
            command: Executed command.
            response: Server response (may be None on error).
        """
        self.output_box.config(state=tk.NORMAL)
        display_response = response if response else "(no response)"
        self.output_box.insert(tk.END, f"> {command}\n{display_response}\n\n")
        self.output_box.see(tk.END)
        self.output_box.config(state=tk.DISABLED)
        self.log_message(f"Command: {command} | Response: {display_response}")

    def fetch_player_list(self) -> None:
        """Fetch current player list from server (non-blocking)."""
        if self.rcon_client:
            try:
                response = self.rcon_client.command("list")
                if response:
                    self.update_player_list(response)
            except (OSError, ConnectionError, TimeoutError):
                pass  # Silently fail for auto-refresh

    def update_player_list(self, list_response: str) -> None:
        """Parse and display player list from 'list' command response.

        Args:
            list_response: Raw response from 'list' command.
        """
        self.player_list_box.delete(0, tk.END)
        try:
            # Parse: "There are 2 of a max of 20 players online: Player1, Player2"
            if ":" in list_response:
                parts = list_response.split(":")
                if len(parts) > 1:
                    player_segment = parts[1].strip()
                    if player_segment:
                        players = [
                            p.strip() for p in player_segment.split(",") if p.strip()
                        ]
                        if players:
                            for player in players:
                                self.player_list_box.insert(tk.END, player)
                            return
            self.player_list_box.insert(tk.END, "No players (or parse error)")
        except (ValueError, IndexError) as e:
            self.player_list_box.insert(tk.END, f"Error: {e}")

    def fetch_datapacks(self) -> None:
        """Fetch datapack list from server (non-blocking)."""
        if self.rcon_client:
            try:
                response = self.rcon_client.command("datapack list")
                if response:
                    self.update_datapack_list(response)
            except (OSError, ConnectionError, TimeoutError):
                pass  # Silently fail for auto-refresh

    def update_datapack_list(self, response: str) -> None:
        """Parse and display datapack list from 'datapack list' response.

        Args:
            response: Raw response from 'datapack list' command.
        """
        self.datapack_list_box.delete(0, tk.END)
        try:
            entries = re.findall(r"\[([^]]+)\]", response)
            if entries:
                for dp in entries:
                    self.datapack_list_box.insert(tk.END, dp.strip())
            else:
                # Fallback if output format differs
                self.datapack_list_box.insert(tk.END, "No datapacks found")
        except re.error as e:
            self.datapack_list_box.insert(tk.END, f"Error: {e}")

    def toggle_password(self) -> None:
        """Toggle password visibility in password entry field."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def toggle_dark_mode(self) -> None:
        """Toggle between dark and light themes."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply color theme to all widgets based on dark_mode setting."""
        colors = self._get_theme_colors()

        # Apply to root
        self.root.configure(bg=colors["root_bg"])
        self.player_frame.config(bg=colors["root_bg"])

        # Apply to cached widgets (much faster than tree traversal)
        for widget, widget_type in self._themeable_widgets:
            if widget_type == "label":
                widget.config(bg=colors["root_bg"], fg=colors["label_fg"])
            elif widget_type == "entry":
                widget.config(
                    bg=colors["entry_bg"],
                    fg=colors["entry_fg"],
                    insertbackground=colors["entry_fg"],
                )
            elif widget_type == "button":
                widget.config(bg=colors["btn_bg"], fg=colors["btn_fg"])
            elif widget_type == "checkbutton":
                widget.config(
                    bg=colors["root_bg"],
                    fg=colors["label_fg"],
                    selectcolor=colors["root_bg"],
                )
            elif widget_type == "scrolledtext":
                widget.config(
                    bg=colors["entry_bg"],
                    fg=colors["entry_fg"],
                    insertbackground=colors["entry_fg"],
                )
            elif widget_type == "listbox":
                widget.config(bg=colors["entry_bg"], fg=colors["entry_fg"])

    def _get_theme_colors(self) -> dict[str, str]:
        """Get color palette for current theme.

        Returns:
            dict: Color mappings for theme elements.
        """
        if self.dark_mode:
            return {
                "root_bg": "#2e2e2e",
                "label_fg": "#ffffff",
                "entry_bg": "#3c3f41",
                "entry_fg": "#ffffff",
                "btn_bg": "#5c5f61",
                "btn_fg": "#ffffff",
            }
        else:
            return {
                "root_bg": "#f0f0f0",
                "label_fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "btn_bg": "#e0e0e0",
                "btn_fg": "#000000",
            }

    def auto_refresh(self) -> None:
        """Periodically refresh player list with rate limiting.

        Only refreshes when:
        - Client is connected
        - Window is visible (not minimized/hidden)

        Implements exponential backoff on consecutive failures.
        """
        # Only refresh if connected and window is visible
        if self.rcon_client and self.root.winfo_viewable():
            try:
                self.fetch_player_list()
                # Success - reset failure counter and interval
                self._refresh_failures = 0
                self._refresh_interval = 5000
            except Exception:
                # Failure - implement exponential backoff
                self._refresh_failures += 1
                # Cap at 60 seconds max interval
                self._refresh_interval = min(
                    5000 * (2 ** self._refresh_failures), 60000
                )

        self.root.after(self._refresh_interval, self.auto_refresh)

    def setup_ui(self) -> None:
        """Initialize all UI components and layout."""
        self._create_connection_widgets()
        self._create_command_widgets()
        self._create_output_widgets()
        self._create_sidebar_widgets()
        self._layout_widgets()
        self._cache_themeable_widgets()

    def _cache_themeable_widgets(self) -> None:
        """Cache all widgets that need theme updates for faster theme switching."""
        self._themeable_widgets = [
            (self.address_label, "label"),
            (self.address_entry, "entry"),
            (self.port_label, "label"),
            (self.port_entry, "entry"),
            (self.password_label, "label"),
            (self.password_entry, "entry"),
            (self.show_password_check, "checkbutton"),
            (self.connect_button, "button"),
            (self.dark_toggle_button, "button"),
            (self.command_label, "label"),
            (self.command_entry, "entry"),
            (self.send_button, "button"),
            (self.output_box, "scrolledtext"),
            (self.player_label, "label"),
            (self.player_list_box, "listbox"),
            (self.datapack_label, "label"),
            (self.datapack_list_box, "listbox"),
        ]

    def _create_connection_widgets(self) -> None:
        """Create connection input widgets (address, port, password)."""
        self.address_label = tk.Label(self.root, text="RCON Address:")
        self.address_entry = tk.Entry(self.root, width=30)
        self.address_entry.insert(0, self.config.get("address", ""))

        self.port_label = tk.Label(self.root, text="Port:")
        self.port_entry = tk.Entry(self.root, width=30)
        self.port_entry.insert(0, str(self.config.get("port", 25575)))

        self.password_label = tk.Label(self.root, text="Password:")
        self.password_entry = tk.Entry(self.root, show="*", width=30)
        self.password_entry.insert(0, self.config.get("password", ""))

        self.show_password_var = tk.BooleanVar()
        self.show_password_check = tk.Checkbutton(
            self.root,
            text="Show Password",
            variable=self.show_password_var,
            command=self.toggle_password,
        )

        self.connect_button = tk.Button(
            self.root, text="Connect", command=self.connect_to_server
        )
        self.dark_toggle_button = tk.Button(
            self.root, text="Toggle Dark Mode", command=self.toggle_dark_mode
        )

    def _create_command_widgets(self) -> None:
        """Create command input widgets."""
        self.command_label = tk.Label(self.root, text="Command:")
        self.command_entry = tk.Entry(self.root, width=30, state=tk.DISABLED)
        self.command_entry.bind("<Return>", self.send_command)

        self.send_button = tk.Button(
            self.root, text="Send", command=self.send_command, state=tk.DISABLED
        )

    def _create_output_widgets(self) -> None:
        """Create output display widget."""
        self.output_box = scrolledtext.ScrolledText(
            self.root, width=60, height=15, state=tk.DISABLED
        )

    def _create_sidebar_widgets(self) -> None:
        """Create sidebar widgets (player list, datapack list)."""
        self.player_frame = tk.Frame(self.root)
        self.player_label = tk.Label(self.player_frame, text="Online Players")
        self.player_list_box = tk.Listbox(self.player_frame, height=12, width=30)

        self.datapack_label = tk.Label(self.player_frame, text="Datapacks")
        self.datapack_scroll_y = tk.Scrollbar(self.player_frame, orient="vertical")
        self.datapack_scroll_x = tk.Scrollbar(self.player_frame, orient="horizontal")
        self.datapack_list_box = tk.Listbox(
            self.player_frame,
            height=12,
            width=30,
            xscrollcommand=self.datapack_scroll_x.set,
            yscrollcommand=self.datapack_scroll_y.set,
            exportselection=False,
        )
        self.datapack_scroll_y.config(command=self.datapack_list_box.yview)
        self.datapack_scroll_x.config(command=self.datapack_list_box.xview)

    def _layout_widgets(self) -> None:
        """Arrange all widgets using grid layout."""
        # Connection widgets
        self.address_label.grid(row=0, column=0, sticky="e", pady=2)
        self.address_entry.grid(row=0, column=1, sticky="w", pady=2)
        self.port_label.grid(row=1, column=0, sticky="e", pady=2)
        self.port_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.password_label.grid(row=2, column=0, sticky="e", pady=2)
        self.password_entry.grid(row=2, column=1, sticky="w", pady=2)
        self.show_password_check.grid(row=3, column=1, sticky="w", pady=2)

        # Command widgets
        self.command_label.grid(row=4, column=0, sticky="e", pady=2)
        self.command_entry.grid(row=4, column=1, sticky="w", pady=2)
        self.connect_button.grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.send_button.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        self.dark_toggle_button.grid(row=5, column=1, sticky="e", padx=85, pady=2)

        # Output widget
        self.output_box.grid(row=6, column=0, columnspan=2, pady=5)

        # Sidebar widgets
        self.player_frame.grid(row=0, column=2, rowspan=8, padx=10, sticky="ns")
        self.player_label.pack()
        self.player_list_box.pack()
        tk.Label(self.player_frame, text="\n").pack()

        self.datapack_label.pack()
        self.datapack_list_box.pack(fill="both", expand=True)
        self.datapack_scroll_y.pack(side="right", fill="y")
        self.datapack_scroll_x.pack(side="bottom", fill="x")

    def run(self) -> None:
        """Start the GUI event loop."""
        self.root.mainloop()


def main() -> None:
    """CLI entry point for mcrcon-gui command."""
    app = RconGUI()
    app.run()


if __name__ == "__main__":
    main()
