# Neona TUI (Python Edition)

A beautiful, rich terminal interface for Neona built with [Textual](https://textual.textualize.io/) and [Rich](https://rich.readthedocs.io/).

## Features

✨ **Rich Visuals** - Beautiful colors, animations, and responsive layout  
🎨 **Modern UI** - Data tables, status bars, and interactive widgets  
⚡ **Fast** - Async HTTP client for smooth daemon communication  
🔌 **Standalone** - Works alongside the Go daemon via HTTP API

## Installation

### From Source

```bash
cd neona-tui
pip install -e .
```

### Requirements

- Python 3.9+
- Neona daemon running on `localhost:7466`

## Usage

```bash
# Start the Python TUI
neona-tui

# Or run directly
python -m neona_tui.app
```

### Commands

| Command | Description |
|---------|-------------|
| `add <title>` | Create a new task |
| `claim` | Claim selected task (requires selection) |
| `release` | Release selected task (must be owner) |
| `run <cmd> [args]` | Run command on claimed task |
| `note <text>` | Add a memory note to selected task |
| `query <q>` | Search memory items |
| `refresh` or `r` | Refresh task list |
| `q` | Quit |

### API Endpoints Used

The TUI client communicates with the Go daemon via these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Daemon health check (version, DB status) |
| `/tasks` | GET/POST | List or create tasks |
| `/tasks/{id}` | GET | Get task details |
| `/tasks/{id}/claim` | POST | Claim task (requires `holder_id`, `ttl_sec`) |
| `/tasks/{id}/release` | POST | Release task (requires `holder_id`) |
| `/tasks/{id}/run` | POST | Run command (requires `holder_id`, `command`, `args`) |
| `/tasks/{id}/logs` | GET | Get task run logs |
| `/tasks/{id}/memory` | GET | Get task memory items |
| `/memory` | POST | Add memory item |
| `/memory?q=...` | GET | Query memory |
| `/workers` | GET | Worker pool stats |

### Keyboard Shortcuts

- `↑/↓` - Navigate tasks
- `r` - Refresh
- `q` or `Ctrl+C` - Quit

## Architecture

```
┌──────────────┐         ┌─────────────┐
│  neona-tui   │  HTTP   │   neona     │
│  (Python)    │ ◄─────► │  (daemon)   │
└──────────────┘         └─────────────┘
   Textual UI          localhost:7466
```

The Python TUI is a **client** that communicates with the Go daemon via HTTP API. This keeps the core engine in Go while providing a richer UI experience.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run in dev mode with live reload
textual run --dev neona_tui/app.py
```

## Comparison with Go TUI

| Feature | Go TUI | Python TUI |
|---------|--------|------------|
| Dependencies | None (static binary) | Python 3.9+ required |
| Visual Polish | Good (Bubbletea) | Excellent (Textual) |
| Animations | Limited | Rich support |
| Startup Time | ~10ms | ~200ms |
| Memory | ~5MB | ~30MB |

## License

AGPL v3 - Same as Neona core
