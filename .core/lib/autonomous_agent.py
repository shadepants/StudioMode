#!/usr/bin/env python3
"""
Autonomous Agent Executor for Studio Mode
==========================================
Polls for tasks and autonomously executes them using an LLM.
Captures output, handles errors/timeouts, and sends notifications.

Usage:
  python autonomous_agent.py --agent-id gemini-cli --poll-interval 10
  python autonomous_agent.py --agent-id gemini-cli --model gpt-4o-mini
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

import httpx

# LiteLLM for multi-model support
try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    print("[!] litellm not installed. Install with: pip install litellm")

# --- CONFIGURATION ---
MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "http://127.0.0.1:8000")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))  # seconds
OUTPUT_DIR = "./workspace/agent_output"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REVIEW = "review"


@dataclass
class ExecutionResult:
    """Result of task execution."""
    task_id: str
    status: TaskStatus
    output: str
    error: Optional[str] = None
    duration_seconds: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    output_path: Optional[str] = None


@dataclass
class Notification:
    """Notification for task events."""
    timestamp: str
    event: str  # completed, failed, timeout, started
    task_id: str
    task_name: str
    message: str
    details: Dict[str, Any] = None


class AutonomousAgent:
    """
    Autonomous agent that polls for tasks and executes them via LLM.
    """
    
    def __init__(
        self,
        agent_id: str,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        server_url: str = MEMORY_SERVER_URL
    ):
        self.agent_id = agent_id
        self.model = model
        self.timeout = timeout
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.notifications: List[Notification] = []
        self.running = False
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async def register(self) -> bool:
        """Register agent with Memory Server."""
        try:
            resp = await self.client.post(
                f"{self.server_url}/agents/register",
                json={
                    "agent_id": self.agent_id,
                    "agent_type": "autonomous",
                    "capabilities": ["code", "research", "analysis", "autonomous"]
                }
            )
            resp.raise_for_status()
            self._notify("registered", "", "Agent Registration", f"Agent '{self.agent_id}' registered successfully")
            return True
        except Exception as e:
            print(f"[ERR] Registration failed: {e}")
            return False
    
    async def heartbeat(self) -> bool:
        """Send heartbeat to server."""
        try:
            resp = await self.client.post(f"{self.server_url}/agents/heartbeat/{self.agent_id}")
            return resp.status_code == 200
        except:
            return False
    
    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Poll for next available task."""
        try:
            resp = await self.client.get(f"{self.server_url}/agents/{self.agent_id}/next")
            resp.raise_for_status()
            data = resp.json()
            return data.get("task")
        except Exception as e:
            return None
    
    async def update_task(self, task_id: str, status: str, metadata: Dict = None) -> bool:
        """Update task status."""
        try:
            resp = await self.client.post(
                f"{self.server_url}/tasks/update",
                json={
                    "task_id": task_id,
                    "status": status,
                    "metadata": metadata or {}
                }
            )
            return resp.status_code == 200
        except:
            return False
    
    async def add_memory(self, text: str, mem_type: str = "episodic", metadata: Dict = None) -> bool:
        """Add entry to Memory Server."""
        try:
            resp = await self.client.post(
                f"{self.server_url}/memory/add",
                json={"text": text, "type": mem_type, "metadata": metadata or {}}
            )
            return resp.status_code == 200
        except:
            return False
    
    def _notify(self, event: str, task_id: str, task_name: str, message: str, details: Dict = None):
        """Create and store a notification."""
        notification = Notification(
            timestamp=datetime.utcnow().isoformat(),
            event=event,
            task_id=task_id,
            task_name=task_name,
            message=message,
            details=details or {}
        )
        self.notifications.append(notification)
        
        # Print to console with text indicators (Windows compatible)
        icons = {
            "started": "[>>]",
            "completed": "[OK]",
            "failed": "[ERR]",
            "timeout": "[TIME]",
            "registered": "[REG]"
        }
        icon = icons.get(event, "[*]")
        print(f"\n{icon} [{event.upper()}] {message}")
        if details:
            for k, v in details.items():
                print(f"   {k}: {v}")
    
    async def execute_task(self, task: Dict[str, Any]) -> ExecutionResult:
        """Execute a task using the LLM."""
        task_id = task["id"]
        task_text = task["text"]
        metadata = json.loads(task.get("metadata", "{}"))
        description = metadata.get("description", "")
        
        self._notify(
            "started", task_id, task_text,
            f"Starting task: {task_text[:50]}...",
            {"model": self.model, "timeout": f"{self.timeout}s"}
        )
        
        start_time = time.time()
        
        # Build prompt
        system_prompt = f"""You are an autonomous AI agent named '{self.agent_id}'.
Your task is to complete the following work item thoroughly and professionally.

Guidelines:
1. Be thorough but concise
2. If the task requires code, write complete, working code
3. If the task requires research, provide sources and summaries
4. Structure your output clearly with headers and sections
5. If you cannot complete the task, explain why clearly"""

        user_prompt = f"""## Task
{task_text}

## Description
{description if description else 'No additional description provided.'}

## Instructions
Complete this task to the best of your ability. Provide a complete, actionable response."""

        try:
            if not HAS_LITELLM:
                raise RuntimeError("litellm not installed")
            
            # Execute with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    litellm.completion,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=4000
                ),
                timeout=self.timeout
            )
            
            output = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            duration = time.time() - start_time
            
            # Save output to file
            output_path = os.path.join(OUTPUT_DIR, f"{task_id[:8]}_{int(time.time())}.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Task: {task_text}\n\n")
                f.write(f"**Agent:** {self.agent_id}\n")
                f.write(f"**Model:** {self.model}\n")
                f.write(f"**Duration:** {duration:.2f}s\n")
                f.write(f"**Tokens:** {tokens}\n\n")
                f.write("---\n\n")
                f.write(output)
            
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                output=output,
                duration_seconds=duration,
                model_used=self.model,
                tokens_used=tokens,
                output_path=output_path
            )
            
            self._notify(
                "completed", task_id, task_text,
                f"Task completed: {task_text[:50]}...",
                {"duration": f"{duration:.2f}s", "tokens": tokens, "output": output_path}
            )
            
            return result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.TIMEOUT,
                output="",
                error=f"Task timed out after {self.timeout} seconds",
                duration_seconds=duration,
                model_used=self.model
            )
            
            self._notify(
                "timeout", task_id, task_text,
                f"Task timed out: {task_text[:50]}...",
                {"timeout": f"{self.timeout}s", "elapsed": f"{duration:.2f}s"}
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            result = ExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                output="",
                error=error_msg,
                duration_seconds=duration,
                model_used=self.model
            )
            
            self._notify(
                "failed", task_id, task_text,
                f"Task failed: {task_text[:50]}...",
                {"error": error_msg[:200], "duration": f"{duration:.2f}s"}
            )
            
            return result
    
    async def process_task(self, task: Dict[str, Any]) -> ExecutionResult:
        """Process a single task end-to-end."""
        task_id = task["id"]
        
        # Execute
        result = await self.execute_task(task)
        
        # Update task status in Memory Server
        status_map = {
            TaskStatus.COMPLETED: "completed",
            TaskStatus.FAILED: "failed",
            TaskStatus.TIMEOUT: "failed"
        }
        
        await self.update_task(
            task_id,
            status_map.get(result.status, "failed"),
            metadata={
                "output_path": result.output_path,
                "duration": result.duration_seconds,
                "model": result.model_used,
                "tokens": result.tokens_used,
                "error": result.error
            }
        )
        
        # Log to memory
        await self.add_memory(
            f"Agent '{self.agent_id}' {result.status.value} task: {task['text'][:50]}...",
            mem_type="episodic",
            metadata={"task_id": task_id, "status": result.status.value}
        )
        
        return result
    
    async def run_loop(self, poll_interval: int = 10, max_tasks: int = 0):
        """
        Main autonomous execution loop.
        
        Args:
            poll_interval: Seconds between polls
            max_tasks: Maximum tasks to process (0 = unlimited)
        """
        self.running = True
        tasks_processed = 0
        
        print(f"\n[AGENT] Autonomous Agent '{self.agent_id}' Starting...")
        print(f"   Model: {self.model}")
        print(f"   Timeout: {self.timeout}s")
        print(f"   Poll Interval: {poll_interval}s")
        print(f"   Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                # Heartbeat
                await self.heartbeat()
                
                # Poll for task
                task = await self.get_next_task()
                
                if task:
                    # Process the task
                    result = await self.process_task(task)
                    tasks_processed += 1
                    
                    if max_tasks > 0 and tasks_processed >= max_tasks:
                        print(f"\n[DONE] Processed {tasks_processed} tasks. Stopping.")
                        break
                else:
                    # No task available
                    print(f"[...] Polling... ({datetime.now().strftime('%H:%M:%S')})", end="\r")
                
                await asyncio.sleep(poll_interval)
                
            except KeyboardInterrupt:
                print("\n\n[BYE] Stopping autonomous agent...")
                break
            except Exception as e:
                print(f"\n[ERR] Loop error: {e}")
                await asyncio.sleep(poll_interval)
        
        self.running = False
        print(f"\n[SUMMARY] Session Summary: Processed {tasks_processed} tasks")
    
    async def close(self):
        """Cleanup resources."""
        await self.client.aclose()


async def main():
    parser = argparse.ArgumentParser(description="Autonomous Agent Executor")
    parser.add_argument("--agent-id", default="autonomous-agent", help="Agent identifier")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model to use")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Task timeout (seconds)")
    parser.add_argument("--poll-interval", type=int, default=10, help="Poll interval (seconds)")
    parser.add_argument("--max-tasks", type=int, default=0, help="Max tasks (0=unlimited)")
    parser.add_argument("--server", default=MEMORY_SERVER_URL, help="Memory Server URL")
    
    args = parser.parse_args()
    
    agent = AutonomousAgent(
        agent_id=args.agent_id,
        model=args.model,
        timeout=args.timeout,
        server_url=args.server
    )
    
    try:
        if not await agent.register():
            print("Failed to register. Is the Memory Server running?")
            sys.exit(1)
        
        await agent.run_loop(
            poll_interval=args.poll_interval,
            max_tasks=args.max_tasks
        )
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
