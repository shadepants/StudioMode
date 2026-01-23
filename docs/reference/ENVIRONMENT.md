# Environment & Configuration

## Environment Variables

| Variable               | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| `GROQ_API_KEY`         | Groq API key for LLM access                           |
| `MEMORY_SERVER_URL`    | Memory Server URL (default: http://127.0.0.1:8000)    |
| `ENGINEER_SERVICE_URL` | Engineer Service URL (default: http://127.0.0.1:8001) |
| `LITELLM_LOG`          | Optional debug logging for LiteLLM                    |

## Key Files & Directories

| File/Path                 | Description               |
| ------------------------- | ------------------------- |
| `.core/memory/tasks.db`   | SQLite task database      |
| `.core/memory/lancedb/`   | LanceDB vector storage    |
| `workspace/agent_output/` | Generated agent outputs   |
| `workspace/incoming/`     | Librarian ingestion queue |
