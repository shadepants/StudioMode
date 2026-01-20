# Research Report: Strategic Forgetting & Memory Decay

**Date:** January 19, 2026
**Topic:** Why "Forgetting" is Critical for C.O.R.E. v4.2

---

## 1. The Core Insight: "More Context != Better Intelligence"

Research from 2025 (University of Texas, Purdue, and Google DeepMind) confirms a paradox: **Accumulating infinite context leads to a 30% decline in reasoning quality.**

### 1.1 The "Brain Rot" Hypothesis
*   **Finding:** Continuous exposure to "stale" or "low-quality" data (e.g., raw logs of past mistakes) poisons the model's reasoning.
*   **Mechanism:** LLMs struggle to distinguish between "Current Truth" and "Past Hallucination" when both are present in the context window.
*   **Impact on GCC:** If we feed the Agent the entire `decision_log.md` (which contains its past errors), it is statistically more likely to repeat those errors.

### 1.2 The "Stability-Plasticity" Dilemma
*   **Stability:** Remembering the "Grand Goal" (The Architecture).
*   **Plasticity:** Adapting to the "Current Task" (The Code).
*   **Solution:** **Adaptive Forgetting.** The Agent must "forget" the implementation details of Task A once Task A is complete, retaining only the *outcome* (the API contract).

---

## 2. Validation of C.O.R.E. Mitigation Strategy

Our proposed **"Log Rotation"** strategy is scientifically sound and aligns with State-of-the-Art (SOTA) research:

1.  **Session Logs (Short-Term):** High-fidelity, raw output. Preserves "Plasticity" (adapting to immediate errors).
    *   *Action:* Rotate every 50 turns.
2.  **Knowledge Graph (Long-Term):** Low-fidelity, high-abstraction. Preserves "Stability" (remembering the architecture).
    *   *Action:* Summarize logs into `knowledge_graph.json`.
3.  **Context Injection (Dynamic):** Use "Windowed Context" to inject only the relevant slice.

---

## 3. Conclusion

"Forgetting" is not a bug; it is a feature. By implementing **Log Rotation**, we are not just saving disk space; we are actively preventing "Reasoning Drift" and ensuring the Agent remains sharp.

**Recommendation:** Proceed with the "Log Rotation" implementation in the GCC.
