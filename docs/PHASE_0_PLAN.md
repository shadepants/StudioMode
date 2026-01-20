# Phase 0 Plan: The Governor & Context Engine

**Status:** APPROVED
**Date:** January 13, 2026
**Owner:** C.O.R.E. Architect (Gemini)

## 1. Executive Summary
Phase 0 initiates the **"Studio Mode"** transformation. We focus on the **Safety Kernel** (The Governor) and the **Memory Hippocampus** (Context Engine). The goal is to prove that an LLM can safely execute shell commands in a browser sandbox (WebContainer) under strict state supervision.

## 2. Objectives
1.  **Context Grounding:** Complete the L0-L3 System Digital Twin to ensure agents know *where* they are.
2.  **Infrastructure Proof:** Verify `WebContainers` can boot and execute `jsh` (JavaScript Shell) commands in the user's browser environment.
3.  **Logic Core:** Implement an **Agentic Graph (LangGraph JS)** to manage Agent/System flow (`IDLE` -> `PLANNING` -> `EXECUTING`) and state persistence.
4.  **Traffic Control:** Build the **Throttler** to manage the impedance mismatch between fast LLM tokens and slow system I/O.

## 3. Scope
*   **In Scope:**
    *   Automated System Context Discovery (Scripts).
    *   "Governor" Prototype (React + WebContainer).
    *   Streaming JSON Parser implementation.
    *   **Logic:** LangGraph JS for ReAct Loop (Nodes/Edges).
*   **Out of Scope:**
    *   Full "Flight Deck" UI (Phase 1).
    *   Multi-Agent Orchestration (Phase 2).
    *   Git Persistence (Phase 1).
    *   Complex XState Graphs for Backend logic.

## 4. Deliverables
| Artifact | Type | Description |
| :--- | :--- | :--- |
| `docs/system_context/L3_TOPOLOGY.md` | Doc | Auto-generated map of local repositories. |
| `docs/PHASE_0_PLAN.md` | Doc | This planning document. |
| `studio-governor/` | Code | A standalone prototype demonstrating the Governor Middleware. |
| `studio-governor/src/graph.ts` | Code | The LangGraph definition for the ReAct loop. |

## 5. Timeline (2 Weeks)
*   **Week 1: Infrastructure & Context**
    *   [x] Initialize C.O.R.E. Hub.
    *   [ ] Finalize System Context (L3 Topology).
    *   [ ] Scaffold `studio-governor` (Vite + React + WebContainers).
    *   [ ] Verify COOP/COEP Security Headers.
*   **Week 2: Logic & Throttling**
    *   [ ] Implement LangGraph JS Workflow.
    *   [ ] Implement `partial-json-parser` for streaming.
    *   [ ] Build the `CommandQueue` for backpressure.
    *   [ ] Integration Test: "The 50 Command Burst."

## 6. Resources & Tools
*   **Compute:** User's Local Machine (Node.js v24).
*   **Runtime:** WebContainers (In-Browser Node.js).
*   **Frameworks:** React 19, LangGraph JS, xterm.js.
*   **Context:** `.core/spokes/*.ps1` scripts.

## 7. Risks & Mitigation
| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **COOP/COEP Hell:** Security headers break external images/scripts. | High | High | Use local assets or proxy external resources. |
| **JSON Fragility:** LLM outputs invalid JSON during streaming. | High | Critical | Use `partial-json-parser` + aggressive retry logic. |
| **Runtime Compatibility:** LangGraph JS dependencies in WebContainer. | Medium | High | Use `langchain/langgraph/web` or polyfills for `async_hooks`. |
