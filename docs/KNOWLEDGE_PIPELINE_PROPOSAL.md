# Knowledge Pipeline Proposal: The "Local NotebookLM"

**Date:** January 19, 2026
**Status:** Draft / Research Phase
**Context:** Studio Mode - Phase 1 (Cognitive Expansion)

---

## 1. Executive Summary
We aim to upgrade the existing **Memory Daemon** (`memory_server.py`) from a passive storage bucket into a **Proactive Knowledge Engine**. This system will mirror the capabilities of Google's NotebookLM (ingestion, synthesis, citation) but with greater automation, privacy, and integration into the local development workflow.

## 2. External Landscape: NotebookLM MCP
We investigated using the "Model Context Protocol" (MCP) to bridge Studio Mode directly to Google's NotebookLM.

### Option A: `khengyun/notebooklm-mcp`
*   **Mechanism:** Uses browser automation (Chrome profile) for persistent authentication.
*   **Pros:** Stable session management, "Professional" grade, supports Docker.
*   **Cons:** Heavy dependency (requires running Chrome), strictly tied to Google's ecosystem.

### Option B: `jacob-bd/notebooklm-mcp`
*   **Mechanism:** Uses cookie extraction (`__Secure-1PSID`) and internal APIs.
*   **Pros:** Lightweight, suitable for headless scripts.
*   **Cons:** Fragile (breaks if Google changes APIs), manual cookie maintenance.

### **Recommendation**
While these tools are powerful, **building a Native Pipeline** (Option C) using our existing LanceDB + LLM stack is superior because:
1.  **Zero Latency:** No API rate limits or network hops.
2.  **Privacy:** "Company Secrets" never leave the local machine.
3.  **Integration:** We can feed "Codebase Context" directly into the research, which NotebookLM cannot easily access.

---

## 3. Proposed Architecture: The "Deep Research" Pipeline

We will extend the existing **Hub & Spoke** model with three specialized roles.

```mermaid
graph LR
    User -->|Topic: 'Rust Patterns'| Scout[Scout Agent]
    
    subgraph "Research Pipeline (.core)"
        Scout -->|1. Harvest| Librarian[The Librarian]
        Librarian -->|Web/PDF/Git| Sources[(Source Registry)]
        Librarian -->|Extract & Chunk| Vectors[(LanceDB)]
        
        Scout -->|2. Synthesize| Analyst[The Analyst]
        Analyst -->|Query (RAG)| Vectors
        Analyst -->|3. Output| Report[Briefing / FAQ / Code]
    end
```

### 3.1 Component Breakdown

#### **The Librarian (Ingestion Engine)**
*   **Responsibility:** "Clean, Catalog, and Store."
*   **New Feature:** A `sources` table in SQLite to track provenance (URL, Title, Author, Date).
*   **Capabilities:**
    *   **Web:** Scrape -> Markdown -> Chunk.
    *   **PDF:** OCR/Extract -> Chunk.
    *   **Git:** Clone -> AST Parse -> Chunk.
*   **Differentiation:** Unlike standard RAG, the Librarian maintains **Source Integrity**—you can query "Only the React Documentation" or "Only the Project Specs."

#### **The Scout (Research Agent)**
*   **Responsibility:** "Go out and find it."
*   **Workflow:**
    1.  User asks: "How do I implement AuthZ in FastAPI?"
    2.  Scout searches Google/Docs.
    3.  Scout filters for high-quality URLs.
    4.  Scout passes URLs to **The Librarian**.

#### **The Analyst (Synthesis Engine)**
*   **Responsibility:** "Make sense of it."
*   **Modes:**
    *   **"The Briefing":** Summarize 50 pages into 1 page.
    *   **"The Critic":** Compare "Source A" (Docs) vs "Source B" (Our Code).
    *   **"The Simulator":** "Pretend you are a user trying to install this."

---

## 4. New Workflows (The "Killer Apps")

### 4.1 The "Recursive Index" (Library of Libraries)
*   **Concept:** A meta-notebook that indexes *other* notebooks.
*   **Use Case:** "I remember we researched 'Vector DBs' last month. Find that analysis."
*   **Tech:** A dedicated LanceDB table for `summaries` of entire collections.

### 4.2 Automated Debrief (Session Continuity)
*   **Concept:** Never lose context between shutdowns.
*   **Action:** On system exit (`SIGINT`), the **Analyst** reads the session logs and writes a "Daily Report" to the Memory.
*   **Next Morning:** The **Conductor** reads the "Daily Report" to resume exactly where you left off.

### 4.3 Cross-Model Verification (The Peer Reviewer)
*   **Concept:** Use the Knowledge Base as a "Unit Test" for Logic.
*   **Action:**
    1.  Agent generates code.
    2.  **Analyst** grabs the "Project Standards" source.
    3.  **Analyst** performs a diff: "Does this code violate our standards?"
    4.  Only compliant code is written to disk.

---

## 5. Implementation Roadmap

### **Phase 1: Foundation (The Librarian)**
*   [ ] Update `memory_server.py` with `sources` table.
*   [ ] Add `source_id` column to LanceDB schema.
*   [ ] Create `/ingest/url` endpoint (using `trafilatura` or similar).

### **Phase 2: Automation (The Scout)**
*   [ ] Create `.core/agents/scout.md` persona.
*   [ ] Implement "Google Search" tool for the Scout.
*   [ ] Build the "Search -> Ingest" loop.

### **Phase 3: Synthesis (The Analyst)**
*   [ ] Create "Synthesis Templates" (Prompt Engineering).
*   [ ] Implement `/synthesize` endpoint (e.g., "Generate FAQ from Source X").
