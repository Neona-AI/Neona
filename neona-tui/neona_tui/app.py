"""Main Textual application for Neona TUI."""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, DataTable
from textual.binding import Binding
from textual import on
from rich.text import Text

from .api_client import NeonaClient, NeonaAPIError, HealthResponse


class StatusBar(Static):
    """Custom status bar showing daemon status and version."""
    
    def __init__(self) -> None:
        super().__init__("")
        self.daemon_online = False
        self.version = ""
        self.holder_id = ""
    
    def update_status(
        self, 
        health: HealthResponse, 
        task_count: int = 0, 
        holder_id: str = ""
    ) -> None:
        """Update the status bar display with health info."""
        self.daemon_online = health.ok
        self.version = health.version
        self.holder_id = holder_id
        
        if health.ok:
            status_text = Text()
            status_text.append("● DAEMON ", style="bold green")
            status_text.append(f"v{health.version} ", style="dim cyan")
            status_text.append(f"| {task_count} tasks ", style="cyan")
            status_text.append(f"| DB: {health.db} ", style="dim")
            if holder_id:
                status_text.append(f"| {holder_id}", style="dim yellow")
            self.update(status_text)
        else:
            status_text = Text()
            status_text.append("○ DAEMON OFFLINE ", style="bold red")
            if health.db:
                status_text.append(f"({health.db})", style="dim red")
            self.update(status_text)


