# Studio Mode - System Documentation

## Overview

Studio Mode is a **multi-agent development factory** that transforms Windows into an autonomous code generation environment. It uses the "Governed HiVE" architecture to coordinate multiple AI agents for software development tasks.

## System Architecture

### Core Components

| Component        | Port | Description                                         |
| ---------------- | ---- | --------------------------------------------------- |
| Memory Server    | 8000 | Central state management, task queue, vector memory |
| Engineer Service | 8001 | Code generation via LLM                             |
| Critic Service   | 8002 | Code review and static analysis                     |
| Scout Service    | 8003 | Web research and scraping                           |
| Health Check     | 8080 | Service monitoring dashboard                        |

### Key Libraries

- **LangGraph Cortex** (`.core/lib/langgraph_cortex.py`): State machine orchestrator
- **Autonomous Agent** (`.core/lib/autonomous_agent.py`): LLM-powered task executor
- **Governor Proxy** (`.core/lib/governor.py`): Rate limiting and safety controls
- **Agent Client** (`.core/lib/agent_client.py`): CLI polling interface

### Spokes (Background Workers)

- **Engineer Worker** (`.core/spokes/engineer_worker.py`): Autonomous task implementation
- **Librarian** (`.core/spokes/librarian.py`): File monitoring and ingestion
- **Orchestrator** (`.core/spokes/orchestrator.ps1`): Heartbeat and state management

---

## State Machine

The Governed HiVE operates on a cyclic state machine:

```
IDLE → EXECUTING (Engineer) → REVIEW (Critic) → IDLE
```

### States

| State     | Description              |
| --------- | ------------------------ |
| IDLE      | Waiting for tasks        |
| EXECUTING | Engineer generating code |
| REVIEW    | Critic evaluating output |

---

## API Reference

### Memory Server Endpoints

#### Tasks
| Endpoint        | Method | Description                             |
| --------------- | ------ | --------------------------------------- |
| `/tasks/create` | POST   | Create a new task                       |
| `/tasks/list`   | GET    | List tasks (filter by status, assignee) |
| `/tasks/claim`  | POST   | Claim a task for execution              |
| `/tasks/update` | POST   | Update task status/metadata             |

#### Agents
| Endpoint                 | Method | Description             |
| ------------------------ | ------ | ----------------------- |
| `/agents/register`       | POST   | Register an agent       |
| `/agents/{id}/next`      | GET    | Get and claim next task |
| `/agents/{id}/tasks`     | GET    | List agent's tasks      |
| `/agents/heartbeat/{id}` | POST   | Send heartbeat          |

#### Memory
| Endpoint        | Method | Description          |
| --------------- | ------ | -------------------- |
| `/memory/add`   | POST   | Add to vector memory |
| `/memory/query` | POST   | Semantic search      |

#### State
| Endpoint        | Method | Description              |
| --------------- | ------ | ------------------------ |
| `/state`        | GET    | Get current system state |
| `/state/update` | POST   | Transition state         |

---

## CLI Tools

### Hive CLI

```powershell
python .core/cli/hive_cli.py <command>

Commands:
  status      Get Hive status
  start       Start the Hive (IDLE → EXECUTING)
  stop        Stop the Hive (→ IDLE)
  add-task    Add a task (-t TEXT -a ASSIGNEE -p PRIORITY)
  list-tasks  List tasks (-s STATUS -a ASSIGNEE)
```

### Agent Client

```powershell
python .core/lib/agent_client.py <command>

Commands:
  poll        Start polling for tasks
  list        Show pending tasks
  complete    Mark task complete
  register    Register agent
```

### Autonomous Agent

```powershell
$env:GROQ_API_KEY = "your-key"
python .core/lib/autonomous_agent.py --agent-id NAME --model MODEL

Options:
  --agent-id    Unique identifier (default: gemini-cli)
  --model       LiteLLM model string (default: groq/llama-3.1-8b-instant)
```

---

## Configuration

### Environment Variables

| Variable               | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| `GROQ_API_KEY`         | Groq API key for LLM access                           |
| `MEMORY_SERVER_URL`    | Memory Server URL (default: http://127.0.0.1:8000)    |
| `ENGINEER_SERVICE_URL` | Engineer Service URL (default: http://127.0.0.1:8001) |

### Files

| File                      | Description               |
| ------------------------- | ------------------------- |
| `.core/memory/tasks.db`   | SQLite task database      |
| `.core/memory/lancedb/`   | LanceDB vector storage    |
| `workspace/agent_output/` | Generated agent outputs   |
| `workspace/incoming/`     | Librarian ingestion queue |

---

## Agent Personas

Agent behavior is defined in `.core/agents/`:

- **architect.md**: System design and planning
- **critic.md**: Code review and quality
- **engineer.md**: Code implementation
- **manager.md**: Task coordination
- **worker.md**: General execution

---

## Troubleshooting

### Memory Server Won't Start
```powershell
# Check port availability
netstat -ano | findstr :8000

# Kill existing process
taskkill /F /PID <PID>
```

### Agent Not Claiming Tasks
1. Verify Memory Server is running
2. Check task assignee matches agent ID
3. Confirm GROQ_API_KEY is set

### Tests Failing
```powershell
# Run with verbose output
pytest tests/ -v --tb=long

# Run specific test
pytest tests/test_critic_service.py -v
```

---

## Version History

| Version | Date       | Changes                                        |
| ------- | ---------- | ---------------------------------------------- |
| v2.1.0  | 2026-01-20 | Multi-agent delegation, Hive CLI, Health Check |
| v2.0.0  | 2026-01-19 | Governed HiVE architecture                     |
| v1.0.0  | 2026-01-18 | Initial SmartCortex backend                    |
