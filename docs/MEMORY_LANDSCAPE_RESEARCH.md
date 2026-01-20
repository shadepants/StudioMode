# Memory Systems Landscape: A Living Research Document

**Last Updated:** January 19, 2026
**Status:** Active Research
**Context:** Studio Mode - Infrastructure Selection

This document tracks the evolving landscape of AI Memory Frameworks, filtered for relevance to our **Local-First, Multi-Agent** architecture.

---

## 1. Top-Tier Candidates (Primary Analysis)

These frameworks represent the "Best in Class" for different architectural needs.

### 🥇 Mem0 (`mem0ai/mem0`)
*   **Best For:** General Purpose "User Memory"
*   **Architecture:** Universal Memory Layer.
*   **Key Feature:** "Adaptive Personalization" (learns user preferences over time).
*   **Persistence:** Vector Stores (Qdrant, Redis) + Graph (Neo4j support in v1).
*   **Relevance to Studio:** High. The clean separation of "User," "Session," and "Agent" memory aligns with our Hub & Spoke model.
*   **Stats:** ⭐ 45k+ | 🔄 Active (Weekly)

### 🥈 Zep (`getzep/zep`)
*   **Best For:** Temporal & Graph Reasoning
*   **Architecture:** "Graphiti" (Temporal Knowledge Graph).
*   **Key Feature:** Tracks facts with `valid_at` / `invalid_at` timestamps. This is critical for preventing stale knowledge (e.g., remembering an old API key that has rotated).
*   **Persistence:** Postgres + Graph Engine.
*   **Relevance to Studio:** Medium-High. The "Temporal" aspect is superior for project history, but the stack (Postgres) is heavier than our preferred SQLite/LanceDB.
*   **Stats:** ⭐ 4k | 🔄 Active (Weekly)

### 🥉 Letta (formerly MemGPT) (`letta-ai/letta`)
*   **Best For:** Stateful, Long-Running Agents
*   **Architecture:** OS-like Memory Management (Virtual Context).
*   **Key Feature:** Explicit "Core Memory" (Bio/Notes) vs "Recall Memory" (Vector Search). Agents act like operating systems managing their own context window.
*   **Relevance to Studio:** High Concept. We should borrow the "OS" metaphor, but the full server might be overkill for a CLI tool.
*   **Stats:** ⭐ 20k+ | 🔄 Active (Weekly)

---

## 2. Specialized Tools (Niche & Utility)

### 🛠️ GPTCache (`zilliztech/GPTCache`)
*   **Role:** Semantic Caching Layer.
*   **Function:** Intercepts LLM calls; if a similar query exists in cache, returns it instantly.
*   **Impact:** Drastically reduces cost/latency for repetitive research tasks.
*   **Recommendation:** **Must Implement.** This should sit in front of the `Librarian` agent.

### 📚 LangMem (`langchain-ai/langmem`)
*   **Role:** Learning & Adaptation.
*   **Function:** Optimized specifically for extracting *patterns* from conversations, not just facts.
*   **Relevance:** Useful for the "Reviewer" agent to learn code style preferences.

---

## 3. Architecture Proposal: The "Composite Memory Stack"

Instead of choosing one, Studio Mode will implement a **Composite Stack** leveraging the best patterns from the above research.

```mermaid
graph TD
    Agent[Agent (Scout/Engineer)] -->|Query| Cache[GPTCache (Semantic Layer)]
    
    Cache -->|Hit| Agent
    Cache -->|Miss| Router[Memory Router]
    
    Router -->|Fact Retrieval| Vector[LanceDB (Mem0 Pattern)]
    Router -->|Relationship Query| Graph[LiteGraph (Zep Pattern)]
    
    subgraph "Persistence Layer"
        Vector -->|Embeddings| HDD[Local Disk]
        Graph -->|JSON/Edges| HDD
    end
```

### Action Items
1.  **Immediate:** Integrate `GPTCache` into the `.core/lib/ai_client.psm1` (or Python equivalent) to speed up repeated queries.
2.  **Short Term:** Adopt `Mem0`'s schema for separating "User" vs "Project" memory in our `memory_server.py`.
3.  **Long Term:** Investigate `Graphiti` (Zep's engine) for managing complex dependency maps in large codebases.