class NeonaTUI(App):
    """Neona Terminal UI - Python Edition with Rich/Textual."""
    
    CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    DataTable {
        height: 1fr;
    }
    
    Input {
        dock: bottom;
        border: round $primary;
    }
    
    #message-box {
        dock: bottom;
        height: auto;
        min-height: 1;
        max-height: 5;
        background: $panel;
        color: $success;
        padding: 0 1;
    }
    
    #help-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """
    
    TITLE = "NEONA Control Plane"
    SUB_TITLE = "Python Edition · Powered by Textual"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh"),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    def __init__(self) -> None:
        super().__init__()
        self.client = NeonaClient()
        self.tasks: list[dict] = []
        self.message = ""
        self.last_health = HealthResponse(ok=False, db="", version="", time="")
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield StatusBar()
        
        # Main content area
        yield Container(
            DataTable(id="tasks-table"),
            Static(id="help-bar"),
            Static(id="message-box"),
            Input(
                placeholder="add <title> | claim | release | run <cmd> [args] | note <text> | query <q> | refresh",
                id="command-input"
            ),
        )
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when app starts."""
        # Setup tasks table
        table = self.query_one("#tasks-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Status", "ID", "Title", "Claimed By")
        
        # Setup help bar
        help_bar = self.query_one("#help-bar", Static)
        help_text = Text()
        help_text.append("Commands: ", style="bold")
        help_text.append("add ", style="cyan")
        help_text.append("claim ", style="green")
        help_text.append("release ", style="yellow")
        help_text.append("run ", style="magenta")
        help_text.append("note ", style="blue")
        help_text.append("query ", style="white")
        help_text.append("| Keys: ", style="bold")
        help_text.append("r=refresh ", style="dim")
        help_text.append("q=quit", style="dim")
        help_bar.update(help_text)
        
        # Initial data load
        await self.refresh_tasks()
    
    async def refresh_tasks(self) -> None:
        """Fetch and display tasks from daemon."""
        status_bar = self.query_one(StatusBar)
        table = self.query_one("#tasks-table", DataTable)
        
        try:
            # Check daemon health via /health endpoint
            health = await self.client.check_health()
            self.last_health = health
            
            if not health.ok:
                status_bar.update_status(health, holder_id=self.client.holder_id)
                self.show_message("Daemon offline - start with 'neona daemon'", error=True)
                return
            
            # Fetch tasks
            task_items = await self.client.list_tasks()
            self.tasks = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "claimed_by": t.claimed_by,
                }
                for t in task_items
            ]
            status_bar.update_status(health, len(self.tasks), self.client.holder_id)
            
            # Update table
            table.clear()
            for task in self.tasks:
                status = self.format_status(task.get("status", "unknown"))
                task_id = task.get("id", "")[:8]
                title = task.get("title", "")
                claimed_by = task.get("claimed_by", "") or "-"
                table.add_row(status, task_id, title, claimed_by)
            
            self.show_message(f"Loaded {len(self.tasks)} tasks")
            
        except NeonaAPIError as e:
            status_bar.update_status(
                HealthResponse(ok=False, db="error", version="", time=""),
                holder_id=self.client.holder_id
            )
            self.show_message(f"API Error: {e}", error=True)
    
    def format_status(self, status: str) -> Text:
        """Format task status with colors."""
        status_map = {
            "pending": ("○ PENDING", "yellow"),
            "claimed": ("◐ CLAIMED", "blue"),
            "running": ("◑ RUNNING", "magenta"),
            "completed": ("● DONE", "green"),
            "failed": ("✗ FAILED", "red"),
        }
        
        text, color = status_map.get(status.lower(), (status.upper(), "white"))
        return Text(text, style=f"bold {color}")
    
    def show_message(self, msg: str, error: bool = False) -> None:
        """Display a message in the message box."""
        self.message = msg
        msg_box = self.query_one("#message-box", Static)
        style = "bold red" if error else "bold green"
        prefix = "✗ " if error else "✓ "
        msg_box.update(Text(prefix + msg, style=style))
    
    def get_selected_task(self) -> dict | None:
        """Get the currently selected task from the table."""
        table = self.query_one("#tasks-table", DataTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(self.tasks):
            return self.tasks[table.cursor_row]
        return None
    
    @on(Input.Submitted)
    async def handle_command(self, event: Input.Submitted) -> None:
        """Handle command input."""
        cmd = event.value.strip()
        event.input.value = ""
        
        if not cmd:
            return
        
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""
        
        try:
            if action == "add":
                await self.cmd_add(args_str)
            elif action in ("refresh", "r"):
                await self.refresh_tasks()
            elif action == "claim":
                await self.cmd_claim()
            elif action == "release":
                await self.cmd_release()
            elif action == "run":
                await self.cmd_run(args_str)
            elif action == "note":
                await self.cmd_note(args_str)
            elif action == "query":
                await self.cmd_query(args_str)
            else:
                self.show_message(
                    f"Unknown command: {action} (try: add, claim, release, run, note, query, refresh)",
                    error=True
                )
                
        except NeonaAPIError as e:
            self.show_message(f"Error: {e}", error=True)
    
    async def cmd_add(self, title: str) -> None:
        """Create a new task."""
        if not title:
            self.show_message("Usage: add <task title>", error=True)
            return
        
        task_id = await self.client.create_task(title)
        self.show_message(f"Created task: {task_id[:8]}")
        await self.refresh_tasks()
    
    async def cmd_claim(self) -> None:
        """Claim the selected task."""
        task = self.get_selected_task()
        if not task:
            self.show_message("No task selected - use arrow keys to select", error=True)
            return
        
        await self.client.claim_task(task["id"])
        self.show_message(f"Claimed task: {task['id'][:8]}")
        await self.refresh_tasks()
    
    async def cmd_release(self) -> None:
        """Release the selected task."""
        task = self.get_selected_task()
        if not task:
            self.show_message("No task selected - use arrow keys to select", error=True)
            return
        
        await self.client.release_task(task["id"])
        self.show_message(f"Released task: {task['id'][:8]}")
        await self.refresh_tasks()
    
    async def cmd_run(self, args_str: str) -> None:
        """Run a command on the selected task."""
        task = self.get_selected_task()
        if not task:
            self.show_message("No task selected - use arrow keys to select", error=True)
            return
        
        if not args_str:
            self.show_message("Usage: run <command> [args...]", error=True)
            return
        
        # Parse command and args
        parts = args_str.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        result = await self.client.run_task(task["id"], command, args)
        
        if result.exit_code == 0:
            self.show_message(f"Command '{command}' completed (exit=0)")
        else:
            output = result.stderr or result.stdout or f"exit code {result.exit_code}"
            self.show_message(f"Command '{command}' failed: {output}", error=True)
    
    async def cmd_note(self, content: str) -> None:
        """Add a note/memory to the selected task."""
        task = self.get_selected_task()
        if not task:
            self.show_message("No task selected - use arrow keys to select", error=True)
            return
        
        if not content:
            self.show_message("Usage: note <content>", error=True)
            return
        
        memory = await self.client.add_memory(task["id"], content)
        self.show_message(f"Added note: {memory.id[:8]}")
    
    async def cmd_query(self, query: str) -> None:
        """Query memory items."""
        if not query:
            self.show_message("Usage: query <search term>", error=True)
            return
        
        results = await self.client.query_memory(query)
        
        if not results:
            self.show_message(f"No results for '{query}'")
        else:
            # Show first few results in message box
            msg_parts = [f"Found {len(results)} result(s):"]
            for m in results[:3]:
                preview = m.content[:40] + "..." if len(m.content) > 40 else m.content
                msg_parts.append(f"  [{m.tags}] {preview}")
            self.show_message("\n".join(msg_parts))
    
    async def action_refresh(self) -> None:
        """Refresh tasks (bound to 'r' key)."""
        await self.refresh_tasks()
    
    async def on_unmount(self) -> None:
        """Called when app closes."""
        await self.client.close()


def main() -> None:
    """Entry point for neona-tui command."""
    app = NeonaTUI()
    app.run()


if __name__ == "__main__":
    main()
