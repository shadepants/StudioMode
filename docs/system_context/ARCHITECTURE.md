# C.O.R.E. Architecture: System Context Engineering

**Version:** 1.0.0
**Status:** Initializing Hub

## 1. Directory Strategy (Hub & Spoke)

| Path | Purpose |
| :--- | :--- |
| `.core/lib/` | Reusable PowerShell modules (Core functions). |
| `.core/spokes/` | Modular inventory/discovery scripts. |
| `.core/config/` | System-wide AI configuration and environment pointers. |
| `.core/agents/` | Specialist agent role definitions and blueprints. |
| `docs/system_context/` | Output directory for the "System Digital Twin" (Markdown). |

## 2. Naming Conventions
*   **Scripts:** `verb_noun.ps1` (e.g., `get_system_inventory.ps1`).
*   **Documentation:** `UPPER_CASE.md` for logs/anchors, `Kebab-case.md` for technical specs.
*   **Variables:** `PascalCase` for PowerShell, `snake_case` for JSON/Config.

## 3. Data Flow
1. **Trigger:** AI Agent (me) or User runs a Spoke.
2. **Action:** Spoke gathers specific OS/App metadata.
3. **Storage:** Results are synthesized into `docs/system_context/`.
4. **Result:** I use the updated context to provide grounded, non-hallucinated assistance.
