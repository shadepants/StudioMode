# Agent Personas

Studio Mode agents follow specific behavioral personas defined in `.core/agents/`.

## Personas

| Persona       | Responsibility                                            | Logic Source                |
| ------------- | --------------------------------------------------------- | --------------------------- |
| **Architect** | High-level system design and implementation planning.     | `.core/agents/architect.md` |
| **Engineer**  | Core code implementation based on architectural plans.    | `.core/agents/engineer.md`  |
| **Critic**    | Code review, static analysis, and quality verification.   | `.core/agents/critic.md`    |
| **Manager**   | Task coordination, delegation, and progress tracking.     | `.core/agents/manager.md`   |
| **Worker**    | General task execution and utility work.                  | `.core/agents/worker.md`    |
| **Scout**     | Web research, documentation scraping, and info gathering. | (via Scout Service)         |

## Persona Configuration
Personas are defined as markdown files containing instructions and constraints for the LLM. When an agent is initialized with a specific persona, it pulls its "system prompt" from these definitions.
