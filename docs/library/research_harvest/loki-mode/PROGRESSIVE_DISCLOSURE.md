# Progressive Disclosure: Context-Efficient Skill Architecture

**Source**: loki-mode v3.0+ Skill System  
**Impact**: ~15% → ~1% context usage (14% reduction)

---

## The Problem

Original loki-mode had a monolithic `SKILL.md` file:
- **1,517 lines** of instructions
- Consumed **~15% of context window** before any work began
- Left less room for actual code and reasoning

---

## The Solution: Progressive Disclosure

Load core instructions always, but defer detailed modules until needed.

### Architecture

```
SKILL.md (~190 lines)         # Always loaded: core RARV cycle, autonomy rules

skills/
  ├── 00-index.md             # Module routing table
  ├── agents.md               # Agent dispatch, A2A patterns
  ├── production.md           # HN patterns, batch processing, CI/CD
  ├── quality-gates.md        # Review system, severity handling
  ├── testing.md              # Playwright, E2E, property-based
  ├── model-selection.md      # Task tool, parallelization
  ├── artifacts.md            # Code generation patterns
  ├── patterns-advanced.md    # Constitutional AI, debate
  └── troubleshooting.md      # Error recovery, fallbacks

references/                   # Deep documentation (23KB+ files)
```

### Routing Table Pattern (`00-index.md`)

```markdown
# Skill Module Index

## When to Load What

| Scenario                        | Module               | Priority |
| ------------------------------- | -------------------- | -------- |
| Multi-agent coordination needed | agents.md            | HIGH     |
| Production deployment task      | production.md        | HIGH     |
| Code review phase               | quality-gates.md     | CRITICAL |
| Test writing/debugging          | testing.md           | HIGH     |
| Performance optimization        | model-selection.md   | MEDIUM   |
| Complex pattern needed          | patterns-advanced.md | LOW      |
| Error encountered               | troubleshooting.md   | CRITICAL |

## Loading Instructions

1. Read this index first
2. Identify which module(s) match current task
3. Load ONLY the required module(s)
4. Avoid loading all modules at once
```

---

## Results

| Metric           | Before      | After     | Improvement       |
| ---------------- | ----------- | --------- | ----------------- |
| **Base Context** | ~15%        | ~1%       | **14% reduction** |
| **Skill Lines**  | 1,517       | 190       | **87% smaller**   |
| **Load Time**    | Always full | On-demand | **Faster**        |
| **Maintenance**  | Monolithic  | Modular   | **Easier**        |

---

## Studio Mode Integration Recommendations

### Current State Analysis

Studio Mode agent files:
- `.core/agents/critic.md` (~100 lines)
- `.core/agents/engineer.md` (pending)
- Future agents: researcher, tester, deployer, etc.

**Current approach**: Each agent has separate persona files (good modularity)

### When to Apply Progressive Disclosure

**Trigger**: If any single agent skill file exceeds **500 lines**

**Implementation**:
1. Create `.core/agents/{agent}/SKILL.md` (core always-loaded instructions)
2. Create `.core/agents/{agent}/skills/` directory
3. Split detailed patterns into modules:
   - `code-patterns.md` - Language-specific best practices
   - `review-checklist.md` - Quality gate procedures
   - `troubleshooting.md` - Error recovery strategies
4. Create `00-index.md` routing table

### Example: Critic Agent Split

If `critic.md` grows to 600+ lines:

```
.core/agents/critic/
  ├── SKILL.md                    # Core: RARV cycle, review philosophy (~150 lines)
  ├── skills/
  │   ├── 00-index.md             # When to load what
  │   ├── static-analysis.md      # Linting, type checking procedures
  │   ├── semantic-review.md      # Business logic validation
  │   ├── security-audit.md       # Vulnerability patterns
  │   └── performance.md          # Optimization guidelines
  └── references/
      └── OWASP-Top-10.md         # Deep security reference
```

---

## Key Takeaways

1. **Don't optimize prematurely** - Only split when files become unwieldy (500+ lines)
2. **Use routing tables** - Make module selection deterministic
3. **Measure context usage** - Track token consumption before/after
4. **Maintain modularity** - Each skill module should be self-contained

---

## Implementation Checklist

When splitting skills in the future:

- [ ] Identify monolithic skill file (>500 lines)
- [ ] Create skill directory structure
- [ ] Extract core instructions (keep <200 lines)
- [ ] Split specialized knowledge into modules
- [ ] Create routing table (`00-index.md`)
- [ ] Measure context reduction
- [ ] Update agent loading logic to read routing table

---

## References

- **Pattern**: Progressive Disclosure (UX principle applied to AI context)
- **Benefit**: ~14% context savings = more room for code/reasoning
- **Trade-off**: Slight complexity increase (routing logic)
- **When**: Only when skill files exceed 500 lines
