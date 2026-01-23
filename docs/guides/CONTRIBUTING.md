# Contributing Guide

Welcome to the Studio Mode development factory. Here is how you can contribute to the system.

## Adding a New Agent Service

1. **Inherit from Base**: Use `.core/services/base_service.py` as your starting point.
2. **Define Persona**: Add a new `.md` file in `.core/agents/` to define the agent's behavior.
3. **Register Service**: Add the service to `start_hive.ps1` and ensure it uses a unique port (800x range).

## Architecture Governance

All changes must follow the **Governed HiVE** specification:
- Core reasoning must be graph-based (Cortex).
- Human-in-the-Loop gates must be preserved.
- Safety checks must be enforced by the Governor.

## Testing
Run the test suite before submitting any changes:
```powershell
pytest tests/ -v
```
