import tkinter as tk
from tkinter import scrolledtext, messagebox
from mcrconpy.core import Rcon as RconPy
import json
import os
import datetime
import re
from threading import Thread

CONFIG_FILE = "rcon_config.json"
LOG_FILE = "rcon_log.txt"


class RconGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minecraft RCON GUI")

        self.rcon_client = None
        self.config = self.load_config()
        self.dark_mode = True

        self.setup_ui()
        self.apply_theme()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self, address, port, password):
        config = {"address": address, "port": port, "password": password}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def connect_to_server(self):
        address = self.address_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Port must be an integer.")
            return

        password = self.password_entry.get().strip()
        if not address or not password:
            messagebox.showwarning("Input Error", "Please enter the address and password.")
            return

        try:
            # Initialize RconPy
            self.rcon_client = RconPy(address, port, password)
            self.rcon_client.connect()
            self.rcon_client.login()

            if not self.rcon_client.is_login():
                raise Exception("Login failed (Incorrect password?)")

            messagebox.showinfo("Success", "Connected to server successfully!")
            self.log_message(f"Connected to {address}:{port}")
            self.send_button.config(state=tk.NORMAL)
            self.command_entry.config(state=tk.NORMAL)
            self.save_config(address, port, password)
            self.fetch_player_list()
            self.fetch_datapacks()

            # Start auto-refresh
            self.auto_refresh()

        except Exception as e:
            self.rcon_client = None
            messagebox.showerror("Error", f"Failed to connect:\n{e}")
            self.log_message(f"Connection error: {e}")

    def send_command(self, event=None):
        if not self.rcon_client:
            messagebox.showwarning("Not Connected", "Please connect first.")
            return
        command = self.command_entry.get().strip()
        if not command:
            return

        # Run in a separate thread to prevent UI freezing
        def run_cmd():
            try:
                response = self.rcon_client.command(command)
                self.root.after(0, lambda: self.update_output(command, response))
                if command.lower().startswith("list"):
                    self.root.after(0, lambda: self.update_player_list(response))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send command:\n{e}"))
                self.root.after(0, lambda: self.log_message(f"Command error: {e}"))

        Thread(target=run_cmd, daemon=True).start()

    def update_output(self, command, response):
        self.output_box.config(state=tk.NORMAL)
        self.output_box.insert(tk.END, f"> {command}\n{response}\n\n")
        self.output_box.see(tk.END)
        self.output_box.config(state=tk.DISABLED)
        self.log_message(f"Command: {command} | Response: {response}")

    def fetch_player_list(self):
        if self.rcon_client:
            try:
                # Basic non-threaded check for auto-refresh, or threaded if preferred
                # For auto-refresh, better use thread or just quick call if network is fast
                response = self.rcon_client.command("list")
                self.update_player_list(response)
            except Exception:
                pass

    def update_player_list(self, list_response):
        self.player_list_box.delete(0, tk.END)
        try:
            # "There are 2 of a max of 20 players online: Player1, Player2"
            if ":" in list_response:
                parts = list_response.split(":")
                if len(parts) > 1:
                    player_segment = parts[1].strip()
                    if player_segment:
                        players = [p.strip() for p in player_segment.split(",") if p.strip()]
                        if players:
                            for player in players:
                                self.player_list_box.insert(tk.END, player)
                            return
            self.player_list_box.insert(tk.END, "No players (or parse error)")
        except Exception as e:
            self.player_list_box.insert(tk.END, f"Error: {e}")

    def fetch_datapacks(self):
        if self.rcon_client:
            try:
                response = self.rcon_client.command("datapack list")
                self.update_datapack_list(response)
            except Exception:
                pass

    def update_datapack_list(self, response):
        self.datapack_list_box.delete(0, tk.END)
        try:
            entries = re.findall(r"[(.*?)]", response)
            if entries:
                for dp in entries:
                    self.datapack_list_box.insert(tk.END, dp.strip())
            else:
                # Try fallback if output format differs
                self.datapack_list_box.insert(tk.END, "No datapacks found")
        except Exception as e:
            self.datapack_list_box.insert(tk.END, f"Error: {e}")

    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.root.configure(bg="#2e2e2e")
            colors = {
                "label_fg": "#ffffff",
                "entry_bg": "#3c3f41",
                "entry_fg": "#ffffff",
                "btn_bg": "#5c5f61",
                "btn_fg": "#ffffff",
            }
        else:
            self.root.configure(bg="#f0f0f0")
            colors = {
                "label_fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "btn_bg": "#e0e0e0",
                "btn_fg": "#000000",
            }

        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.root["bg"], fg=colors["label_fg"])
            elif isinstance(widget, tk.Entry):
                widget.config(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["entry_fg"])
            elif isinstance(widget, tk.Button):
                widget.config(bg=colors["btn_bg"], fg=colors["btn_fg"])
            elif isinstance(widget, tk.Checkbutton):
                widget.config(bg=self.root["bg"], fg=colors["label_fg"], selectcolor=self.root["bg"])

        self.command_entry.config(insertbackground=colors["entry_fg"])
        self.output_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["entry_fg"])
        self.player_list_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"])
        self.datapack_list_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"])
        self.player_frame.config(bg=self.root["bg"])

    def auto_refresh(self):
        if self.rcon_client:
            self.fetch_player_list()
        self.root.after(5000, self.auto_refresh)

    def setup_ui(self):
        self.address_label = tk.Label(self.root, text="RCON Address:")
        self.address_entry = tk.Entry(self.root, width=30)
        self.address_entry.insert(0, self.config.get("address", ""))

        self.port_label = tk.Label(self.root, text="Port:")
        self.port_entry = tk.Entry(self.root, width=30)
        self.port_entry.insert(0, self.config.get("port", "25575"))

        self.password_label = tk.Label(self.root, text="Password:")
        self.password_entry = tk.Entry(self.root, show="*", width=30)
        self.password_entry.insert(0, self.config.get("password", ""))

        self.show_password_var = tk.BooleanVar()
        self.show_password_check = tk.Checkbutton(
            self.root, text="Show Password", variable=self.show_password_var, command=self.toggle_password
        )

        self.connect_button = tk.Button(self.root, text="Connect", command=self.connect_to_server)
        self.dark_toggle_button = tk.Button(self.root, text="Toggle Dark Mode", command=self.toggle_dark_mode)

        self.command_label = tk.Label(self.root, text="Command:")
        self.command_entry = tk.Entry(self.root, width=30, state=tk.DISABLED)
        self.command_entry.bind("<Return>", self.send_command)

        self.send_button = tk.Button(self.root, text="Send", command=self.send_command, state=tk.DISABLED)
        self.output_box = scrolledtext.ScrolledText(self.root, width=60, height=15, state=tk.DISABLED)

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

        # Layout
        self.address_label.grid(row=0, column=0, sticky="e", pady=2)
        self.address_entry.grid(row=0, column=1, sticky="w", pady=2)
        self.port_label.grid(row=1, column=0, sticky="e", pady=2)
        self.port_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.password_label.grid(row=2, column=0, sticky="e", pady=2)
        self.password_entry.grid(row=2, column=1, sticky="w", pady=2)
        self.show_password_check.grid(row=3, column=1, sticky="w", pady=2)
        self.command_label.grid(row=4, column=0, sticky="e", pady=2)
        self.command_entry.grid(row=4, column=1, sticky="w", pady=2)
        self.connect_button.grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.send_button.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        self.dark_toggle_button.grid(row=5, column=1, sticky="e", padx=85, pady=2)
        self.output_box.grid(row=6, column=0, columnspan=2, pady=5)

        self.player_frame.grid(row=0, column=2, rowspan=8, padx=10, sticky="ns")
        self.player_label.pack()
        self.player_list_box.pack()
        tk.Label(self.player_frame, text="\n").pack()

        self.datapack_label.pack()
        self.datapack_list_box.pack(fill="both", expand=True)
        self.datapack_scroll_y.pack(side="right", fill="y")
        self.datapack_scroll_x.pack(side="bottom", fill="x")

    def run(self):
        self.root.mainloop()


def main():
    app = RconGUI()
    app.run()


if __name__ == "__main__":
    main()
