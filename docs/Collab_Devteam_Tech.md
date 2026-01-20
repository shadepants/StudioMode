This is a comprehensive technical specification and product vision for the **Human-Parity Multi-Agent "Studio" Mode**.

This specification rejects the current industry trend of "instant, opaque code generation" which leads to unmaintainable "slop." Instead, it defines a system where AI agents operate with the transparency, tools, and pacing of a high-functioning human development team. This empowers a single user to act as a CTO/Architect, removing the resource barrier of hiring a team while maintaining deep control and understanding of the codebase.

---

# Technical Specification: The "Studio" Mode (Human-Parity Architecture)

## 1. The "Anti-Slop" Doctrine

Current AI coding tools prioritize *speed of inference*, resulting in code that looks correct but often lacks architectural coherence—"slop." To counter this, **Studio Mode** prioritizes *depth of reasoning* and *process visibility*.

**Core Principle:** Agents must not have "magic" access to the codebase. They must not use hidden APIs to inject code. They must interact with the project environment exactly as a human developer does: through the terminal, the file system, and the version control system.

## 2. The Human-Parity Constraint Engine (HPCE)

The HPCE is the governance layer that forces agents to adhere to human limitations. This is crucial for education: the user cannot learn if the AI performs actions (like analyzing a 10,000-line file instantly) that a human cannot replicate.

### A. Velocity Throttling & Cognitive Pacing

Instead of dumping a completed file instantly, the HPCE enforces a "Cognitive Rhythmic Output":

* **Reading Emulation:** When an agent "reads" a file, the UI highlights code blocks sequentially, scrolling at a readable pace (approx. 300-500 words per minute). This forces the user to scan the code *with* the agent.
* **Keystroke Dynamics:** Code is not "pasted"; it is "typed."
* **Base Typing Speed:** Variable between 40-80 WPM (Words Per Minute) depending on the "Seniority" setting of the agent.
* **Burst & Pause:** Typing occurs in logical bursts (functions/blocks) followed by "micro-pauses" (500ms - 2s) to simulate thinking time.
* **Self-Correction:** The agent will occasionally backspace to correct a typo or rename a variable, explicitly modeling the iterative nature of coding.



### B. Tooling Isomorphism (The "No-Magic" Rule)

Agents operate in a sandboxed shell environment with **zero privileged access**.

* **Terminal Only:** If the agent needs to know what files are in a directory, it must execute `ls -la`. It cannot query a hidden file-tree API.
* **Git-Based Workflow:** Agents cannot "undo" a mistake by resetting the context window. They must run `git status`, realize the error, and execute `git reset` or `git checkout`. This teaches the user proper version control hygiene.
* **Dependency Management:** Agents must explicitly run `pnpm install` and handle the output. If a package is missing, they troubleshoot the `package.json` file visibly.

## 3. The Multi-Agent "Studio" Architecture

In Studio Mode, the single "Copilot" splits into specialized, persistent personas. These are not just prompt wrappers; they are distinct state machines with unique permissions and "personalities."

### The Roles

1. **The Architect (Lead):**
* **Responsibility:** Breaks down high-level prompts into technical specs. Does not write implementation code.
* **Output:** Creates markdown files in a `/docs/specs/` directory (e.g., `feature-auth-flow.md`).
* **Behavior:** Asks the user clarifying questions before dispatching work to the Engineer.


2. **The Engineer (Builder):**
* **Responsibility:** Implementation.
* **Constraint:** Can only write code that matches the Architect's spec.
* **Behavior:** Opens file editors, runs the terminal, and commits code.


3. **The QA/Critic (Reviewer):**
* **Responsibility:** Rejects "slop."
* **Workflow:** Once the Engineer finishes, the QA agent runs the code, executes tests, and performs a "Code Review."
* **Output:** It does *not* fix the code. It opens a GitHub-style Pull Request comment thread listing the issues (e.g., "This function is too complex," or "You didn't handle the edge case for null inputs"). The Engineer must then fix it.



### The "Meeting Room" (Inter-Agent Communication)

Instead of hidden context passing, agents communicate via a visible "Team Chat" separate from the code editor.

* **Scenario:** The Engineer hits a roadblock.
* **Action:** The Engineer pauses typing, switches to the "Team Chat," and pings the Architect: *"I can't implement the caching layer because Redis isn't configured. Should I mock it or set up Redis?"*
* **Education Value:** The user sees the trade-off discussion happen in real-time. They learn *how* decisions are made, not just the final result.

## 4. User Experience: The "Over-the-Shoulder" View

The UI transforms from a standard IDE into a "Flight Deck."

### The Viewports

1. **The Workspace (Main):** The active file being edited. You see the cursor moving, text appearing, and the terminal executing commands.
2. **The Thought Log (Sidebar):** A real-time stream of the active agent's internal monologue.
* *Example:* "The user wants a dark mode toggle. I should check `tailwind.config.js` first to see if 'class' strategy is enabled."


3. **The Team Chat (Bottom):** Where agents coordinate. The user can jump in here as the "CTO" to break ties or redirect focus.

### The "Intervention" Mechanism

Since the agents work at a human pace, the user can **interrupt** effectively.

* **Hover-to-Query:** While the Engineer is typing a specific line, the user can hover and click "Why?" The agent pauses and explains: *"I'm using a `useCallback` here because this function is passed to a child component, and I want to prevent unnecessary re-renders."*
* **"Stop & Pivot":** The user can hit a "Freeze" button. The agents stop. The user types: *"Don't use Redux for this, just use React Context."* The Architect acknowledges, updates the spec, and the Engineer resumes with the new direction.

## 5. Implementation Roadmap (Phased Rollout)

### Phase 1: The "Slow" Agent (Single Node)

* Implement the **HPCE (Constraint Engine)**.
* Replace instantaneous text generation with the "Typing Simulator."
* Enforce `exec` calls for all file operations (no virtual file system manipulation).

### Phase 2: The Binary Pair (Dev + QA)

* Introduce the **QA Agent loop**.
* The Dev agent cannot mark a task "Complete" until the QA agent passes the test suite.
* User visibility into the "Code Review" diffs generated by the QA agent.

### Phase 3: The Full Studio (Architect + Dev + QA + User)

* Full multi-agent orchestration.
* The "Team Chat" interface.
* Long-term memory (agents remember "we decided to use Shadcn UI three days ago").

This architecture ensures that the AI is not a crutch, but a **multiplier**. It turns the solo developer into a manager of a competent, junior-to-mid-level team, allowing them to build enterprise-grade software without losing the ability to understand and maintain the code themselves.