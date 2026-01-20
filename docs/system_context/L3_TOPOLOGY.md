# Layer 3: System Topology Map

**Version:** 1.0.0
**Grounding Root:** `C:\users\user\Repositories\StudioMode`
**Last Scanned:** January 15, 2026

## 1. Primary Hub (The Control Room)
The central nervous system of Studio Mode. All agent logic and memory reside here.

| Path | Description |
| :--- | :--- |
| `Repositories\StudioMode\` | **Project Root**. |
| `Repositories\StudioMode\.core\` | Framework logic, services, and memory client. |
| `Repositories\StudioMode\docs\` | System context and Phase 0 documentation. |
| `Repositories\StudioMode\studio-governor\` | (Planned) React sandbox for command execution. |

## 2. The Factory Floor (Repositories)
Active development projects outside the framework.

| Project Name | Path | Notes |
| :--- | :--- | :--- |
| **Pennys-PIMS** | `C:\users\user\Repositories\Pennys-PIMS` | Targeted for integration. |
| **Psychometrics** | `C:\users\user\Repositories\Psychometrics` | Targeted for integration. |

## 3. Infrastructure & Toolchain (Layer 1-2 Anchors)
Crucial directories for system operations and tool availability.

| Category | Path | Description |
| :--- | :--- | :--- |
| **Package Manager** | `C:\users\user\scoop` | Main source of binaries and shims. |
| **Containerization** | `C:\users\user\.docker` | Docker configurations and model storage. |
| **Security** | `C:\users\user\.ssh` | SSH keys and known hosts. |
| **CLI Configs** | `C:\users\user\.config` | Shared tool configurations. |

## 4. Documentation & Research Hotspots
Non-repository locations containing critical knowledge.

| Path | Significance |
| :--- | :--- |
| `C:\users\user\Documents\Collab_Devteam_Tech.md` | Team collaboration standards. |
| `C:\users\user\Downloads\Specs & Architecture_Human Parity Studio.md` | Original architectural specs. |

## 5. Noise Reducers (Exclusion Zones)
*   `C:\users\user\AppData\`
*   `C:\users\user\node_modules\`
*   `C:\users\user\Downloads\` (except specific hotspots)
*   `C:\users\user\Favorites\` / `Links\` / `Searches\`