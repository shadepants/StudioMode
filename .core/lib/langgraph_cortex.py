"""
LangGraph Cortex Integration for Studio Mode
============================================
Provides a LangGraph-based state machine for orchestrating the Hive Loop.
Integrates with the Memory Server for state persistence and task management.
"""

import os
import json
import httpx
from typing import TypedDict, Annotated, Literal, Optional
from enum import Enum

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages

# LiteLLM for model abstraction
import litellm

# --- CONFIGURATION ---

# --- CONFIGURATION ---
try:
    from ..config import MEMORY_SERVER_URL, DEFAULT_MODEL
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from .core.config import MEMORY_SERVER_URL, DEFAULT_MODEL


# --- STATE DEFINITION ---
# --- STATE DEFINITION ---
try:
    from ..models import AgentState
except ImportError:
    from .core.models import AgentState


class HiveState(TypedDict):
    """The shared state for the Hive Loop graph."""
    current_phase: AgentState
    task_id: Optional[str]
    task_text: Optional[str]
    task_assignee: Optional[str]
    context: str
    result: Optional[str]
    critique: Optional[str]
    iteration: int
    max_iterations: int


# --- MEMORY SERVER CLIENT ---
class MemoryClient:
    """HTTP client for interacting with the Memory Server."""
    
    def __init__(self, base_url: str = MEMORY_SERVER_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def get_state(self) -> AgentState:
        """Get current system state."""
        resp = self.client.get(f"{self.base_url}/state")
        return AgentState(resp.json()["current_state"])
    
    def update_state(self, new_state: AgentState) -> dict:
        """Transition to a new state."""
        resp = self.client.post(
            f"{self.base_url}/state/update",
            json={"new_state": new_state.value}
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_pending_tasks(self, assignee: str = "engineer") -> list:
        """Get pending tasks for an assignee."""
        resp = self.client.get(
            f"{self.base_url}/tasks/list",
            params={"status": "pending", "assignee": assignee}
        )
        return resp.json().get("tasks", [])
    
    def claim_task(self, task_id: str, agent_id: str) -> dict:
        """Claim a task for execution."""
        resp = self.client.post(
            f"{self.base_url}/tasks/claim",
            json={"task_id": task_id, "agent_id": agent_id}
        )
        resp.raise_for_status()
        return resp.json()
    
    def update_task(self, task_id: str, status: str, metadata: dict = None) -> dict:
        """Update task status and metadata."""
        resp = self.client.post(
            f"{self.base_url}/tasks/update",
            json={"task_id": task_id, "status": status, "metadata": metadata or {}}
        )
        resp.raise_for_status()
        return resp.json()
    
    def add_memory(self, text: str, mem_type: str = "episodic", metadata: dict = None) -> dict:
        """Add a memory entry."""
        resp = self.client.post(
            f"{self.base_url}/memory/add",
            json={"text": text, "type": mem_type, "metadata": metadata or {}}
        )
        return resp.json()
    
    def query_memory(self, query: str, limit: int = 5, filter_type: str = None) -> list:
        """Query memory for relevant context."""
        payload = {"text": query, "limit": limit}
        if filter_type:
            payload["filter_type"] = filter_type
        resp = self.client.post(f"{self.base_url}/memory/query", json=payload)
        return resp.json().get("results", [])
    
    def write_file(self, path: str, content: str) -> dict:
        """Write a file to workspace."""
        resp = self.client.post(
            f"{self.base_url}/fs/write",
            json={"path": path, "content": content}
        )
        resp.raise_for_status()
        return resp.json()


# --- AGENT NODES ---
def fetch_task_node(state: HiveState) -> HiveState:
    """
    IDLE → EXECUTING transition node.
    Fetches the next pending task from the queue.
    """
    client = MemoryClient()
    tasks = client.get_pending_tasks(assignee="engineer")
    
    if not tasks:
        # No tasks available, remain idle
        return {**state, "task_id": None, "task_text": None}
    
    # Claim the first pending task
    task = tasks[0]
    print(f"[fetch] Claiming task: {task['id']}")
    client.claim_task(task["id"], agent_id="engineer_agent")
    client.update_state(AgentState.EXECUTING)
    
    # Gather context from memory
    context_results = client.query_memory(task["text"], limit=3, filter_type="knowledge")
    context = "\n".join([r.get("text", "") for r in context_results])
    
    return {
        **state,
        "current_phase": AgentState.EXECUTING,
        "task_id": task["id"],
        "task_text": task["text"],
        "task_assignee": task.get("assignee"),
        "context": context,
        "iteration": state.get("iteration", 0) + 1
    }


def engineer_node(state: HiveState) -> HiveState:
    """
    EXECUTING node: The Engineer Agent generates code based on the task.
    """
    if not state.get("task_text"):
        return state
    
    client = MemoryClient()
    
    # Build the prompt
    system_prompt = """You are the C.O.R.E. Engineer, a specialized code generation agent.
Your primary objective is implementation, debugging, and optimization.
Follow the "Refinist" approach: Functional Core (v0.1) first, then hardening.

Rules:
1. Write clean, type-safe TypeScript or Python code
2. Include JSDoc/docstrings for all functions
3. Handle errors gracefully
4. Output ONLY the code, no explanations"""

    user_prompt = f"""Task: {state['task_text']}

Relevant Context:
{state.get('context', 'No additional context available.')}

Previous Critique (if any):
{state.get('critique', 'None - this is the first attempt.')}

Generate the code to complete this task."""

    # Call LLM
    response = litellm.completion(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000
    )
    
    result = response.choices[0].message.content
    
    # Save result to workspace
    output_path = f"agent_output/{state['task_id'][:8]}_result.txt"
    client.write_file(output_path, result)
    
    # Transition to REVIEW
    client.update_state(AgentState.REVIEW)
    client.update_task(state["task_id"], status="review", metadata={"result_path": output_path})
    
    client.add_memory(
        text=f"Engineer completed task {state['task_id'][:8]}: {state['task_text'][:50]}...",
        mem_type="episodic",
        metadata={"task_id": state["task_id"], "output_path": output_path}
    )
    
    return {
        **state,
        "current_phase": AgentState.REVIEW,
        "result": result
    }


def critic_node(state: HiveState) -> HiveState:
    """
    REVIEW node: The Critic Agent evaluates the Engineer's output.
    """
    if not state.get("result"):
        return state
    
    client = MemoryClient()
    
    system_prompt = """You are the Critic, a specialized QA agent.
Your role is to validate the output of the Engineer agent.

Evaluation Criteria:
1. Code Quality: Is it clean, readable, and follows best practices?
2. Completeness: Does it fully address the task requirements?
3. Safety: Are there any security issues or unsafe operations?
4. Type Safety: Are types properly defined and used?

Output Format:
VERDICT: PASS or FAIL
SCORE: 1-10
ISSUES: (list any issues, or "None")
SUGGESTIONS: (list improvements, or "None")"""

    user_prompt = f"""Task: {state['task_text']}

Engineer's Output:
```
{state['result']}
```

Evaluate this output against the task requirements."""

    response = litellm.completion(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=500
    )
    
    critique = response.choices[0].message.content
    passed = "VERDICT: PASS" in critique.upper()
    
    if passed or state.get("iteration", 0) >= state.get("max_iterations", 3):
        # Task complete or max iterations reached
        client.update_state(AgentState.IDLE)
        client.update_task(state["task_id"], status="completed", metadata={"critique": critique})
        client.add_memory(
            text=f"Critic APPROVED task {state['task_id'][:8]} after {state['iteration']} iteration(s)",
            mem_type="episodic"
        )
        return {
            **state,
            "current_phase": AgentState.IDLE,
            "critique": critique,
            "task_id": None,
            "task_text": None
        }
    else:
        # Send back for revision
        client.update_state(AgentState.EXECUTING)
        client.update_task(state["task_id"], status="pending", metadata={"critique": critique})
        client.add_memory(
            text=f"Critic REJECTED task {state['task_id'][:8]}: Sending back for revision",
            mem_type="episodic"
        )
        return {
            **state,
            "current_phase": AgentState.EXECUTING,
            "critique": critique
        }


def should_continue(state: HiveState) -> Literal["fetch", "engineer", "critic", "end"]:
    """Router function to determine next node."""
    phase = state.get("current_phase", AgentState.IDLE)
    print(f"[router] Current Phase: {phase}")
    
    if phase == AgentState.IDLE:
        if state.get("task_id"):
            print("[router] Decision: end")
            return "end"  # Just completed a task
        print("[router] Decision: fetch")
        return "fetch"  # Look for new tasks
    elif phase == AgentState.EXECUTING:
        print("[router] Decision: engineer")
        return "engineer"
    elif phase == AgentState.REVIEW:
        print("[router] Decision: critic")
        return "critic"
    else:
        print("[router] Decision: end")
        return "end"


# --- GRAPH CONSTRUCTION ---
def create_hive_graph() -> StateGraph:
    """Build the LangGraph state machine for the Hive Loop."""
    graph = StateGraph(HiveState)
    
    # Add nodes
    graph.add_node("fetch", fetch_task_node)
    graph.add_node("engineer", engineer_node)
    graph.add_node("critic", critic_node)
    
    # Set entry point
    graph.set_entry_point("fetch")
    
    # Add conditional edges from 'fetch'
    graph.add_conditional_edges(
        "fetch",
        should_continue,
        {
            "fetch": "fetch",     # Loop back if no task
            "engineer": "engineer",
            "end": END
        }
    )
    
    # Add conditional edges from 'engineer'
    graph.add_conditional_edges(
        "engineer",
        should_continue,
        {
            "critic": "critic",
            "end": END
        }
    )
    
    # Add conditional edges from 'critic'
    graph.add_conditional_edges(
        "critic",
        should_continue,
        {
            "fetch": "fetch",
            "engineer": "engineer",
            "end": END
        }
    )
    
    return graph.compile()


# --- MAIN EXECUTION ---
def run_hive_loop(max_iterations: int = 3) -> dict:
    """
    Execute one iteration of the Hive Loop.
    Returns the final state after processing.
    """
    graph = create_hive_graph()
    
    initial_state: HiveState = {
        "current_phase": AgentState.IDLE,
        "task_id": None,
        "task_text": None,
        "task_assignee": None,
        "context": "",
        "result": None,
        "critique": None,
        "iteration": 0,
        "max_iterations": max_iterations
    }
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    print("[LangGraph Cortex] Starting Hive Loop...")
    result = run_hive_loop()
    print(f"[LangGraph Cortex] Complete. Final state: {result.get('current_phase')}")
