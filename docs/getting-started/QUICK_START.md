# Quick Start Guide

Follow these steps to get Studio Mode up and running.

## Prerequisites
- Windows OS (designed for PowerShell/CMD)
- Python 3.12+
- `GROQ_API_KEY` set in your environment

## One-Command Launch (Recommended)
This starts the entire system including the Memory Server, Agent Services, and Orchestrator.

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Launch the hive
./start_hive.ps1
```

## Manual Launch (Development)
For more granular control during development:

```powershell
# 1. Start the Memory Server
python .core/services/memory_server.py

# 2. Start an autonomous agent (in a new terminal)
python .core/lib/autonomous_agent.py --agent-id gemini-cli
```

## Next Steps
- Verify the system is running: `python .core/cli/hive_cli.py status`
- Add your first task: `python .core/cli/hive_cli.py add-task --text "Hello world"`
