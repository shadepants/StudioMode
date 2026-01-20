# Memory Systems Research & Performance Standards

**Date:** January 16, 2026
**Context:** Studio Mode - Phase 0 (The Governor & Context Engine)
**Objective:** Select and benchmark a "Hippocampus" solution for the Agentic System.

---

## 1. Candidate Systems Analysis

We evaluated four open-source memory management systems for suitability in a local, multi-agent environment ("Studio Mode").

### 1.1 Mem0 (`mem0ai/mem0`)
*   **Architecture:** Multi-level memory (User/Session/Agent) backed by Vector Stores (Qdrant, Redis, etc.) + Graph variants (Mem0g).
*   **Token Efficiency:** **High**. Uses Retrieval-Augmented Generation (RAG) to inject only relevant memories, claiming ~90% token reduction vs. full context.
*   **Pros:**
    *   Strong SDK support (Python/Node).
    *   Self-hostable via Docker/Python.
    *   "Graph Memory" (Mem0g) excels at temporal reasoning.
*   **Cons:** Default configuration often relies on external LLMs (OpenAI) for extraction.

### 1.2 Zep (`getzep/zep`)
*   **Architecture:** Temporal Knowledge Graph (Graphiti). Stores "Episodes" and summarizes them over time.
*   **Token Efficiency:** **Very High**. Uses pre-summarized context blocks and relationship-aware retrieval.
*   **Pros:**
    *   **Latency:** Claims sub-200ms retrieval (faster than Mem0 in some benchmarks).
    *   **Context:** excellent at maintaining "long-term" narrative cohesion (Temporal Graph).
*   **Cons:** Open-source version (Community Edition) is sometimes lagging behind the Cloud offering; specific Python/uv requirements.

### 1.3 OpenMemory (`CaviraOSS/OpenMemory`)
*   **Architecture:** Hierarchical (Episodic/Semantic/Procedural) storage. "Not just a Vector DB."
*   **Token Efficiency:** Uses "Composite Scoring" (Salience + Recency + Coactivation) to decay old memories.
*   **Pros:**
    *   **Local-First:** Explicitly designed for privacy and self-hosting.
    *   **Cognitive Model:** Mimics human memory structures better than simple RAG.
*   **Cons:** High architectural complexity; fewer public benchmarks.

### 1.4 ReMe (`agentscope-ai/ReMe`)
*   **Architecture:** Modular (Personal/Task/Working Memory).
*   **Token Efficiency:** Explicit "Message Offload/Reload" mechanisms to manage context window budgets.
*   **Pros:** Good for "Task-oriented" agents.
*   **Cons:** Less mature ecosystem than Mem0/Zep.

---

## 2. Recommendation

**Primary Candidate: Mem0 (or its patterns applied to our LanceDB backbone)**
*   *Reason:* Best balance of developer ergonomics (SDK), performance (75ms latency with reranking), and documentation. Its "Graph" approach aligns with our need for a "System Digital Twin."

**Alternative:** **Zep** if strict temporal reasoning (understanding *when* something happened) becomes a blocker.

---

## 3. Performance Standards & Benchmarking Plan

To ensure the selected system meets "Studio Mode" requirements, we will implement the following **Measurable & Repeatable Benchmarks**.

### 3.1 Key Metrics
| Metric | Definition | Target Budget |
| :--- | :--- | :--- |
| **Ingestion Latency** | Time to index a new `episodic` fact (e.g., "User created file X"). | < 200ms (p95) |
| **Retrieval Latency** | Time to fetch context for a query (e.g., "What is the auth schema?"). | < 100ms (p95) |
| **Token Efficiency** | % reduction in prompt size vs. raw history. | > 85% Reduction |
| **Recall Accuracy** | % of relevant facts retrieved for a "Gold Set" of queries. | > 90% (Hit Rate) |
| **Throughput** | Max concurrent read/write operations per second. | > 50 ops/sec |

### 3.2 Automated Test Suite (`tests/benchmark_memory.py`)
We will create a standardized test harness that runs against the local Memory Daemon.

**Test Scenarios:**
1.  **"The Firehose" (Ingestion):**
    *   Inject 1,000 synthetic logs/facts in rapid succession.
    *   *Measure:* Write Latency, CPU Usage, RAM Spike.
2.  **"The Needle in a Haystack" (Retrieval):**
    *   Inject 10,000 distractor facts and 1 target fact.
    *   Query for the target.
    *   *Measure:* Read Latency, Accuracy (Did it find it?).
3.  **"The Long Haul" (Stability):**
    *   Continuous read/write cycle for 1 hour.
    *   *Measure:* Memory Leakage (RAM usage delta).

### 3.3 CI/CD Integration
*   **Trigger:** On every PR affecting `.core/services/memory_server.py`.
*   **Action:** Run `benchmark_memory.py --mode=ci`.
*   **Regression Guard:** Fail build if Latency > Budget OR Accuracy < 90%.
*   **Reporting:** Generate a `benchmark_report.json` artifact tracking historical trends.

### 3.4 Historical Tracking
*   Store benchmark results in a local SQLite file (`.core/logs/benchmarks.db`).
*   Visualize trends (Latency vs. Commit) in the Governor Dashboard (future feature).

