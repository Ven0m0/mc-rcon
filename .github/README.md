# MC-RCON

A unified Python RCON client for Minecraft servers, featuring both a synchronous/asynchronous library, a Command Line Interface (CLI), and a Graphical User Interface (GUI).

## Features

- **Unified Library**: `mcrconpy` supports IPv4 and IPv6 transparently.
- **Async Support**: `mcrconpy.aio` provides an `asyncio`-compatible client.
- **CLI**: robust command-line tool.
- **GUI**: Tkinter-based graphical interface with dark mode and syntax highlighting.

## Installation

Using Poetry:

```bash
poetry install
```

## Usage

### CLI

Run the CLI using the installed script or python module:

```bash
# Using poetry script
poetry run mcrcon -a localhost -p 25575 -P password

# Or directly with python
python -m mcrconpy.cli -a localhost -p 25575 -P password
```

Arguments:

- `-a`, `--address`: Server address (required).
- `-p`, `--port`: RCON port (default 25575).
- `-P`, `--password`: RCON password (required).
- `-A`, `--audit`: Save audit logs to JSONL.

### GUI

Run the GUI:

```bash
# Using poetry script
poetry run mcrcon-gui

# Or directly with python
python -m mcrconpy.gui
```

### Library Usage

**Synchronous:**

```python
from mcrconpy import RconPy

with RconPy("localhost", 25575, "password") as rcon:
    rcon.connect()
    rcon.login()
    response = rcon.command("list")
    print(response)
```

**Asynchronous:**

```python
import asyncio
from mcrconpy.aio import AsyncClient

async def main():
    async with AsyncClient("localhost", 25575, "password") as client:
        response, req_id = await client.send_cmd("list")
        print(response)

asyncio.run(main())
```

## Structure

- `mcrconpy/`: Main package.
  - `connection.py`: Socket handling (IPv4/IPv6).
  - `aio.py`: Async implementation.
  - `gui.py`: GUI implementation.
  - `cli.py`: CLI implementation.
  - `packet.py`: RCON packet structure.
