"""HTTP API client for Neona daemon.

Mirrors the Go TUI client (internal/tui/client.go) for API compatibility.
"""

import socket
import httpx
from dataclasses import dataclass
from typing import Any, Optional


class NeonaAPIError(Exception):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, body: str = ""):
        self.message = message
        self.status_code = status_code
        self.body = body
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.body:
            return f"{self.message}: {self.body}"
        return self.message


@dataclass
class HealthResponse:
    """Response from /health endpoint."""
    ok: bool
    db: str
    version: str
    time: str


@dataclass
class TaskItem:
    """Task item from list."""
    id: str
    title: str
    status: str
    claimed_by: str


@dataclass
class TaskDetail:
    """Detailed task info."""
    id: str
    title: str
    description: str
    status: str
    claimed_by: str
    created_at: str
    updated_at: str


@dataclass
class RunDetail:
    """Run/log entry for a task."""
    id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str


@dataclass
class MemoryDetail:
    """Memory item."""
    id: str
    content: str
    tags: str
    task_id: str = ""


@dataclass
class WorkersStats:
    """Worker pool statistics."""
    active_workers: int
    global_max: int
    connector_counts: dict[str, int]
    workers: list[dict[str, Any]]


class NeonaClient:
    """Async HTTP client for Neona daemon API.
    
    Mirrors the Go TUI client contract for full compatibility.
    """
    
    DEFAULT_TIMEOUT = 10.0
    DEFAULT_TTL_SEC = 300  # 5 minutes, same as Go
    
    def __init__(self, base_url: str = "http://127.0.0.1:7466"):
        """Initialize client with base URL.
        
        Args:
            base_url: Base URL of Neona daemon (default: http://127.0.0.1:7466)
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=self.DEFAULT_TIMEOUT)
        # Generate holder_id same as Go TUI: "tui@<hostname>"
        self.holder_id = f"tui@{socket.gethostname()}"
    
    async def check_health(self) -> HealthResponse:
        """Check daemon health via /health endpoint.
        
        Returns:
            HealthResponse with ok, db, version, time
            
        Raises:
            NeonaAPIError: If request fails
        """
        try:
            response = await self.client.get("/health")
            if response.status_code >= 400:
                return HealthResponse(ok=False, db="unreachable", version="", time="")
            
            data = response.json()
            return HealthResponse(
                ok=data.get("ok", False),
                db=data.get("db", "unknown"),
                version=data.get("version", "unknown"),
                time=data.get("time", ""),
            )
        except httpx.RequestError:
            return HealthResponse(ok=False, db="unreachable", version="", time="")
    
    async def is_healthy(self) -> bool:
        """Simple health check returning bool.
        
        Returns:
            True if daemon is online and healthy
        """
        health = await self.check_health()
        return health.ok
    
    async def list_tasks(self, status_filter: str = "") -> list[TaskItem]:
        """List all tasks, optionally filtered by status.
        
        Args:
            status_filter: Filter by status (pending, claimed, running, completed, failed)
            
        Returns:
            List of TaskItem objects
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            params = {"status": status_filter} if status_filter else {}
            response = await self.client.get("/tasks", params=params)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError("Failed to list tasks", response.status_code, body)
            
            data = response.json()
            return [
                TaskItem(
                    id=t.get("id", ""),
                    title=t.get("title", ""),
                    status=t.get("status", ""),
                    claimed_by=t.get("claimed_by", ""),
                )
                for t in data
            ]
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to list tasks: {e}")
    
    async def get_task(self, task_id: str) -> TaskDetail:
        """Get details for a specific task.
        
        Args:
            task_id: Task ID
            
        Returns:
            TaskDetail object
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            response = await self.client.get(f"/tasks/{task_id}")
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to get task {task_id}", response.status_code, body)
            
            t = response.json()
            return TaskDetail(
                id=t.get("id", ""),
                title=t.get("title", ""),
                description=t.get("description", ""),
                status=t.get("status", ""),
                claimed_by=t.get("claimed_by", ""),
                created_at=t.get("created_at", ""),
                updated_at=t.get("updated_at", ""),
            )
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to get task {task_id}: {e}")
    
    async def create_task(self, title: str, description: str = "") -> str:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description (optional)
            
        Returns:
            Created task ID
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            payload = {"title": title, "description": description}
            response = await self.client.post("/tasks", json=payload)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError("Failed to create task", response.status_code, body)
            
            data = response.json()
            return data.get("id", "")
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to create task: {e}")
    
    async def claim_task(self, task_id: str, ttl_sec: int = DEFAULT_TTL_SEC) -> dict[str, Any]:
        """Claim a task.
        
        Args:
            task_id: Task ID to claim
            ttl_sec: Lease TTL in seconds (default: 300)
            
        Returns:
            Lease info from daemon
            
        Raises:
            NeonaAPIError: If API request fails (e.g., already claimed)
        """
        try:
            payload = {
                "holder_id": self.holder_id,
                "ttl_sec": ttl_sec,
            }
            response = await self.client.post(f"/tasks/{task_id}/claim", json=payload)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to claim task {task_id}", response.status_code, body)
            
            return response.json()
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to claim task {task_id}: {e}")
    
    async def release_task(self, task_id: str) -> None:
        """Release a claimed task.
        
        Args:
            task_id: Task ID to release
            
        Raises:
            NeonaAPIError: If API request fails (e.g., not owner)
        """
        try:
            payload = {"holder_id": self.holder_id}
            response = await self.client.post(f"/tasks/{task_id}/release", json=payload)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to release task {task_id}", response.status_code, body)
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to release task {task_id}: {e}")
    
    async def run_task(self, task_id: str, command: str, args: Optional[list[str]] = None) -> RunDetail:
        """Run a command for a claimed task.
        
        Args:
            task_id: Task ID
            command: Command to run
            args: Command arguments (optional)
            
        Returns:
            RunDetail with exit code, stdout, stderr
            
        Raises:
            NeonaAPIError: If API request fails (e.g., not owner, not allowed)
        """
        try:
            payload = {
                "holder_id": self.holder_id,
                "command": command,
                "args": args or [],
            }
            response = await self.client.post(f"/tasks/{task_id}/run", json=payload)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to run command on task {task_id}", response.status_code, body)
            
            r = response.json()
            return RunDetail(
                id=r.get("id", ""),
                command=r.get("command", command),
                exit_code=r.get("exit_code", -1),
                stdout=r.get("stdout", ""),
                stderr=r.get("stderr", ""),
            )
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to run command on task {task_id}: {e}")
    
    async def get_task_logs(self, task_id: str) -> list[RunDetail]:
        """Get run logs for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of RunDetail objects
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            response = await self.client.get(f"/tasks/{task_id}/logs")
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to get logs for task {task_id}", response.status_code, body)
            
            data = response.json()
            return [
                RunDetail(
                    id=r.get("id", ""),
                    command=r.get("command", ""),
                    exit_code=r.get("exit_code", -1),
                    stdout=r.get("stdout", ""),
                    stderr=r.get("stderr", ""),
                )
                for r in data
            ]
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to get logs for task {task_id}: {e}")
    
    async def get_task_memory(self, task_id: str) -> list[MemoryDetail]:
        """Get memory items for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of MemoryDetail objects
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            response = await self.client.get(f"/tasks/{task_id}/memory")
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError(f"Failed to get memory for task {task_id}", response.status_code, body)
            
            data = response.json()
            return [
                MemoryDetail(
                    id=m.get("id", ""),
                    content=m.get("content", ""),
                    tags=m.get("tags", ""),
                    task_id=m.get("task_id", task_id),
                )
                for m in data
            ]
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to get memory for task {task_id}: {e}")
    
    async def add_memory(self, task_id: str, content: str, tags: str = "note") -> MemoryDetail:
        """Add a memory item (note) for a task.
        
        Args:
            task_id: Task ID
            content: Memory content
            tags: Tags for the memory (default: "note")
            
        Returns:
            Created MemoryDetail
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            payload = {
                "task_id": task_id,
                "content": content,
                "tags": tags,
            }
            response = await self.client.post("/memory", json=payload)
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError("Failed to add memory", response.status_code, body)
            
            m = response.json()
            return MemoryDetail(
                id=m.get("id", ""),
                content=m.get("content", content),
                tags=m.get("tags", tags),
                task_id=m.get("task_id", task_id),
            )
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to add memory: {e}")
    
    async def query_memory(self, query: str) -> list[MemoryDetail]:
        """Search memory items.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching MemoryDetail objects
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            response = await self.client.get("/memory", params={"q": query})
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError("Failed to query memory", response.status_code, body)
            
            data = response.json()
            return [
                MemoryDetail(
                    id=m.get("id", ""),
                    content=m.get("content", ""),
                    tags=m.get("tags", ""),
                    task_id=m.get("task_id", ""),
                )
                for m in data
            ]
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to query memory: {e}")
    
    async def get_workers(self) -> WorkersStats:
        """Get worker pool statistics.
        
        Returns:
            WorkersStats object
            
        Raises:
            NeonaAPIError: If API request fails
        """
        try:
            response = await self.client.get("/workers")
            
            if response.status_code >= 400:
                body = response.text
                raise NeonaAPIError("Failed to get workers", response.status_code, body)
            
            data = response.json()
            return WorkersStats(
                active_workers=data.get("active_workers", 0),
                global_max=data.get("global_max", 0),
                connector_counts=data.get("connector_counts", {}),
                workers=data.get("workers", []),
            )
        except httpx.RequestError as e:
            raise NeonaAPIError(f"Failed to get workers: {e}")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
