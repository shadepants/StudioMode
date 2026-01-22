"""
Hive CLI Tool
=============
Command-line interface for managing the Governed Hive.

Usage:
    python -m .core.cli.hive_cli start
    python -m .core.cli.hive_cli stop
    python -m .core.cli.hive_cli status
    python -m .core.cli.hive_cli add-task --text "Your task" --assignee "agent-id"
    python -m .core.cli.hive_cli list-tasks
"""

import argparse
import sys
import os
import httpx

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from .core.config import MEMORY_SERVER_URL


def start(args):
    """Start the Governed Hive services."""
    print("Starting Governed Hive...")
    try:
        r = httpx.post(f"{MEMORY_SERVER_URL}/state/update", json={"new_state": "EXECUTING"})
        if r.status_code == 200:
            print("✅ Governed Hive started successfully!")
        else:
            print(f"❌ Failed to start: {r.text}")
    except httpx.ConnectError:
        print("❌ Memory Server not running. Start it first with:")
        print("   python .core/services/memory_server.py")


def stop(args):
    """Stop the Governed Hive services."""
    print("Stopping Governed Hive...")
    try:
        r = httpx.post(f"{MEMORY_SERVER_URL}/state/update", json={"new_state": "IDLE"})
        if r.status_code == 200:
            print("✅ Governed Hive stopped successfully!")
        else:
            print(f"❌ Failed to stop: {r.text}")
    except httpx.ConnectError:
        print("❌ Memory Server not reachable.")


def status(args):
    """Query the status of the Governed Hive."""
    try:
        r = httpx.get(f"{MEMORY_SERVER_URL}/state")
        if r.status_code == 200:
            state = r.json().get("current_state", "UNKNOWN")
            print(f"🔹 Governed Hive Status: {state}")
        else:
            print(f"❌ Failed to get status: {r.text}")
    except httpx.ConnectError:
        print("❌ Memory Server not running.")


def add_task(args):
    """Add a new task to the Governed Hive."""
    try:
        payload = {
            "text": args.text,
            "assignee": args.assignee,
            "priority": args.priority
        }
        r = httpx.post(f"{MEMORY_SERVER_URL}/tasks/create", json=payload)
        if r.status_code == 200:
            task_id = r.json().get("task_id")
            print(f"✅ Task added successfully! ID: {task_id}")
        else:
            print(f"❌ Failed to add task: {r.text}")
    except httpx.ConnectError:
        print("❌ Memory Server not running.")


def list_tasks(args):
    """List all tasks in the Governed Hive."""
    try:
        params = {}
        if args.status:
            params["status"] = args.status
        if args.assignee:
            params["assignee"] = args.assignee
        
        r = httpx.get(f"{MEMORY_SERVER_URL}/tasks/list", params=params)
        if r.status_code == 200:
            tasks = r.json().get("tasks", [])
            if not tasks:
                print("📭 No tasks found.")
                return
            
            print(f"📋 Found {len(tasks)} task(s):\n")
            for t in tasks:
                status_icon = "🟢" if t["status"] == "completed" else "🟡" if t["status"] == "in_progress" else "⚪"
                print(f"  {status_icon} [{t['id'][:8]}...] {t['text'][:50]}...")
                print(f"     Assignee: {t.get('assignee', 'unassigned')} | Status: {t['status']}")
                print()
        else:
            print(f"❌ Failed to list tasks: {r.text}")
    except httpx.ConnectError:
        print("❌ Memory Server not running.")


def main():
    parser = argparse.ArgumentParser(
        description="Hive CLI - Manage the Governed Hive",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the Governed Hive")
    start_parser.set_defaults(func=start)

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the Governed Hive")
    stop_parser.set_defaults(func=stop)

    # Status command
    status_parser = subparsers.add_parser("status", help="Get Hive status")
    status_parser.set_defaults(func=status)

    # Add-task command
    add_task_parser = subparsers.add_parser("add-task", help="Add a new task")
    add_task_parser.add_argument("--text", "-t", required=True, help="Task description")
    add_task_parser.add_argument("--assignee", "-a", default="gemini-cli", help="Agent to assign")
    add_task_parser.add_argument("--priority", "-p", default="normal", choices=["low", "normal", "high"])
    add_task_parser.set_defaults(func=add_task)

    # List-tasks command
    list_tasks_parser = subparsers.add_parser("list-tasks", help="List all tasks")
    list_tasks_parser.add_argument("--status", "-s", help="Filter by status")
    list_tasks_parser.add_argument("--assignee", "-a", help="Filter by assignee")
    list_tasks_parser.set_defaults(func=list_tasks)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
