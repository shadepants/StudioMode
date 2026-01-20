# Phase 1 Implementation Plan: The Flight Deck & Librarian

**Status:** APPROVED
**Date:** January 19, 2026
**Owner:** C.O.R.E. Architect
**Context:** Studio Mode > Phase 1

## 1. Executive Summary
Phase 1 focuses on connecting the **Studio Governor** (UI) to the **Memory Daemon** (Backend). We will transform the isolated "Safety Kernel" into a live "Flight Deck" that visualizes the C.O.R.E. v4.2 Factory pipeline. Simultaneously, we will implement the **Librarian** as a "File Watcher" service to bridge the gap between external research (NotebookLM exports) and our local Vector DB.

## 2. Architecture: The "Control Room" Pattern

```mermaid
graph TD
    User[User] -->|Interacts| UI[Studio Governor (React)]
    
    subgraph "The Flight Deck (Frontend)"
        UI -->|Polls| Status[ Research Status API]
        UI -->|Reads| FS[Mirror Filesystem]
    end
    
    subgraph "The Engine Room (Backend)"
        Status -->|Managed By| Mem[memory_server.py]
        Mem -->|Stores| LDB[LanceDB (Vectors)]
        Mem -->|Stores| SQL[SQLite (Ontology)]
        
        Lib[Librarian Script] -->|Watches| Drop[./workspace/incoming]
        Lib -->|Ingests| Mem
    end
```

## 3. Work Streams

### Stream A: The Memory API Upgrade (Backend)
*   **Goal:** Expose the "Research Factory" state to the UI.
*   **Tasks:**
    1.  **Enhance `memory_server.py`:**
        *   Add `GET /sources`: List ingested research materials.
        *   Add `GET /ontology`: Return the current Knowledge Graph (Nodes/Edges).
        *   Implement `POST /research/scout`: A clearer endpoint to trigger a research job.
    2.  **Stub the Scout:** Replace the mock `asyncio.sleep` with a "Stub" that creates a dummy source entry in SQLite, proving the database write works.

### Stream B: The Librarian (Ingestion Service)
*   **Goal:** Safe ingestion of research without complex MCP dependencies for now.
*   **Mechanism:** "The Drop Box"
    *   Create directory `workspace/incoming`.
    *   Create script `.core/spokes/librarian.py`.
    *   **Logic:** Watch `workspace/incoming/*.{md,txt,pdf}`. When a file appears:
        1.  Read content.
        2.  Generate Checksum.
        3.  Call `POST /memory/add` (Vector) and Insert into `sources` (SQLite).
        4.  Move file to `workspace/processed/`.

### Stream C: The Studio Governor (Frontend)
*   **Goal:** Visualize the system state.
*   **Tasks:**
    1.  **Dashboard:** Replace the static "Activity Log" with a **"Factory Pipeline"** view (Progress bars for Scout/Ingest/Synthesize).
    2.  **Knowledge View:** A new tab to render the "Ontology Graph" (using `react-force-graph` or simple lists initially).
    3.  **Connectivity:** Switch `FileExplorer` to use the live `http://localhost:8000/fs` endpoints instead of just local mocks (if applicable) or verify the existing hook.

## 4. Execution Steps (The "Script")

1.  **Setup:**
    *   Create `workspace/incoming` and `workspace/processed`.
2.  **Backend:**
    *   Edit `.core/services/memory_server.py` to add `GET /sources`.
3.  **Librarian:**
    *   Write `.core/spokes/librarian.py` (Python `watchdog` library).
4.  **Frontend:**
    *   Install `lucide-react` (already there) and `swr` (for data fetching).
    *   Create `src/components/FactoryMonitor.tsx`.
    *   Update `src/App.tsx` to include the Monitor.
5.  **Verify:**
    *   Drop a text file into `incoming/`.
    *   Watch it disappear.
    *   See it appear in the `sources` table via the UI.

## 5. Risk Assessment (Red Team)
*   **Risk:** `memory_server.py` and `studio-governor` running on different ports (8000 vs 5173) causes CORS issues.
    *   *Mitigation:* `memory_server.py` already has `CORSMiddleware` allowing `*`.
*   **Risk:** File Watching conflicts if the user saves a file while Librarian is reading.
    *   *Mitigation:* Use a "rename to .lock" or "wait for write completion" logic in `librarian.py`.
*   **Risk:** UI complexity.
    *   *Mitigation:* Start with a simple JSON dump or Table view before building a complex Graph visualization.

## 6. Success Criteria
*   [ ] User can drop a file in `workspace/incoming`.
*   [ ] System automatically ingests it into LanceDB.
*   [ ] Governor UI shows the new "Source" in a list.
*   [ ] "Research Status" shows "Idle" or "Active".
