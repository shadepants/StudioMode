# Phase 2 Plan: Multi-Agent Orchestration & The Flight Deck

**Status:** REFINED
**Date:** January 19, 2026
**Owner:** C.O.R.E. Architect (Gemini)

## 1. Executive Summary
Phase 2 transitions Studio Mode from a single-agent "Research Factory" into a collaborative **"Multi-Agent Hive."** We will implement the **Conductor/Worker** pattern where a Manager agent breaks down user intent into atomic tasks, and specialized Worker agents (Engineer, Scout) execute them asynchronously via the Memory System (The Neurolink). The UI will evolve into a full "Flight Deck" with Kanban visualization and real-time agent observability.

## 2. Objectives
1.  **The Handoff Protocol:** Implement a standardized JSON schema for tasks that includes `status`, `assignee`, `dependencies`, and `result_payload`.
2.  **Autonomous Polling:** Create a background loop script (`.core/spokes/orchestrator.ps1`) that manages agent transitions based on task completion.
3.  **Cross-Agent Memory:** Ensure Workers can read the "context" created by the Scout (Phase 1) to inform their engineering decisions.
4.  **Verification Loop:** Implement the **Critic** role to review task outputs before they are merged into the "Functional Core."

## 3. Architecture: The Hive Loop

```mermaid
graph TD
    User[User] -->|Goal| Conductor[Conductor Agent]
    Conductor -->|Task A, B, C| SQL[Task Registry (SQLite)]
    
    subgraph "The Workforce"
        SQL -->|Poll| Engineer[Engineer Agent]
        SQL -->|Poll| Scout[Scout Agent]
        
        Engineer -->|Output| SQL
        Scout -->|Output| SQL
    end
    
    SQL -->|Review| Critic[Critic Agent]
    Critic -->|Approval| User
```

## 4. Work Streams

### Stream A: The Orchestrator (PowerShell) - *[IN PROGRESS]*
*   **Goal:** A script that manages the agent "Turns."
*   **Tasks:**
    1.  [x] Create `.core/spokes/orchestrator.ps1`.
    2.  [ ] **Debug:** Fix state transition logic (Orchestrator failing to set `EXECUTING`).
    3.  [ ] Logic:
        *   While(true):
            *   Query `/tasks/list` for `status=pending`.
            *   If tasks exist, set system state to `EXECUTING`.
            *   If all tasks `completed`, set state to `REVIEW`.
            *   If `REVIEW` passes, set to `IDLE`.

### Stream B: Agent Logic Expansion
*   **Goal:** Update `engineer.md` and `worker.md` to be "Task-Aware."
*   **Tasks:**
    1.  Update system prompts to explicitly reference the `/tasks/update` endpoint.
    2.  Implement a "Task Buffer" in the UI to visualize who is working on what.

### Stream C: The Critic Agent
*   **Goal:** A specialized persona for quality control.
*   **Tasks:**
    1.  Create `.core/agents/critic.md`.
    2.  Role: Review `completed` tasks and verify against the original `plan` stored in memory.

### Stream D: The Flight Deck UX (New)
*   **Goal:** A "Human-in-the-Loop" dashboard.
*   **Tasks:**
    1.  **Kanban Board:** Enhance `TaskBoard.tsx` with columns: `Backlog`, `Hive (In Progress)`, `Review`, `Archive`.
    2.  **Live Feed:** Create `AgentFeed.tsx` to stream `episodic` memory logs (Agent thoughts/actions).
    3.  **Controls:** Add "Approve/Reject" buttons for the Review column.

## 5. Deliverables
| Artifact | Type | Description |
| :--- | :--- | :--- |
| `.core/spokes/orchestrator.ps1` | Code | The main loop for task status management. |
| `.core/agents/critic.md` | Persona | The QA agent definition. |
| `studio-governor/src/components/TaskBoard.tsx` | UI | Kanban-style view of the task registry. |
| `studio-governor/src/components/AgentFeed.tsx` | UI | Real-time log of agent activity. |

## 6. Risks
*   **Race Conditions:** Two workers picking up the same task. *Mitigation: Implement `claimed_by` field with atomic updates.* (Completed in Backend).
*   **Infinite Loops:** Conductor creating tasks that fail, leading to more tasks. *Mitigation: Recursion depth limit on Task Generation.*