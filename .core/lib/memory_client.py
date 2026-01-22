"""
Memory Server Client
====================
Unified client for interacting with the Central Memory Server.
Supports Agent Registration, Task Management, and Memory Operations.
"""

import httpx
from typing import Optional, Dict, Any, List
from ..config import MEMORY_SERVER_URL

class AsyncMemoryClient:
    """Async HTTP client for the Memory Server."""
    
    def __init__(self, base_url: str = MEMORY_SERVER_URL, timeout: float = 30.0):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def register(self, agent_id: str, agent_type: str, capabilities: List[str]) -> bool:
        """Register agent capabilities."""
        try:
            resp = await self.client.post(
                f"{self.base_url}/agents/register",
                json={
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "capabilities": capabilities
                }
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[MemoryClient] Registration failed: {e}")
            return False

    async def heartbeat(self, agent_id: str) -> bool:
        """Send heartbeat."""
        try:
            resp = await self.client.post(f"{self.base_url}/agents/heartbeat/{agent_id}")
            return resp.status_code == 200
        except:
            return False

    async def get_next_task(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Poll for next task assigned to agent."""
        try:
            resp = await self.client.get(f"{self.base_url}/agents/{agent_id}/next")
            resp.raise_for_status()
            return resp.json().get("task")
        except:
            return None

    async def update_task(self, task_id: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """Update task status."""
        try:
            await self.client.post(
                f"{self.base_url}/tasks/update",
                json={
                    "task_id": task_id,
                    "status": status,
                    "metadata": metadata or {}
                }
            )
            return True
        except Exception as e:
            print(f"[MemoryClient] Task update failed: {e}")
            return False

    async def add_memory(self, text: str, mem_type: str = "episodic", metadata: Dict[str, Any] = None) -> bool:
        """Add memory entry."""
        try:
            await self.client.post(
                f"{self.base_url}/memory/add",
                json={
                    "text": text,
                    "type": mem_type,
                    "metadata": metadata or {}
                }
            )
            return True
        except:
            return False

    async def read_file(self, path: str) -> Optional[str]:
        """Read file content via FS API."""
        try:
            resp = await self.client.get(f"{self.base_url}/fs/read", params={"path": path})
            if resp.status_code == 200:
                return resp.json().get("content")
        except:
            pass
        return None

    async def write_file(self, path: str, content: str) -> bool:
        """Write file content via FS API."""
        try:
            resp = await self.client.post(
                f"{self.base_url}/fs/write",
                json={"path": path, "content": content}
            )
            return resp.status_code == 200
        except:
            return False

    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        try:
            resp = await self.client.get(f"{self.base_url}/tasks/list")
            if resp.status_code == 200:
                return resp.json().get("tasks", [])
        except:
            pass
        return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
