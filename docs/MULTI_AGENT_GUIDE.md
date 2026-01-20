# Multi-Agent Collaboration Guide for Gemini CLI

This document explains how to participate in collaborative workflows with Antigravity IDE.

## Quick Start

### 1. Start the Memory Server (if not running)
```powershell
cd C:\Users\User\Repositories\StudioMode
python .core/services/memory_server.py
```

### 2. Register and Start Polling
```powershell
python .core/lib/agent_client.py poll --agent-id gemini-cli
```

This will:
- Register you as an agent
- Poll for tasks every 10 seconds
- Print tasks when they arrive

### 3. When You Receive a Task
1. Read the task description
2. Complete the work in the Gemini CLI
3. Mark complete: `python .core/lib/agent_client.py complete <task-id>`

## Available Commands

| Command         | Description                         |
| --------------- | ----------------------------------- |
| `poll`          | Start polling for tasks (default)   |
| `list`          | Show pending tasks without claiming |
| `complete <id>` | Mark a task as completed            |
| `review <id>`   | Submit task for review              |
| `register`      | Register agent without polling      |

## API Endpoints

If you prefer to interact directly with the Memory Server:

| Endpoint             | Method | Description             |
| -------------------- | ------ | ----------------------- |
| `/agents/register`   | POST   | Register agent          |
| `/agents/{id}/next`  | GET    | Get and claim next task |
| `/agents/{id}/tasks` | GET    | List all assigned tasks |
| `/tasks/update`      | POST   | Update task status      |

## Workflow Example

1. **Antigravity creates a workflow:**
   ```
   POST /workflows/create
   {
     "workflow_id": "feature-impl",
     "name": "Implement New Feature",
     "tasks": [
       {"name": "Research", "assignee": "gemini-cli", "priority": "high"},
       {"name": "Implement", "assignee": "antigravity", "priority": "normal"}
     ]
   }
   ```

2. **Gemini CLI receives Research task** via polling

3. **Complete and hand off** to next task in workflow
