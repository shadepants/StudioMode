# API Reference: Memory Server

The Memory Server acts as the central hub for the Governed HiVE system.

## Endpoints

### Tasks
| Endpoint        | Method | Description                             |
| --------------- | ------ | --------------------------------------- |
| `/tasks/create` | POST   | Create a new task                       |
| `/tasks/list`   | GET    | List tasks (filter by status, assignee) |
| `/tasks/claim`  | POST   | Claim a task for execution              |
| `/tasks/update` | POST   | Update task status/metadata             |

### Agents
| Endpoint                 | Method | Description             |
| ------------------------ | ------ | ----------------------- |
| `/agents/register`       | POST   | Register an agent       |
| `/agents/{id}/next`      | GET    | Get and claim next task |
| `/agents/{id}/tasks`     | GET    | List agent's tasks      |
| `/agents/heartbeat/{id}` | POST   | Send heartbeat          |

### Memory
| Endpoint        | Method | Description          |
| --------------- | ------ | -------------------- |
| `/memory/add`   | POST   | Add to vector memory |
| `/memory/query` | POST   | Semantic search      |

### State
| Endpoint        | Method | Description              |
| --------------- | ------ | ------------------------ |
| `/state`        | GET    | Get current system state |
| `/state/update` | POST   | Transition state         |
