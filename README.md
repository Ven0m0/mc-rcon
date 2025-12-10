# mc-rcon

> A high-performance Python RCON client for Minecraft servers

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Features

- **🚀 High Performance**: Built with `orjson` for fast JSON serialization and `uvloop` for async I/O
- **⚡ Async & Sync**: Both synchronous and asynchronous client implementations
- **🔒 Type Safe**: Fully typed with strict mypy compliance
- **📝 Audit Logging**: Optional JSONL audit trail for all commands
- **🎨 Modern Python**: Uses Python 3.10+ features (pattern matching, union types)
- **🖥️ GUI & CLI**: Command-line interface and Tkinter-based GUI

## Installation

### Using pip

```bash
pip install mc-rcon
```

### Using Poetry

```bash
poetry add mc-rcon
```

### Using uv

```bash
uv add mc-rcon
```

### From source

```bash
git clone https://github.com/Ven0m0/mc-rcon.git
cd mc-rcon
poetry install
```

## Quick Start

### Synchronous Client

```python
from mcrconpy import Rcon

# Using context manager (recommended)
with Rcon("localhost", 25575, "your_password") as client:
    response = client.command("list")
    print(response)

# Manual connection management
client = Rcon("localhost", 25575, "your_password")
client.connect()
client.login()
response = client.command("say Hello from Python!")
print(response)
client.close()
```

### Asynchronous Client

```python
import asyncio
from mcrconpy import AsyncRcon

async def main():
    async with AsyncRcon("localhost", 25575, "your_password") as client:
        response = await client.command("list")
        print(response)

        # Send multiple commands
        players = await client.command("list")
        time = await client.command("time query daytime")
        print(f"Players: {players}")
        print(f"Time: {time}")

# Run with uvloop for best performance (Linux/macOS)
asyncio.run(main())
```

## CLI Usage

### Basic command execution

```bash
# Synchronous mode
mcrcon -a localhost -p 25575 -P your_password

# Asynchronous mode
mcrcon -a localhost -p 25575 -P your_password --async-mode
```

### Interactive REPL

Once connected, you'll see a `>>` prompt where you can type commands:

```
>> list
There are 5 players online: Player1, Player2, Player3, Player4, Player5
>> time set day
Set the time to 1000
>> quit
```

### GUI Application

Launch the graphical interface:

```bash
mcrcon-gui
```

The GUI provides:
- Connection manager (address, port, password)
- Interactive console
- Command history
- Dark mode support

## API Reference

### `Rcon` (Synchronous Client)

```python
class Rcon:
    def __init__(self, address: str, port: int, password: str) -> None: ...
    def connect(self) -> None: ...
    def login(self) -> bool: ...
    def command(self, cmd: str) -> str | None: ...
    def is_login(self) -> bool: ...
    def close(self) -> None: ...
```

### `AsyncRcon` (Asynchronous Client)

```python
class AsyncRcon:
    def __init__(self, host: str, port: int, password: str) -> None: ...
    async def connect(self, timeout: float = 2.0) -> None: ...
    async def command(self, cmd: str, timeout: float = 2.0) -> str: ...
    async def close(self) -> None: ...
```

### `Packet` (Low-level Protocol)

```python
class Packet:
    @staticmethod
    def build(req_id: int, packet_type: int, data: str | bytes) -> bytes: ...

    @staticmethod
    def decode(data: bytes) -> tuple[int, int, int, str]: ...

    @staticmethod
    def read_length(data: bytes) -> int: ...
```

## Audit Logging

Enable audit logging to track all RCON commands:

```python
from mcrconpy import Rcon, Audit

with Rcon("localhost", 25575, "password") as client:
    response = client.command("list")

    # Save to audit log
    Audit.to_save({
        "command": "list",
        "response": response,
        "timestamp": time.time()
    })

# Load audit history
history = Audit.to_load()
for entry in history:
    print(entry)
```

Audit logs are stored as JSONL at:
- Linux: `~/.local/state/mcrconpy/audit.jsonl`
- macOS: `~/Library/Logs/mcrconpy/audit.jsonl`
- Windows: `C:\Users\<user>\AppData\Local\mcrconpy\Logs\audit.jsonl`

## Performance

This library is optimized for high performance:

| Component | Technology | Benefit |
|-----------|-----------|---------|
| JSON Serialization | `orjson` | ~6x faster than stdlib `json` |
| Async I/O | `uvloop` | Node.js-level event loop performance |
| Type Safety | `mypy --strict` | Catch errors at development time |
| Zero-copy Buffers | `memoryview` | Reduced memory allocations |

### Benchmarks

```python
# Async client with uvloop (10,000 commands)
# Average: 0.8ms per command
# Throughput: ~1,250 commands/sec
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/Ven0m0/mc-rcon.git
cd mc-rcon

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Code Quality

```bash
# Format code (Black style)
ruff format .

# Lint code
ruff check .

# Type check
mypy --strict mcrconpy/

# Run tests
pytest --durations=0 -v
```

### Project Standards

- **Formatting**: Black style via `ruff format` (88 char line length)
- **Linting**: Ruff with strict rules (Pyflakes, pycodestyle, isort, pyupgrade)
- **Type Safety**: 100% typed with `mypy --strict`
- **Testing**: Pytest with async support and coverage reporting
- **Performance**: Optimized with `orjson`, `uvloop`, and zero-copy techniques

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow code standards:
   - Run `ruff format .` before committing
   - Ensure `mypy --strict` passes
   - Add tests for new features
   - Maintain >80% code coverage
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Protocol Reference

This implementation follows the [Source RCON Protocol](https://developer.valvesoftware.com/wiki/Source_RCON_Protocol) used by Minecraft servers.

### Packet Structure

```
Field         Type        Value
Size          int32       Packet size (excluding this field)
ID            int32       Request ID
Type          int32       Command type (3=AUTH, 2=EXECCOMMAND, 0=RESPONSE)
Body          byte[]      Null-terminated ASCII string
Pad           byte        NULL byte
```

### Supported Commands

All standard Minecraft server commands are supported:
- `list` - List online players
- `say <message>` - Broadcast message
- `time set <value>` - Set world time
- `weather <type>` - Change weather
- `op <player>` - Grant operator status
- And many more...

## Troubleshooting

### Connection Timeout

```python
from mcrconpy.exceptions import ServerTimeOut

try:
    with Rcon("localhost", 25575, "password") as client:
        response = client.command("list")
except ServerTimeOut:
    print("Server took too long to respond")
```

### Authentication Failed

```python
from mcrconpy.exceptions import ServerAuthError

try:
    with Rcon("localhost", 25575, "wrong_password") as client:
        pass
except ServerAuthError:
    print("Invalid password")
```

### Enable RCON on Minecraft Server

Edit `server.properties`:
```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_password
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [orjson](https://github.com/ijl/orjson) for fast JSON serialization
- Powered by [uvloop](https://github.com/MagicStack/uvloop) for high-performance async I/O
- Follows [Source RCON Protocol](https://developer.valvesoftware.com/wiki/Source_RCON_Protocol) specification

## Links

- **Repository**: https://github.com/Ven0m0/mc-rcon
- **Issues**: https://github.com/Ven0m0/mc-rcon/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

Made with ❤️ for the Minecraft community
