# GEMINI.md

## Project Overview

`mc-rcon` is a Python-based project that provides tools for interacting with Minecraft servers via the RCON (Remote Console) protocol. It offers both a command-line interface (CLI) and a graphical user interface (GUI) to send commands and manage a Minecraft server remotely.

### Key Components

- **`mcrconpy`**: The core Python package containing the RCON client implementation.
  - `cli.py`: The entry point for the command-line interface.
  - `packet.py`, `connection.py`, `authn.py`: Core logic for RCON protocol handling.
- **`mcrcon-gui.py`**: A Tkinter-based GUI application.
  - Allows connecting to a server with address, port, and password.
  - Provides a console for sending commands and viewing responses.
  - Displays online players and datapack lists.
  - Supports dark mode.
- **`aiorcon`**: An asynchronous RCON client module (likely `aio-mc-rcon`).
- **`mcrcon_ipv6`**: Module potentially providing IPv6 support for RCON.

## Building and Running

This project uses **Poetry** for dependency management.

### Prerequisites

- Python 3.10+
- Poetry

### Setup

1. **Install Dependencies:**

```bash
poetry install
```

### Usage

#### CLI

To use the command-line interface:

```bash
# General syntax
python -m mcrconpy.cli -a <ADDRESS> -p <PORT> -P <PASSWORD>

# Example
python -m mcrconpy.cli -a localhost -p 25575 -P mysecretpassword
```

Arguments:

- `-a`, `--address`: Minecraft Server TCP address (Required).
- `-p`, `--port`: Minecraft Server RCON Port (Default: 25575).
- `-P`, `--password`: User password (Required).
- `-A`, `--audit`: Enable audit logging to a JSONL file.

#### GUI

To launch the graphical user interface:

```bash
python mcrcon-gui.py
```

The GUI requires `tkinter` to be installed on your system.

## Development Conventions

- **Dependency Management:** The project uses `pyproject.toml` with Poetry.
- **Code Style:**
  - `.editorconfig` is present, suggesting adherence to standard formatting rules.
  - `.ruff_cache` suggests **Ruff** is used for linting and formatting.
  - `.shellcheckrc` indicates ShellCheck usage for shell scripts (if any).
- **Type Hinting:** The code uses Python type hints (e.g., `def main() -> None:`).

## File Structure

- `mcrconpy/`: Main package source code.
- `aiorcon/`: Async RCON client implementation.
- `mcrcon_ipv6/`: IPv6 specific implementation.
- `mcrcon-gui.py`: Main script for the GUI application.
- `mcrcon-gui-2.py`: Likely an alternative or older version of the GUI.
- `pyproject.toml`: Poetry configuration and dependencies.
