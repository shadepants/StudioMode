# Studio Mode: Technical Manual & System Architecture

**Version:** 1.0.0
**Date:** January 13, 2026
**System Status:** Production Ready

---

## 1. Executive Summary

**Studio Mode** is a "Multi-Agent Development Factory" designed to transform a standard Windows environment into an autonomous software engineering pipeline. Unlike traditional RAG (Retrieval-Augmented Generation) systems, Studio Mode utilizes a **"System Digital Twin"** (Context Engineering) and a **Memory Daemon** (LanceDB) to provide agents with real-time, grounded awareness of the OS, toolchain, and project topology.

The system operates on the **Hub & Spoke** model, where a central "Conductor" agent orchestrates specialized "Worker" agents (Engineer, Scout, Critic) via a persistent memory bus known as the **Neurolink**.

---

## 2. High-Level Architecture

```mermaid
graph TD
    User[User / Architect] -->|Directs| Conductor[Conductor Agent]
    
    subgraph "Core System (.core)"
        Conductor -->|Plan| Neurolink[Memory Daemon (LanceDB)]
        Neurolink -->|Task Context| Engineer[Engineer Agent]
        Neurolink -->|Research Context| Scout[Scout Agent]
        
        Engineer -->|Code Changes| FS[File System]
        Scout -->|Web Data| FS
        
        FS -->|Auto-Sync| Neurolink
    end
    
    subgraph "Context Layers"
        L0[L0: Substrate]
        L1[L1: Toolchain]
        L2[L2: Services]
        L3[L3: Topology]
    end
    
    Neurolink -.->|Indexes| L0
    Neurolink -.->|Indexes| L1
    Neurolink -.->|Indexes| L2
    Neurolink -.->|Indexes| L3
```

---

## 3. Core Components

### 3.1 The Memory Daemon (Service)
*   **Location:** `.core/services/memory_server.py`
*   **Stack:** Python 3.12, FastAPI, LanceDB, Sentence-Transformers.
*   **Role:** The "Hippocampus" of the system. It handles:
    *   **Vector Storage:** Embeds text using `all-MiniLM-L6-v2`.
    *   **State Machine:** Tracks global agent state (`IDLE`, `PLANNING`, `EXECUTING`, `REVIEW`).
    *   **Auto-Sync:** Watches `docs/system_context/*.md` and keeps the vector DB updated with the latest system state.

### 3.2 The Neurolink (Protocol)
*   **Location:** `.core/lib/memory_client.psm1`
*   **Interface:** PowerShell REST Client.
*   **Mechanism:** Asynchronous message passing via the database.
*   **Object Types:**
    *   `episodic`: A record of past actions or user facts.
    *   `knowledge`: Static documentation synced from Markdown.
    *   `task`: An executable unit of work with status tracking.

### 3.3 The Context Engine (Data)
*   **Location:** `docs/system_context/`
*   **Strategy:** "Digital Twin" snapshotting.
*   **Layers:**
    *   **Layer 0 (Substrate):** Hardware, OS Version, Resources.
    *   **Layer 1 (Toolchain):** Installed Languages, Compilers, Package Managers.
    *   **Layer 2 (Services):** Active Ports, Docker Containers, Background Daemons.
    *   **Layer 3 (Topology):** Project directories, "Hotspots", Stack Definitions.

---

## 4. Agent Workflows

### 4.1 The "Plan -> Dispatch -> Execute" Loop

1.  **Inception:**
    *   User inputs a high-level goal (e.g., "Refactor the auth service").
    *   **Conductor** loads `system_context` to understand the current auth implementation.
    *   **Conductor** transitions State to `PLANNING`.

2.  **Decomposition:**
    *   **Conductor** breaks the goal into atomic `Tasks`:
        *   *Task A:* "Create `auth_new.py` interface."
        *   *Task B:* "Update `server.py` to use new interface."
    *   **Conductor** writes these tasks to Memory (`status: pending`).

3.  **Dispatch:**
    *   **Conductor** transitions State to `EXECUTING`.
    *   **Engineer** polls Memory for pending tasks.
    *   **Engineer** marks Task A as `in_progress`.

4.  **Execution & Convergence:**
    *   **Engineer** writes the code.
    *   **Engineer** marks Task A as `completed` and logs the result (`type: episodic`).
    *   **Critic** (Optional) reviews the result against the spec.

5.  **Completion:**
    *   Once all tasks are complete, **Conductor** transitions State to `REVIEW` or `IDLE`.

---

## 5. Data Schemas

### 5.1 Memory Entry
```python
class MemoryEntry(BaseModel):
    id: str           # SHA256 Hash
    text: str         # The content (chunked)
    vector: Vector    # 384-dim embedding
    type: str         # "episodic" | "knowledge" | "task"
    metadata: str     # JSON string
    timestamp: float
```

### 5.2 Task Metadata (JSON)
```json
{
    "task_id": "uuid",
    "assignee": "Engineer",
    "status": "pending",
    "priority": "high",
    "dependencies": []
}
```

---

## 6. Installation & Maintenance

### 6.1 Bootstrapping
Run the bootloader script to verify dependencies and start the daemon:
```powershell
.core/Conductor.ps1
```

### 6.2 Adding Knowledge
Simply create or edit any Markdown file in `docs/system_context/`. The Memory Daemon will detect the change (on next sync cycle) and update the vector index automatically.

### 6.3 Extending Personas
Edit `.core/agents/manager.md` or `.core/agents/worker.md` to change the system prompts and behavioral constraints of the agents.
