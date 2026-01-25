# .core/services/memory_server.py
import os
import time
import asyncio
import json
import uuid
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- IMPORTS ---
import sys
# Add .core directory to sys.path so we can import config directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from config import DB_URI, SQLITE_DB, SYNC_INTERVAL, WORKSPACE_DIR
    from models import AgentState, VALID_TRANSITIONS
    from services.vector_store import VectorStore, MemoryEntry
    from services.file_manager import FileManager
    from services.task_manager import TaskManager, TaskCreateRequest, TaskUpdateRequest, TaskClaimRequest
    from services.state_manager import StateManager, StateUpdateRequest
    from services.research_manager import ResearchManager, SourceAddRequest
except ImportError as e:
    print(f"[!] Import Error: {e}")
    # Fallback if structure is different
    from ..config import DB_URI, SQLITE_DB, SYNC_INTERVAL, WORKSPACE_DIR
    from ..models import AgentState
    from .vector_store import VectorStore
    from .file_manager import FileManager
    from .task_manager import TaskManager
    from .state_manager import StateManager
    from .research_manager import ResearchManager

# --- GLOBAL SERVICE CONTAINER ---
class ServiceContainer:
    cortex: Optional[VectorStore] = None
    files: Optional[FileManager] = None
    tasks: Optional[TaskManager] = None
    state: Optional[StateManager] = None
    research: Optional[ResearchManager] = None

services = ServiceContainer()

# --- BACKGROUND TASKS ---
async def doc_sync_loop():
    """Background loop for file syncing."""
    while True:
        try:
            if services.files:
                await asyncio.to_thread(services.files.sync_documentation)
        except Exception as e:
            print(f"[!] Sync error: {e}")
        await asyncio.sleep(SYNC_INTERVAL)

# --- LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] Initializing Modular Memory System...")
    os.makedirs(os.path.dirname(DB_URI), exist_ok=True)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    
    # Initialize Services
    services.cortex = VectorStore(DB_URI)
    services.files = FileManager(services.cortex)
    services.tasks = TaskManager(SQLITE_DB)
    services.state = StateManager(services.cortex)
    services.research = ResearchManager(SQLITE_DB, services.cortex)
    
    # Start Background Loop
    asyncio.create_task(doc_sync_loop())
    
    yield
    print("[*] Shutting down.")
    if services.cortex: services.cortex.flush()
    if services.tasks: services.tasks.close()
    if services.research: services.research.close()

# --- API ---
app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- MODELS (Specific to API layer) ---
class AddMemoryRequest(BaseModel):
    text: str
    type: str 
    metadata: dict = {}

class QueryRequest(BaseModel):
    text: str
    limit: int = 3
    filter_type: Optional[str] = None

class FileWriteRequest(BaseModel):
    path: str
    content: str
    
class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str] = []

class ReflectRequest(BaseModel):
    task_id: str
    failure_reason: str
    pattern: str
    solution: Optional[str] = None

# --- ENDPOINTS: STATE ---

@app.get("/state")
def get_state():
    if not services.state: raise HTTPException(503, "Initializing")
    return {"current_state": services.state.get_state()}

@app.post("/state/update")
def update_state(req: StateUpdateRequest):
    return services.state.update_state(req)

# --- ENDPOINTS: RESEARCH & KNOWLEDGE ---

@app.post("/research/start")
async def start_research(background_tasks: BackgroundTasks, topic: str, depth: int = 1):
    job_id = await services.research.start_research(topic, background_tasks)
    return {"status": "started", "job_id": job_id}

@app.get("/research/status")
def get_research_status():
    return services.research.get_research_status()

@app.get("/sources")
def get_sources(limit: int = 50):
    return services.research.get_sources(limit)

@app.post("/sources/add")
def add_source(req: SourceAddRequest):
    source_id = services.research.add_source(req)
    return {"status": "success", "id": source_id}

@app.get("/knowledge/graph")
def get_knowledge_graph():
    return services.research.get_knowledge_graph()

# --- ENDPOINTS: MEMORY ---

@app.post("/memory/add")
def add_memory(req: AddMemoryRequest):
    mem_id = services.cortex.add(req.text, req.type, req.metadata)
    return {"status": "success", "id": mem_id}

@app.post("/memory/query")
def query_memory(req: QueryRequest):
    return services.research.query_memory_with_cache(req.text, req.limit, req.filter_type)

@app.get("/memory/feed")
def get_memory_feed(limit: int = 20):
    return services.cortex.get_feed(limit)

# --- ENDPOINTS: REFLECT ---

