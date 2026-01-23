# CLI Reference

Studio Mode provides several CLI tools for system interaction and agent management.

## Hive CLI
Manage the overall system state and tasks.

```powershell
python .core/cli/hive_cli.py <command>

Commands:
  status      Get Hive status
  start       Start the Hive (IDLE → EXECUTING)
  stop        Stop the Hive (→ IDLE)
  add-task    Add a task (-t TEXT -a ASSIGNEE -p PRIORITY)
  list-tasks  List tasks (-s STATUS -a ASSIGNEE)
```

## Agent Client
Low-level agent task management.

```powershell
python .core/lib/agent_client.py <command>

Commands:
  poll        Start polling for tasks
  list        Show pending tasks
  complete    Mark task complete
  register    Register agent
```

## Autonomous Agent
Launch individual agent instances.

```powershell
python .core/lib/autonomous_agent.py --agent-id NAME --model MODEL

Options:
  --agent-id    Unique identifier (default: gemini-cli)
  --model       LiteLLM model string (default: groq/llama-3.1-8b-instant)
```
