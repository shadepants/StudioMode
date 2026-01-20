# C.O.R.E. v4.2 Strategy Session: Meeting Minutes & Synthesis

**Date:** January 19, 2026
**Topic:** Studio Mode Evolution & The Research Factory
**Participants:** User (Architect) & Gemini (Senior Systems Architect)

---

## 1. Session Objective
To define the architecture for a "Multi-Agent Research Factory" capable of autonomous data ingestion, synthesis, and actionable intelligence generation, evolving the existing "Studio Mode" into a production-grade system ("C.O.R.E. v4.2").

---

## 2. Narrative Arc & Thought Paths

### Path A: The "NotebookLM Integration" Exploration
*   **Initial Query:** How to connect Gemini CLI to NotebookLM for research.
*   **Discovery:** Identified two MCP server options:
    *   `khengyun/notebooklm-mcp` (Browser-based/Stable - **Selected**).
    *   `jacob-bd/notebooklm-mcp` (API-based/Fragile).
*   **Outcome:** Successfully installed the `notebooklm` skill, authenticated via browser, and ingested 5 key notebooks into the local library.

### Path B: The "Memory System" Deep Dive
*   **Challenge:** Moving beyond simple RAG to a "Knowledge Engine."
*   **Research:** Evaluated Mem0, Zep, and OpenMemory.
*   **Key Insight:** We need a "Composite Stack":
    *   **LanceDB:** For long-term vector storage (The Hippocampus).
    *   **GPTCache:** For semantic caching (The Reflex).
    *   **Graph/Ontology:** For structured relationships (The Cortex).
*   **Action:** Updated `memory_server.py` to include tables for `sources`, `ontology`, `datasets`, and `semantic_cache`.

### Path C: The "Factory" Vision (Macro Goal)
*   **User Vision:** A factory that takes a "Topic" and outputs "Curated Datasets, Ontologies, and Actionable Intelligence."
*   **Architecture:** Defined the supply chain:
    1.  **Scout:** Harvest data (Web/GitHub).
    2.  **Librarian:** Ingest & Ground (NotebookLM).
    3.  **Architect:** Structure (Ontology/Graph).
    4.  **Engineer:** Build (Code/Apps).
*   **Consensus:** The system must be **Local-First**, **Transparent**, and **Automated**.

### Path D: The "Governor" Dashboard
*   **Asset Discovery:** Found `studio-governor`, an existing React/WebContainer prototype.
*   **Pivot:** Decided to repurpose this as the "Factory Control Room" to monitor agent activity and Tier 3 Anchors (Objective, Constraints, State).

---

## 3. Key Decisions & Architectural Anchors

| Decision | Context | Status |
| :--- | :--- | :--- |
| **Hybrid Memory Stack** | Use LanceDB (Vectors) + SQLite (Ontology) + GPTCache (Speed). | **Implemented in Backend** |
| **Identity** | The system is "C.O.R.E. v4.2" - A peer-level collaborator, not a chatbot. | **Defined in Persona** |
| **Ingestion Strategy** | Use NotebookLM as the "Grounding Layer" before mirroring to local DB. | **Validated** |
| **Governance** | Strict "Human-Parity" constraints (no magic APIs, readable typing speeds). | **Documented** |

---

## 4. Current State Snapshot

### The Asset Inventory
1.  **Codebase:** `StudioMode` repo with `.core` framework.
2.  **Memory Daemon:** `memory_server.py` updated with Factory Schema.
3.  **Research Corpus (Ingested):**
    *   *The Integration Axis* (Psych Ontology)
    *   *The HiVE Orchestrator* (Coding Agent Spec)
    *   *Human-Parity AI Studio* (Governance Spec)
    *   *The AI Agent Handbook* (Business Use Cases)
    *   *Design Systems Compendium* (UI/UX)
4.  **Frontend:** `studio-governor` (Ready for connection).

---

## 5. Next Steps (The "Path Forward")

1.  **Final Specification:** Draft `docs/STUDIO_BLUEPRINT.md` to formally encode the "C.O.R.E. v4.2" architecture.
2.  **Bridge Building:** Create the "Sidecar Script" to automatically mirror NotebookLM insights into the local LanceDB.
3.  **Dashboard Integration:** Connect the `studio-governor` UI to the `memory_server.py` Factory API.
