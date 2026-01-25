# Parallel 3-Way Review System

**Source**: loki-mode Quality Gates  
**Impact**: Simultaneous code, business logic, and security audits

---

## Core Concept

Every code change goes through **3 specialized reviewers simultaneously** instead of a single sequential review.

### Review Flow

```
IMPLEMENT → REVIEW (parallel) → AGGREGATE → FIX → RE-REVIEW → COMPLETE
              │
              ├─ code-reviewer (Sonnet)
              │  └─ Code quality, patterns, best practices
              │
              ├─ business-logic-reviewer (Sonnet)
              │  └─ Requirements, edge cases, UX
              │
              └─ security-reviewer (Sonnet)
                 └─ Vulnerabilities, OWASP Top 10
```

### Benefits

- **Faster feedback**: Parallel execution vs. sequential
- **Multi-perspective coverage**: Different lens per reviewer
- **Specialization**: Each reviewer optimized for their domain

---

## Severity-Based Issue Handling

Not all issues should block progress. loki-mode uses tiered severity handling:

| Severity     | Action                      | Code Annotation          | Re-Review? |
| ------------ | --------------------------- | ------------------------ | ---------- |
| **Critical** | **BLOCK** - Fix immediately | N/A                      | ✅ Yes      |
| **High**     | **BLOCK** - Fix immediately | N/A                      | ✅ Yes      |
| **Medium**   | **BLOCK** - Fix immediately | N/A                      | ✅ Yes      |
| **Low**      | Continue with TODO          | `// TODO(review): ...`   | ❌ No       |
| **Cosmetic** | Continue with FIXME         | `// FIXME(nitpick): ...` | ❌ No       |

### Example

```python
# Critical: SQL injection vulnerability - BLOCKS merge
def get_user(user_id):
    return db.execute(f"SELECT * FROM users WHERE id = {user_id}")  # ❌ BLOCKED

# Low: Missing docstring - Continues with annotation
# TODO(review): Add docstring explaining the caching strategy
def compute_stats():  # ✅ Continues
    return cached_results

# Cosmetic: Variable naming - Continues with annotation
# FIXME(nitpick): Consider renaming 'x' to 'user_count' for clarity
x = len(users)  # ✅ Continues
```

---

## Studio Mode Integration Points

### Current Critic Service

**File**: `.core/services/critic_service.py`

**Current behavior**: Single review pass with binary approve/reject

### Proposed Enhancement: Multi-Perspective Critic

#### Phase 1: Parallel Reviews (No LLM Changes)

Extend `critic_service.py` to run 3 analysis passes in parallel:

```python
# .core/services/critic_service.py

async def review_code(file_path: str) -> ReviewResult:
    """Run parallel 3-way review."""
    
    # Execute all 3 reviews concurrently
    code_review, business_review, security_review = await asyncio.gather(
        review_code_quality(file_path),
        review_business_logic(file_path),
        review_security(file_path)
    )
    
    # Aggregate results
    all_issues = aggregate_reviews(
        code_review, 
        business_review, 
        security_review
    )
    
    # Apply severity gating
    blocking_issues = [i for i in all_issues if i.severity in ['CRITICAL', 'HIGH', 'MEDIUM']]
    
    if blocking_issues:
        return ReviewResult(
            approved=False,
            issues=blocking_issues,
            requires_fix=True
        )
    else:
        return ReviewResult(
            approved=True,
            issues=all_issues,  # Includes Low/Cosmetic for annotations
            requires_fix=False
        )
```

#### Phase 2: Specialized Review Personas

Create 3 specialized review modes:

```markdown
# .core/agents/critic/skills/code-review.md
You are a **Code Quality Reviewer**. Focus on:
- Design patterns and architecture
- Code duplication and DRY violations
- Performance and efficiency
- Readability and maintainability
- Naming conventions
```

```markdown
# .core/agents/critic/skills/business-review.md
You are a **Business Logic Reviewer**. Focus on:
- Requirements compliance
- Edge case handling
- User experience implications
- Data validation
- Error messaging
```

```markdown
# .core/agents/critic/skills/security-review.md
You are a **Security Reviewer**. Focus on:
- OWASP Top 10 vulnerabilities
- Authentication and authorization
- Input validation and sanitization
- Secrets management
- Dependency vulnerabilities
```

#### Phase 3: Severity Classification

Train Critic to classify issues by severity:

```python
class ReviewIssue:
    severity: Literal['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'COSMETIC']
    category: Literal['CODE', 'BUSINESS', 'SECURITY']
    message: str
    file: str
    line: int
    suggested_fix: Optional[str]
```

**Severity Guidelines**:
- **CRITICAL**: Security vulnerabilities, data loss, system crashes
- **HIGH**: Incorrect business logic, major bugs, broken features
- **MEDIUM**: Performance issues, missing error handling, poor UX
- **LOW**: Missing documentation, minor refactoring opportunities
- **COSMETIC**: Code style, naming preferences, whitespace

---

## Implementation Roadmap

### ✅ Can Do Now (No Architecture Changes)

1. **Add severity field** to review responses
2. **Document review categories** in `critic.md`
3. **Create annotation templates** for Low/Cosmetic issues

### 🔄 Requires Orchestrator Update

4. **Parallel review execution** in `critic_service.py`
5. **Aggregation logic** to merge 3 review results
6. **Severity-based gating** (block vs. continue)

### 🚀 Future Enhancement (Phase 5+)

7. **Multi-agent LLM calls** (3 separate Critic instances)
8. **Specialized review prompts** per category
9. **Learning from severity patterns** (RARV integration)

---

## Metrics to Track

After implementing parallel review:

| Metric                | Target                                   |
| --------------------- | ---------------------------------------- |
| Review coverage       | 100% code/business/security              |
| False positive rate   | <10% for CRITICAL/HIGH                   |
| Review time           | <50% of sequential (via parallelization) |
| Low/Cosmetic accuracy | >80% correctly classified                |

---

## Key Takeaways

1. **Parallel > Sequential**: Faster feedback via concurrent reviews
2. **Severity matters**: Not all issues should block progress
3. **Specialization**: Different reviewers for different concerns
4. **Start simple**: Begin with categorization, then parallelize, then specialize

---

## References

- **Pattern**: Multi-perspective review with severity-based gating
- **Benefit**: Faster, more comprehensive quality assurance
- **Trade-off**: Increased complexity in aggregation logic
- **Integration**: Extends current `critic_service.py` incrementally
