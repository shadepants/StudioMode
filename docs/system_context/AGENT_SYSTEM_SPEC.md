# Agent System Specification & Architecture

**Version:** 1.0.0
**Status:** Draft
**Date:** 2026-01-13

## 1. Agent Roles & Personas

| Agent Role | Primary Objective | Toolset Access |
| :--- | :--- | :--- |
| **The Conductor** (Manager) | Orchestration, Planning, State Management | `Memory Client`, `Task Dispatcher` |
| **The Engineer** (Worker) | Code Implementation, Testing, Refactoring | `File Ops`, `Shell`, `Git` |
| **The Scout** (Researcher) | Information Retrieval, Documentation | `Web Fetch`, `Search`, `Docs Reader` |
| **The Critic** (QA/Auditor) | Validation, Security, Logic Checking | `Linter`, `Read File`, `Memory Client` |

## 2. Tool Integrations

All agents interface with the **Core System** via the `Memory Client` PowerShell module (`.core/lib/memory_client.psm1`).

*   **Standard Interface:** PowerShell Functions (`Get-MemoryHealth`, `Add-MemoryEntry`, `Search-Memory`).
*   **Execution Environment:** All agents run within the host OS shell (PowerShell/Bash) but are constrained by their prompt instructions.

## 3. Communication Protocols: "The Neurolink"

We utilize the **LanceDB Memory Daemon** as the central message bus. This avoids complex socket programming and ensures a permanent audit log of all inter-agent communication.

### The Task Lifecycle
1.  **Plan:** Conductor decomposes user request into atomic `Tasks`.
2.  **Dispatch:** Conductor writes a memory entry:
    *   `Type`: "task"
    *   `Text`: "Detailed instruction..."
    *   `Metadata`: `{ "status": "pending", "assignee": "Engineer", "priority": "P0" }`
3.  **Poll:** Agents query memory for `type="task"` where `metadata.status="pending"` AND `metadata.assignee="{MyRole}"`.
4.  **Ack:** Agent updates task metadata to `status="in_progress"`.
5.  **Resolve:** Agent completes task and writes a result entry (`Type`: "episodic").
6.  **Close:** Agent updates task metadata to `status="completed"`.

## 4. Data Schemas

### Task Object (stored in Memory Entry)
```json
{
  "text": "Refactor the authentication logic in server.py to use OAuth2.",
  "type": "task",
  "metadata": {
    "task_id": "uuid-v4",
    "parent_goal_id": "uuid-v4",
    "assignee": "engineer",
    "status": "pending",
    "created_at": 1768362000,
    "context_refs": ["/docs/auth_spec.md"]
  }
}
```

### State Object (Global System State)
Managed by the Memory Daemon's internal state machine:
*   `IDLE`: Waiting for user input.
*   `PLANNING`: Conductor is breaking down requests.
*   `EXECUTING`: Workers are performing tasks.
*   `REVIEW`: Critic is validating output.

## 5. Performance Metrics (KPIs)

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **Task Velocity** | Time from `pending` -> `completed`. | < 30s per atomic task |
| **Context Hit Rate** | Relevance score of retrieved memory vs. task needs. | > 0.75 Cosine Similarity |
| **Drift** | Deviation of final code from `ARCHITECTURE.md`. | 0% (Enforced by Critic) |
| **Safety** | Number of blocked high-risk commands. | 100% Catch Rate |
