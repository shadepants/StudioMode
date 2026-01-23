# System Overview: Studio Mode

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

| State     | Description              |
| --------- | ------------------------ |
| IDLE      | Waiting for tasks        |
| EXECUTING | Engineer generating code |
| REVIEW    | Critic evaluating output |

---

## Agent Personas

Detailed persona definitions can be found in [AGENT_PERSONAS.md](AGENT_PERSONAS.md).

- **Architect**: System design and planning
- **Critic**: Code review and quality
- **Engineer**: Code implementation
- **Manager**: Task coordination
- **Worker**: General execution
