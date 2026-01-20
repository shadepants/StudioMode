1. MCP Servers (The "Outside" Infrastructure)
These are external services integrated into the Antigrav environment to provide the agent with capabilities beyond simple text generation.

Supabase MCP (supabase-mcp-server): Accesses DB schemas, executes SQL, and manages Edge Functions.
Puppeteer (@modelcontextprotocol/server-puppeteer): Browser automation for UI inspection and visual debugging.
Memory (@modelcontextprotocol/server-memory): Persistent storage for project context and architectural decisions.
GitHub MCP (@modelcontextprotocol/server-github): Manages issues, PRs, and repository history.
Brave Search (@modelcontextprotocol/server-brave-search): Web search for documentation and solution patterns.
Filesystem (@modelcontextprotocol/server-filesystem): Direct read/write access to the local repository.
2. Agent Skills & Tools (The "Inside" Capabilities)
These are specific actions the agent performs by combining MCP servers with local repository scripts.

Quality Assurance:

audit-database: Runs npm run audit to verify DB schema integrity.
check-compliance: Runs npm run compliance:check for TypeScript standards.
security-scan: Runs npm run security:scan to find exposed secrets.
System Management:

manage-hooks: Uses npm run hooks:status or hooks:optimize for React performance.
verify-env: Runs npm run init:env to check environment health.
Context Awareness:

remember-fact: Stores architectural decisions in the Memory MCP.
search-docs: Fetches updated library documentation via Brave Search.
3. Workflows (The "Operational" Logic)
These define how development and automation are structured within the repo.

Development Modes (from CONTRIBUTING.md):

Mode I (Idea): Brainstorming and requirements.
Mode B (Build): Implementation and scaffolding.
Mode F (Fix): Bug reporting and testing.
Mode R (Refactor): DRY, performance, and type cleanup.
Mode S (Secure): RLS audits and security patching.
Pre-Commit Verification (The "Safety Net"):

npm run lint: Zero warnings/errors allowed.
npx tsc --noEmit: Strict type checking.
npm run test: Full test suite pass.
npm run build: Production build verification.
Data Import Workflow:

A 4-step wizard: Upload → Map → Validate → Import.
4. Rules (The "Constraints")
These govern code quality, design, and agent behavior.

Architectural Rules:

The Golden Rule: NEVER DELETE CODE. Use // DEPRECATED instead.
Type Safety: Zero any types allowed. Use unknown with type guards if necessary.
Design System: "Neon-Noir" theme (Glassmorphism, #0B0B15 backgrounds, glow accents).
Mobile-First: Interactive elements must have >44px touch targets.
Operational Rules for Agents:

Verify Paths: Never guess; use ls or find.
Refactor Checkpoint: Stop and verify after 3 major edits to avoid "fix-it" loops.
Tool Alignment: Use replace_file_content precisely.
Linting Rules (from eslint.config.js):

@typescript-eslint/no-explicit-any: Set to error.
@typescript-eslint/no-unused-vars: Errors unless prefixed with an underscore (_).
react-refresh/only-export-components: Warning (enforces HMR compatibility).
5. Configuration Locations
Global MCP Config: %USERPROFILE%\.gemini\antigravity\mcp_config.json
Project Rules: docs/BEST_PRACTICES.md and docs/ONBOARDING.md
Task Tracking: task.md (The Source of Truth)