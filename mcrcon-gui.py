import tkinter as tk
from tkinter import scrolledtext, messagebox
from mcipc.rcon.je import Client
import socket
import json
import os
import datetime
import re

# Global client object
rcon_client = None
CONFIG_FILE = "rcon_config.json"
LOG_FILE = "rcon_log.txt"

datapack_list_box = None


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(address, port, password):
    config = {"address": address, "port": port, "password": password}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def connect_to_server():
    global rcon_client
    address = address_entry.get().strip()
    port = int(port_entry.get().strip())
    password = password_entry.get().strip()
    if not address or not password:
        messagebox.showwarning("Input Error", "Please enter the address and password.")
        return
    try:
        rcon_client = Client(address, port, timeout=5)
        rcon_client.connect()
        rcon_client.login(password)
        messagebox.showinfo("Success", "Connected to server successfully!")
        log_message(f"Connected to {address}:{port}")
        send_button.config(state=tk.NORMAL)
        command_entry.config(state=tk.NORMAL)
        save_config(address, port, password)
        fetch_player_list()
        fetch_datapacks()
    except socket.timeout:
        messagebox.showerror("Connection Timeout", "Connection timed out. Check the address and port.")
        log_message("Connection timed out")
    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "Connection refused. Is RCON enabled?")
        log_message("Connection refused")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to connect:\n{e}")
        log_message(f"Connection error: {e}")


def send_command(event=None):
    global rcon_client
    if not rcon_client:
        messagebox.showwarning("Not Connected", "Please connect first.")
        return
    command = command_entry.get().strip()
    if not command:
        return
    try:
        response = rcon_client.run(command)
        output_box.config(state=tk.NORMAL)
        output_box.insert(tk.END, f"> {command}\n{response}\n\n")
        output_box.see(tk.END)
        output_box.config(state=tk.DISABLED)
        log_message(f"Command: {command} | Response: {response}")
        if command.lower() == "/list":
            update_player_list(response)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send command:\n{e}")
        log_message(f"Command error: {e}")


def fetch_player_list():
    try:
        if rcon_client:
            response = rcon_client.run("/list")
            update_player_list(response)
    except Exception as e:
        player_list_box.delete(0, tk.END)
        player_list_box.insert(tk.END, "Failed to get player list.")
        log_message(f"Player list fetch error: {e}")


def update_player_list(list_response):
    player_list_box.delete(0, tk.END)
    try:
        if ":" in list_response:
            parts = list_response.split(":")
            if len(parts) > 1:
                player_segment = parts[1].strip()
                players = [p.strip() for p in player_segment.split(",") if p.strip()]
                if players:
                    for player in players:
                        player_list_box.insert(tk.END, player)
                    return
        player_list_box.insert(tk.END, "No players")
    except Exception as e:
        player_list_box.insert(tk.END, f"Error parsing list: {e}")
        log_message(f"List parsing error: {e}")


def fetch_datapacks():
    try:
        if rcon_client:
            response = rcon_client.run("datapack list")
            update_datapack_list(response)
    except Exception as e:
        datapack_list_box.delete(0, tk.END)
        datapack_list_box.insert(tk.END, "Failed to get datapacks.")
        log_message(f"Datapack list fetch error: {e}")


def update_datapack_list(response):
    datapack_list_box.delete(0, tk.END)
    try:
        entries = re.findall(r"\[(.*?)\]", response)
        if entries:
            for dp in entries:
                datapack_list_box.insert(tk.END, dp.strip())
        else:
            datapack_list_box.insert(tk.END, "No datapacks found")
    except Exception as e:
        datapack_list_box.insert(tk.END, f"Error parsing datapacks: {e}")
        log_message(f"Datapack parsing error: {e}")


def toggle_password():
    if show_password_var.get():
        password_entry.config(show="")
    else:
        password_entry.config(show="*")


def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()


