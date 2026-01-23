import asyncio
import time
import socket
import os
import sys
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Add .core directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from lib.memory_client import AsyncMemoryClient
except ImportError:
    try:
        from ..lib.memory_client import AsyncMemoryClient
    except ImportError:
         # Fallback if run from different context
         from .core.lib.memory_client import AsyncMemoryClient

class BaseAgentService(ABC):
    """
    Abstract base class for autonomous agent services in Studio Mode.
    
    Provides standardized lifecycle management for agents including:
    - Automatic registration with Memory Server
    - Background heartbeat to maintain online status
    - Task polling loop to fetch and process assigned work
    
    Subclasses must implement the `process_task()` method.
    
    Example:
        class MyAgent(BaseAgentService):
            async def process_task(self, task: dict):
                # Handle the task
                await self.update_task(task['id'], 'DONE')
        
        agent = MyAgent("my-agent", "worker", ["code", "review"])
        asyncio.run(agent.start())
    """
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str] = [], memory_url: str = None):
        """
        Initialize the agent service.
        
        Args:
            agent_id: Unique identifier for this agent instance (e.g., "engineer-1")
            agent_type: Category of agent (e.g., "engineer", "critic", "scout")
            capabilities: List of task types this agent can handle (e.g., ["code", "review"])
            memory_url: Optional custom Memory Server URL. Defaults to http://127.0.0.1:8000
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.client = AsyncMemoryClient(base_url=memory_url) if memory_url else AsyncMemoryClient()
        self.running = False
        self._task_queue = asyncio.Queue()

    async def start(self):
        """Start the service loops."""
        print(f"[*] Starting {self.agent_id} ({self.agent_type})...")
        self.running = True
        
        # 1. Register
        await self.client.register(self.agent_id, self.agent_type, self.capabilities)
        
        # 2. Start Heartbeat Loop
        asyncio.create_task(self._heartbeat_loop())
        
        # 3. Start Task Polling Loop
        asyncio.create_task(self._poll_loop())
        
        # 4. Keep alive or serve specific logic (can be overridden or awaited)
        while self.running:
            await asyncio.sleep(1.0)

    async def stop(self):
        """Stop the service."""
        print(f"[*] Stopping {self.agent_id}...")
        self.running = False
        await self.client.close()

    async def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds."""
        while self.running:
            try:
                await self.client.heartbeat(self.agent_id)
            except Exception as e:
                print(f"[!] Heartbeat failed: {e}")
            await asyncio.sleep(30)

    async def _poll_loop(self):
        """Poll for next task."""
        while self.running:
            try:
                task = await self.client.get_next_task(self.agent_id)
                if task:
                    print(f"[{self.agent_id}] Processing task: {task['id']}")
                    await self.process_task(task)
                else:
                    await asyncio.sleep(5) # Idle poll interval
            except Exception as e:
                print(f"[!] Poll error: {e}")
                await asyncio.sleep(5)

    @abstractmethod
    async def process_task(self, task: Dict[str, Any]):
        """Implement specific task processing logic."""
        pass

    async def update_task(self, task_id: str, status: str, metadata: Dict = None):
        """Helper to update task status."""
        await self.client.update_task(task_id, status, metadata)
