# SYSTEM SPECIFICATION: The Governed HiVE Architecture

**Version:** 2.1.0 (HITL Enhanced)
**Status:** APPROVED FOR IMPLEMENTATION
**Objective:** Transform Studio Mode into a deterministic, observable, and measurable Agentic Factory with mandatory Human-in-the-Loop (HITL) governance.

---

## 1. Modular Architecture Breakdown

The system is decoupled into three distinct modules with strict interfaces.

### Module A: The Spine (Autonomic Infrastructure)
*   **Role:** The stable, deterministic foundation handling I/O and state persistence.
*   **Components:**
    1.  **Librarian Service (`librarian.py`):**
        *   *Function:* Watchdog for `workspace/incoming`. Auto-ingests files to LanceDB.
        *   *Interface:* Emits `SIGNAL_FILE_INGESTED` to the Message Bus.
    2.  **Memory Server (`memory_server.py`):**
        *   *Function:* CRUD interface for Vector DB (LanceDB) and SQL Metadata.
        *   *Interface:* HTTP API (`POST /query`, `POST /add`).
    3.  **MCP Host:**
        *   *Function:* Standardized bridge for external tools (Browser, Filesystem).
*   **Measurable Success:**
    *   Librarian detects and indexes a 5MB text file in < 2 seconds.
    *   Memory Server returns semantic search results in < 200ms.

### Module B: The Cortex (Cognitive State Machine)
*   **Role:** The reasoning engine executing the "HiVE Cycle." It is **NOT** a linear script; it is a Graph.
*   **State Nodes:**
    1.  **MAPPER:** Queries GraphRAG to identify dependency trees and "blast radius."
    2.  **ARCHITECT:** Generates `spec.md` (Requirements) and `plan.md` (Implementation Steps).
    3.  **ENGINEER:** Generates code/artifacts based *strictly* on `plan.md`.
    4.  **CRITIC:** Validates output against the Constitution and RepoReason metrics.
*   **Interface:** Receives `Goal` from Governor; Returns `Artifacts` or `Error`.
*   **Measurable Success:**
    *   Graph transitions are logged explicitly (e.g., `State: PLANNING -> State: WAITING_FOR_USER`).
    *   No code is generated without a preceding, user-approved `plan.md` artifact.

### Module C: The Governor (Safety & HITL Middleware)
*   **Role:** The active proxy and "Superego" ensuring safety and human alignment.
*   **Functions:**
    1.  **Throttling:** Buffers output tokens to 40-60 WPM (Human Reading Speed).
    2.  **Interception:** Blocks execution of high-risk commands (`DenyList`) pending explicit user confirmation.
    3.  **Approval Interface:** Presents "Go/No-Go" gates to the user at critical transitions.
*   **Measurable Success:**
    *   Critical decisions (Deploy, Delete) trigger a confirmation prompt 100% of the time.
    *   User feedback loops are integrated into the context before the next attempt.

---

## 2. The HiVE Execution Cycle (Logic Pathway with HITL)

This defines the rigorous loop the Cortex must follow. **User Confirmation is a mandatory state transition.**

### Phase 1: Context & Mapping
1.  **Action:** Cortex activates **MAPPER** node.
2.  **Check:** Does the request implicate >5 files (High DFI)?
    *   *Yes:* **[STOP]** Request task decomposition from User.
    *   *No:* Proceed to Phase 2.

### Phase 2: Planning & Specification
1.  **Action:** Cortex activates **ARCHITECT** node.
2.  **Output:** `spec.md` and `plan.md` saved to `workspace/_meta/`.
3.  **[GATE] USER REVIEW:**
    *   **System State:** PAUSED.
    *   **User Action:** Review `plan.md`. Options: `APPROVE`, `REFINE (with feedback)`, `REJECT`.
    *   **Transition:** Only proceed to Phase 3 upon `APPROVE`.

### Phase 3: Construction
1.  **Action:** Cortex activates **ENGINEER** node.
2.  **Input:** Approved `plan.md` + Mapped Context.
3.  **Output:** Code files in `workspace/draft/`.

### Phase 4: Verification & Final Sign-off
1.  **Action:** Cortex activates **CRITIC** node.
2.  **Evaluation:** Applies **RepoReason Metrics**.
3.  **Decision:**
    *   *Fail:* Loop back to Phase 3 (Auto-Refine) up to 3 times.
    *   *Pass:* **[GATE] FINAL APPROVAL**.
4.  **[GATE] FINAL APPROVAL:**
    *   **System State:** PAUSED.
    *   **User Action:** Review Diff / Critic Report. Options: `MERGE`, `RETRY`.
    *   **Transition:** Upon `MERGE`, commit to `workspace/src/`.

---

## 3. Measurable Quality Metrics (RepoReason)

The Critic Agent must utilize these metrics for objective verification.

| Metric | Full Name | Definition | Threshold (Fail) |
| :--- | :--- | :--- | :--- |
| **ESV** | Effective Sliced Volume | The number of lines of code the agent must read to understand the context. | **> 2,000 LOC** (Context Overload) |
| **MCL** | Mutation Chain Length | The number of sequential changes required to reach the goal state. | **> 5 Steps** (State Drift) |
| **DFI** | Dependency Fan-in | The number of external files/modules that impact the current task. | **> 5 Dependencies** (Cognitive Crush) |

---

## 4. Modular Implementation Pathway

### Step 1: Solidify the Spine
*   **Task:** Wrap `librarian.py` and `memory_server.py` into a unified `SpineService`.
*   **Verify:** Services run as daemons; API endpoints are responsive.

### Step 2: Build the Governor Prototype (HITL Focus)
*   **Task:** Create `governor.py` proxy. Implement the `ask_user_permission(action)` function.
*   **Action:** Define the `CriticalActionList` (e.g., file writes, network calls).
*   **Verify:** Script pauses and waits for 'y' input before executing a mock delete command.

### Step 3: Implement the Cortex State Machine
*   **Task:** Refactor `Orchestrator.ps1` to use a switch-based State Machine.
*   **Action:** Add `WAITING_FOR_USER` state.
*   **Verify:** Orchestrator creates `plan.md` and explicitly stops, asking for user review.

### Step 4: Integration
*   **Task:** Connect Governor -> Cortex -> Spine.
*   **Action:** Execute a full "Plan -> Review -> Code -> Verify" cycle.
*   **Verify:** User is prompted twice (Plan Review, Final Merge); all metrics are logged.
