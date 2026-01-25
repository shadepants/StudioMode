# loki-mode: RARV Cycle Overview

**Source**: [github.com/asklokesh/loki-mode](https://github.com/asklokesh/loki-mode)  
**Benchmark**: 98.78% HumanEval (vs. Claude Desktop 64.02%, Cursor 55.61%)

---

## Core Philosophy

loki-mode is a multi-agent autonomous system that doesn't just write code—it **thinks, acts, learns, and verifies** through continuous self-improvement.

The system achieves **2-3x quality improvement** through the RARV (Reason-Act-Reflect-Verify) cycle.

---

## RARV Cycle: Reason-Act-Reflect-Verify

A four-phase autonomous loop that enables continuous learning from failures:

```
1.. REASON
   └─ Read .loki/CONTINUITY.md including "Mistakes & Learnings"
   └─ Check .loki/state/ and .loki/queue/
   └─ Identify next task or improvement

2. ACT
   └─ Execute task, write code
   └─ Commit changes atomically (git checkpoint)

3. REFLECT
   └─ Update .loki/CONTINUITY.md with progress
   └─ Update state files
   └─ Identify NEXT improvement

4. VERIFY
   └─ Run automated tests (unit, integration, E2E)
   └─ Check compilation/build
   └─ Verify against spec

   IF VERIFICATION FAILS:
   ├─ Capture error details (stack trace, logs)
   ├─ Analyze root cause
   ├─ UPDATE "Mistakes & Learnings" in CONTINUITY.md
   ├─ Rollback to last good git checkpoint if needed
   └─ Apply learning and RETRY from REASON
```

---

## Key Components

### CONTINUITY.md
- **Purpose**: Persistent memory of progress and learnings
- **Structure**:
  - Current task context
  - Completed work
  - **Mistakes & Learnings** section (critical for self-improvement)
  - Next steps

### State Checkpoints
- Automatic state saves every 5 seconds
- Git checkpoints for atomic rollback
- Enable auto-resume after interruptions

### Perpetual Improvement Mode
There is **NEVER** a "finished" state. After completing the PRD, the system:
- Runs performance optimizations
- Adds missing test coverage
- Improves documentation
- Refactors code smells
- Updates dependencies
- Enhances user experience

It keeps going until you stop it.

---

## Studio Mode Integration Opportunities

### 1. REFLECT Node in Cortex State Machine
**Current**: `IDLE → EXECUTING → REVIEW → IDLE`

**Proposed**: `IDLE → EXECUTING → REVIEW → REFLECT → IDLE`

The REFLECT node would:
- Update `CONTINUITY.md` or `LESSONS.md` in `.core/memory/`
- Capture patterns from failed reviews
- Build a knowledge base of "what not to do"

### 2. Critic Agent Enhancement
**Current**: Static analysis and rejection

**Proposed**: Learning-based review
- When rejecting code, log the pattern to `.core/memory/LESSONS.md`
- Before future reviews, read LESSONS to avoid repeating mistakes
- Track improvement metrics (rejection rate over time)

### 3. Auto-Resume Capability
- Implement state checkpointing in Orchestrator
- Enable graceful restart after rate limits or crashes
- Use `.core/state/checkpoint.json` for resume points

---

## Metrics & Success Indicators

- **Quality**: 2-3x improvement through continuous self-verification
- **Context Efficiency**: See [PROGRESSIVE_DISCLOSURE.md](file:///C:/Users/User/Repositories/StudioMode/docs/library/research_harvest/loki-mode/PROGRESSIVE_DISCLOSURE.md)
- **Benchmark**: 98.78% HumanEval (industry-leading)

---

## References

- **Core Concept**: Reflection + Learning from failures
- **Implementation**: `.loki/CONTINUITY.md` as persistent memory
- **Verification**: Automated testing with rollback on failure
- **Outcome**: Continuous improvement without human intervention