def apply_theme():
    if dark_mode:
        root.configure(bg="#2e2e2e")
        colors = {
            "label_fg": "#ffffff",
            "entry_bg": "#3c3f41",
            "entry_fg": "#ffffff",
            "btn_bg": "#5c5f61",
            "btn_fg": "#ffffff",
        }
    else:
        root.configure(bg="#f0f0f0")
        colors = {
            "label_fg": "#000000",
            "entry_bg": "#ffffff",
            "entry_fg": "#000000",
            "btn_bg": "#e0e0e0",
            "btn_fg": "#000000",
        }

    for widget in root.winfo_children():
        if isinstance(widget, tk.Label):
            widget.config(bg=root["bg"], fg=colors["label_fg"])
        elif isinstance(widget, tk.Entry):
            widget.config(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["entry_fg"])
        elif isinstance(widget, tk.Button):
            widget.config(bg=colors["btn_bg"], fg=colors["btn_fg"])
        elif isinstance(widget, tk.Checkbutton):
            widget.config(bg=root["bg"], fg=colors["label_fg"], selectcolor=root["bg"])
    command_entry.config(insertbackground=colors["entry_fg"])
    output_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"], insertbackground=colors["entry_fg"])
    player_list_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"])
    datapack_list_box.config(bg=colors["entry_bg"], fg=colors["entry_fg"])
    player_frame.config(bg=root["bg"])


def auto_refresh():
    fetch_player_list()
    root.after(5000, auto_refresh)


# GUI setup
root = tk.Tk()
root.title("Minecraft RCON GUI")
config = load_config()
dark_mode = True

address_label = tk.Label(root, text="RCON Address:")
address_entry = tk.Entry(root, width=30)
address_entry.insert(0, config.get("address", ""))
port_label = tk.Label(root, text="Port:")
port_entry = tk.Entry(root, width=30)
port_entry.insert(0, config.get("port", "25575"))
password_label = tk.Label(root, text="Password:")
password_entry = tk.Entry(root, show="*", width=30)
password_entry.insert(0, config.get("password", ""))
show_password_var = tk.BooleanVar()
show_password_check = tk.Checkbutton(root, text="Show Password", variable=show_password_var, command=toggle_password)
connect_button = tk.Button(root, text="Connect", command=connect_to_server)
dark_toggle_button = tk.Button(root, text="Toggle Dark Mode", command=toggle_dark_mode)
command_label = tk.Label(root, text="Command:")
command_entry = tk.Entry(root, width=30, state=tk.DISABLED)
command_entry.bind("<Return>", send_command)
send_button = tk.Button(root, text="Send", command=send_command, state=tk.DISABLED)
output_box = scrolledtext.ScrolledText(root, width=60, height=15, state=tk.DISABLED)

player_frame = tk.Frame(root)
player_label = tk.Label(player_frame, text="Online Players")
player_list_box = tk.Listbox(player_frame, height=12, width=30)

# Datapack section with scrollbars
datapack_label = tk.Label(player_frame, text="Datapacks")
datapack_scroll_y = tk.Scrollbar(player_frame, orient="vertical")
datapack_scroll_x = tk.Scrollbar(player_frame, orient="horizontal")
datapack_list_box = tk.Listbox(
    player_frame,
    height=12,
    width=30,
    xscrollcommand=datapack_scroll_x.set,
    yscrollcommand=datapack_scroll_y.set,
    exportselection=False,
)
datapack_scroll_y.config(command=datapack_list_box.yview)
datapack_scroll_x.config(command=datapack_list_box.xview)

# Layout
address_label.grid(row=0, column=0, sticky="e", pady=2)
address_entry.grid(row=0, column=1, sticky="w", pady=2)
port_label.grid(row=1, column=0, sticky="e", pady=2)
port_entry.grid(row=1, column=1, sticky="w", pady=2)
password_label.grid(row=2, column=0, sticky="e", pady=2)
password_entry.grid(row=2, column=1, sticky="w", pady=2)
show_password_check.grid(row=3, column=1, sticky="w", pady=2)
command_label.grid(row=4, column=0, sticky="e", pady=2)
command_entry.grid(row=4, column=1, sticky="w", pady=2)
connect_button.grid(row=5, column=0, sticky="e", padx=5, pady=2)
send_button.grid(row=5, column=1, sticky="w", padx=5, pady=2)
dark_toggle_button.grid(row=5, column=1, sticky="e", padx=85, pady=2)
output_box.grid(row=6, column=0, columnspan=2, pady=5)

player_frame.grid(row=0, column=2, rowspan=8, padx=10, sticky="ns")
player_label.pack()
player_list_box.pack()
tk.Label(player_frame, text="\n").pack()  # Spacer with more height

datapack_label.pack()
datapack_list_box.pack(fill="both", expand=True)
datapack_scroll_y.pack(side="right", fill="y")
datapack_scroll_x.pack(side="bottom", fill="x")

apply_theme()
auto_refresh()
root.mainloop()
