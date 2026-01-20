#!/usr/bin/env python3
"""
Gemini CLI Agent Client
========================
Polling client for Gemini CLI to participate in collaborative workflows.
Run this in the background while using Gemini CLI to auto-receive tasks.

Usage:
  python agent_client.py --agent-id gemini-cli --poll-interval 5
"""

import argparse
import json
import time
import sys
import os
from typing import Optional, Dict, Any

import httpx

# --- CONFIGURATION ---
DEFAULT_SERVER = os.getenv("MEMORY_SERVER_URL", "http://127.0.0.1:8000")
DEFAULT_AGENT_ID = "gemini-cli"
DEFAULT_POLL_INTERVAL = 10  # seconds


class AgentClient:
    """Client for participating in multi-agent workflows."""
    
    def __init__(self, server_url: str, agent_id: str, agent_type: str = "gemini-cli"):
        self.server_url = server_url
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.client = httpx.Client(timeout=30.0)
        self.registered = False
    
    def register(self, capabilities: list = None) -> bool:
        """Register this agent with the Memory Server."""
        try:
            resp = self.client.post(
                f"{self.server_url}/agents/register",
                json={
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "capabilities": capabilities or ["code", "research", "analysis"]
                }
            )
            resp.raise_for_status()
            self.registered = True
            print(f"✅ Registered as '{self.agent_id}'")
            return True
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """Send heartbeat to show agent is still active."""
        try:
            resp = self.client.post(f"{self.server_url}/agents/heartbeat/{self.agent_id}")
            return resp.status_code == 200
        except:
            return False
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Poll for the next available task."""
        try:
            resp = self.client.get(f"{self.server_url}/agents/{self.agent_id}/next")
            resp.raise_for_status()
            data = resp.json()
            return data.get("task")
        except Exception as e:
            print(f"Poll error: {e}")
            return None
    
    def get_pending_tasks(self) -> list:
        """Get all pending tasks without claiming."""
        try:
            resp = self.client.get(
                f"{self.server_url}/tasks/list",
                params={"status": "pending", "assignee": self.agent_id}
            )
            return resp.json().get("tasks", [])
        except:
            return []
    
    def complete_task(self, task_id: str, result: str = "") -> bool:
        """Mark a task as completed."""
        try:
            resp = self.client.post(
                f"{self.server_url}/tasks/update",
                json={
                    "task_id": task_id,
                    "status": "completed",
                    "metadata": {"result": result}
                }
            )
            return resp.status_code == 200
        except:
            return False
    
    def submit_for_review(self, task_id: str, output_path: str = "") -> bool:
        """Submit task for review."""
        try:
            resp = self.client.post(
                f"{self.server_url}/tasks/update",
                json={
                    "task_id": task_id,
                    "status": "review",
                    "metadata": {"output_path": output_path}
                }
            )
            return resp.status_code == 200
        except:
            return False


def format_task(task: dict) -> str:
    """Format task for display."""
    if not task:
        return "No task"
    
    metadata = json.loads(task.get("metadata", "{}"))
    lines = [
        f"📋 Task: {task['text']}",
        f"   ID: {task['id'][:8]}...",
        f"   Priority: {task['priority']}",
    ]
    if metadata.get("description"):
        lines.append(f"   Description: {metadata['description']}")
    if metadata.get("workflow_id"):
        lines.append(f"   Workflow: {metadata['workflow_id']}")
    return "\n".join(lines)


def run_polling_loop(client: AgentClient, interval: int, interactive: bool = True):
    """Main polling loop."""
    print(f"\n🔄 Polling for tasks every {interval}s...")
    print("   Press Ctrl+C to stop\n")
    
    last_task_id = None
    
    while True:
        try:
            # Send heartbeat
            client.heartbeat()
            
            # Check for tasks
            task = client.get_next_task()
            
            if task and task["id"] != last_task_id:
                last_task_id = task["id"]
                print("\n" + "="*60)
                print("📬 NEW TASK RECEIVED!")
                print("="*60)
                print(format_task(task))
                print("="*60)
                
                if interactive:
                    print("\n💡 Complete this task, then run:")
                    print(f'   python agent_client.py complete {task["id"][:8]}')
                    print(f'   OR: python agent_client.py review {task["id"][:8]}')
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopping agent client...")
            break


def main():
    parser = argparse.ArgumentParser(description="Gemini CLI Agent Client")
    parser.add_argument("command", nargs="?", default="poll",
                        choices=["poll", "list", "complete", "review", "register"],
                        help="Command to run")
    parser.add_argument("task_id", nargs="?", help="Task ID for complete/review commands")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID, help="Agent identifier")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Memory Server URL")
    parser.add_argument("--interval", type=int, default=DEFAULT_POLL_INTERVAL, help="Poll interval (seconds)")
    parser.add_argument("--result", default="", help="Result message for complete command")
    
    args = parser.parse_args()
    
    client = AgentClient(args.server, args.agent_id)
    
    if args.command == "register":
        client.register()
        
    elif args.command == "poll":
        if not client.register():
            sys.exit(1)
        run_polling_loop(client, args.interval)
        
    elif args.command == "list":
        tasks = client.get_pending_tasks()
        if tasks:
            print(f"📋 Pending tasks for '{args.agent_id}':\n")
            for task in tasks:
                print(format_task(task))
                print()
        else:
            print("No pending tasks.")
            
    elif args.command == "complete":
        if not args.task_id:
            print("Error: task_id required for complete command")
            sys.exit(1)
        # Find full task ID from prefix
        tasks = client.get_pending_tasks()
        full_id = next((t["id"] for t in tasks if t["id"].startswith(args.task_id)), None)
        if full_id:
            if client.complete_task(full_id, args.result):
                print(f"✅ Task {args.task_id} marked complete!")
            else:
                print(f"❌ Failed to complete task")
        else:
            print(f"Task not found: {args.task_id}")
            
    elif args.command == "review":
        if not args.task_id:
            print("Error: task_id required for review command")
            sys.exit(1)
        tasks = client.get_pending_tasks()
        full_id = next((t["id"] for t in tasks if t["id"].startswith(args.task_id)), None)
        if full_id:
            if client.submit_for_review(full_id):
                print(f"📤 Task {args.task_id} submitted for review!")
            else:
                print(f"❌ Failed to submit for review")
        else:
            print(f"Task not found: {args.task_id}")


if __name__ == "__main__":
    main()