@app.post("/reflect/log_lesson")
def log_lesson(req: ReflectRequest):
    """Log a failed pattern to LESSONS.md for future learning."""
    lessons_path = os.path.join(".core/memory", "LESSONS.md")
    
    # Ensure file exists
    if not os.path.exists(lessons_path):
        os.makedirs(os.path.dirname(lessons_path), exist_ok=True)
        with open(lessons_path, "w") as f:
            f.write("# Lessons Learned\n\n---\n\n")
    
    lesson_entry = f"""## Pattern: Task {req.task_id} Failure
- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Task ID**: {req.task_id}
- **Issue**: {req.failure_reason}
- **Pattern to Avoid**:
```
{req.pattern}
```
{f'- **Solution**: {req.solution}' if req.solution else ''}

---
"""
    
    # Append to LESSONS.md
    with open(lessons_path, "a") as f:
        f.write(lesson_entry)
    
    # Also log to episodic memory
    services.cortex.add(
        f"Lesson learned from task {req.task_id}: {req.failure_reason}", 
        "episodic", 
        {"task_id": req.task_id, "action": "reflect", "reason": req.failure_reason}
    )
    
    return {"status": "success", "lesson_logged": True}

@app.get("/reflect/lessons")
def get_lessons():
    """Retrieve all lessons learned."""
    lessons_path = os.path.join(".core/memory", "LESSONS.md")
    if os.path.exists(lessons_path):
        with open(lessons_path, "r") as f:
            return {"content": f.read()}
    return {"content": "# Lessons Learned\n\nNo lessons recorded yet."}

# --- ENDPOINTS: FILES ---

@app.get("/fs/list")
async def list_files(path: str = ""):
    return await services.files.list_files(path)

@app.get("/fs/read")
async def read_file(path: str):
    return await services.files.read_file(path)

@app.post("/fs/write")
async def write_file(req: FileWriteRequest):
    return await services.files.write_file(req.path, req.content)

# --- ENDPOINTS: TASKS ---

@app.post("/tasks/create")
def create_task(req: TaskCreateRequest):
    task_id = services.tasks.create_task(req)
    # Log creation
    services.cortex.add(f"New Task Created: {req.text}", "episodic", {"task_id": task_id})
    return {"status": "success", "task_id": task_id}

@app.post("/tasks/claim")
def claim_task(req: TaskClaimRequest):
    res = services.tasks.claim_task(req)
    services.cortex.add(
        f"Agent '{req.agent_id}' claimed task {req.task_id}", 
        "episodic", 
        {"task_id": req.task_id, "agent": req.agent_id, "action": "claim"}
    )
    return res

@app.post("/tasks/update")
def update_task_endpoint(req: TaskUpdateRequest):
    res = services.tasks.update_task(req)
    # Log update
    msg = f"Task {req.task_id} updated to '{req.status}'"
    services.cortex.add(
        msg, "episodic", 
        {"task_id": req.task_id, "status": req.status, "action": "update"}
    )
    return res

@app.get("/tasks/list")
def list_tasks(status: Optional[str] = None, assignee: Optional[str] = None):
    return {"tasks": services.tasks.list_tasks(status, assignee)}

# --- ENDPOINTS: AGENTS ---
# (Simple in-memory registry for now, can be moved to state_manager later)
registered_agents: Dict[str, dict] = {}

@app.post("/agents/register")
def register_agent(req: AgentRegistration):
    registered_agents[req.agent_id] = {
        "agent_id": req.agent_id,
        "agent_type": req.agent_type,
        "capabilities": req.capabilities,
        "last_heartbeat": time.time(),
        "status": "online"
    }
    services.cortex.add(
        f"Agent '{req.agent_id}' registered", "episodic", 
        {"agent_id": req.agent_id, "action": "register"}
    )
    return {"status": "success"}

@app.post("/agents/heartbeat/{agent_id}")
def heartbeat(agent_id: str):
    if agent_id in registered_agents:
        registered_agents[agent_id]["last_heartbeat"] = time.time()
        registered_agents[agent_id]["status"] = "online"
        return {"status": "ok"}
    raise HTTPException(404, "Agent not registered")

@app.get("/agents/{agent_id}/next")
def get_next_task(agent_id: str):
    task = services.tasks.get_next_task(agent_id)
    if task:
        services.cortex.add(
            f"Agent '{agent_id}' auto-claimed task {task['id']}", 
            "episodic", 
            {"task_id": task["id"], "agent": agent_id}
        )
        return {"task": task, "claimed": True}
    return {"task": None}

@app.get("/")
def health_check():
    state = services.state.get_state() if services.state else "STARTUP"
    return {"status": "online", "state": state, "mode": "modular"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

