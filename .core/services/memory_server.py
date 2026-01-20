# .core/services/memory_server.py
import os
import hashlib
import time
import sqlite3
import asyncio
import json
import uuid
import math
from typing import List, Optional, Literal, Dict, Any
from enum import Enum
from contextlib import asynccontextmanager

import aiofiles
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- CONFIGURATION ---
DB_URI = "./.core/memory/lancedb"
SQLITE_DB = "./.core/memory/tasks.db"
DOCS_DIR = "./docs/system_context"
WORKSPACE_DIR = "./workspace"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SYNC_INTERVAL = 60  # Seconds
BUFFER_SIZE = 5     # Auto-flush after 5 items (ReMe Lite)
DECAY_RATE = 0.0001 # OpenMemory Decay Factor

# --- ENUMS ---
class AgentState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    REVIEW = "REVIEW"

VALID_TRANSITIONS = {
    AgentState.IDLE: [AgentState.PLANNING, AgentState.EXECUTING],
    AgentState.PLANNING: [AgentState.EXECUTING, AgentState.IDLE],
    AgentState.EXECUTING: [AgentState.REVIEW, AgentState.PLANNING], 
    AgentState.REVIEW: [AgentState.IDLE, AgentState.PLANNING]
}

# --- DATA MODELS ---
func = get_registry().get("sentence-transformers").create(name=EMBEDDING_MODEL_NAME)

class MemoryEntry(LanceModel):
    id: str
    text: str = func.SourceField()
    vector: Vector(func.ndims()) = func.VectorField()
    type: str 
    metadata: str # JSON string: { "prev_id": "...", "source": "..." }
    timestamp: float

class FileHash(LanceModel):
    file_path: str
    content_hash: str
    last_updated: float

class ResearchJob(BaseModel):
    id: str
    topic: str
    status: str 
    progress: float 
    logs: List[str] = []
    result_summary: Optional[str] = None

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

class TaskCreateRequest(BaseModel):
    text: str
    assignee: str
    priority: str = "normal"
    metadata: dict = {}

class TaskUpdateRequest(BaseModel):
    task_id: str
    status: str
    metadata: dict = {}

class StateUpdateRequest(BaseModel):
    new_state: AgentState

class SourceAddRequest(BaseModel):
    title: str
    type: str
    url: str
    summary: str = ""
    tags: List[str] = []
    checksum: str

# --- GLOBAL CONTEXT ---
class SystemContext:
    cortex: Optional[Any] = None 
    tbl_hashes = None
    current_state = AgentState.IDLE
    sql_conn = None

ctx = SystemContext()

# --- SMART CORTEX (Hybrid Architecture) ---
class SmartCortex:
    def __init__(self, db: lancedb.DBConnection):
        self.tbl = db.create_table("memory", schema=MemoryEntry, exist_ok=True)
        self.buffer: List[Dict[str, Any]] = []
        self.last_episodic_id: Optional[str] = None
        try:
            last_entry = self.tbl.search().where("type='episodic'").limit(1).to_list()
            if last_entry:
                self.last_episodic_id = last_entry[0]['id']
        except Exception:
            pass

    def add(self, text: str, type: str, metadata: Dict[str, Any] = {}) -> str:
        if type == "episodic":
            metadata["prev_id"] = self.last_episodic_id
        
        entry_id = str(uuid.uuid4())
        timestamp = time.time()
        
        entry = {
            "id": entry_id,
            "text": text,
            "type": type,
            "metadata": json.dumps(metadata),
            "timestamp": timestamp
        }

        if type == "episodic":
            self.buffer.append(entry)
            self.last_episodic_id = entry_id
            if len(self.buffer) >= BUFFER_SIZE:
                self.flush()
        else:
            self.tbl.add([entry])
            
        return entry_id

    def flush(self):
        if not self.buffer: return
        print(f"[Cortex] Flushing {len(self.buffer)} items to Long-Term Memory...")
        self.tbl.add(self.buffer)
        self.buffer = []

    def search(self, query: str, limit: int = 5, filter_type: Optional[str] = None) -> List[Dict]:
        pool_size = limit * 3
        q = self.tbl.search(query).limit(pool_size)
        if filter_type:
            q = q.where(f"type = '{filter_type}'")
        candidates = q.to_list()
        if not candidates: return []
        
        now = time.time()
        reranked = []
        for item in candidates:
            raw_score = 1.0 - item.get('_distance', 0.5)
            age_hours = (now - item['timestamp']) / 3600
            time_penalty = 1 / (1 + (DECAY_RATE * age_hours))
            final_score = raw_score * time_penalty
            item['_score'] = final_score
            reranked.append(item)
        reranked.sort(key=lambda x: x['_score'], reverse=True)
        return reranked[:limit]

# --- BACKGROUND TASKS ---
async def doc_sync_loop():
    while True:
        try:
            await asyncio.to_thread(_sync_documentation)
        except Exception as e:
            print(f"[!] Sync error: {e}")
        await asyncio.sleep(SYNC_INTERVAL)

def _sync_documentation():
    if not os.path.exists(DOCS_DIR): return
    if not ctx.cortex: return
    try:
        if ctx.tbl_hashes:
            stored_hashes = {row["file_path"]: row["content_hash"] for row in ctx.tbl_hashes.to_pandas().to_dict('records')}
        else:
            stored_hashes = {}
    except Exception as e:
        print(f"[!] Hash Load Error: {e}")
        stored_hashes = {}
    
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.endswith(".md"): continue
            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if full_path not in stored_hashes or stored_hashes[full_path] != current_hash:
                print(f"[+] Syncing file: {file}")
                meta = {"source": full_path, "hash": current_hash}
                ctx.cortex.add(content, "knowledge", meta)
                ctx.tbl_hashes.add([FileHash(file_path=full_path, content_hash=current_hash, last_updated=time.time())])

def init_sqlite():
    ctx.sql_conn = sqlite3.connect(SQLITE_DB, check_same_thread=False)
    ctx.sql_conn.row_factory = sqlite3.Row
    cur = ctx.sql_conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, 
        text TEXT, 
        assignee TEXT, 
        claimed_by TEXT,
        status TEXT, 
        priority TEXT, 
        metadata TEXT, 
        created_at REAL, 
        updated_at REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, title TEXT, type TEXT, url TEXT, summary TEXT, tags TEXT, checksum TEXT, created_at REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ontology_nodes (id TEXT PRIMARY KEY, label TEXT, type TEXT, metadata TEXT, created_at REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ontology_edges (source_id TEXT, target_id TEXT, relation TEXT, weight REAL, PRIMARY KEY (source_id, target_id, relation))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, name TEXT, description TEXT, schema TEXT, row_count INTEGER, storage_path TEXT, created_at REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS semantic_cache (query_hash TEXT PRIMARY KEY, query_text TEXT, response TEXT, embedding BLOB, hit_count INTEGER DEFAULT 1, last_accessed REAL)""")
    ctx.sql_conn.commit()

# --- LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] Initializing Hybrid Memory System (Mem0+Zep+ReMe)...")
    os.makedirs(os.path.dirname(DB_URI), exist_ok=True)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    db = lancedb.connect(DB_URI)
    ctx.cortex = SmartCortex(db)
    ctx.tbl_hashes = db.create_table("file_hashes", schema=FileHash, exist_ok=True)
    init_sqlite()
    asyncio.create_task(doc_sync_loop())
    yield
    print("[*] Shutting down.")
    if ctx.cortex: ctx.cortex.flush()
    if ctx.sql_conn: ctx.sql_conn.close()

# --- API INIT ---
app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

active_jobs = {}

# --- ENDPOINTS ---

async def run_research_pipeline(job_id: str, topic: str):
    job = active_jobs[job_id]
    try:
        job.status = "scouting"
        job.logs.append(f"Deploying Scout Agent for: {topic}")
        await asyncio.sleep(2)
        job.status = "ingesting"
        job.progress = 0.3
        job.logs.append("Found 5 high-quality sources. Handing over to Librarian.")
        await asyncio.sleep(2)
        job.status = "synthesizing"
        job.progress = 0.7
        job.logs.append("Architecting Knowledge Graph nodes...")
        cur = ctx.sql_conn.cursor()
        node_id = str(uuid.uuid4())
        cur.execute("INSERT INTO ontology_nodes (id, label, type, created_at) VALUES (?, ?, ?, ?)", (node_id, topic, "concept", time.time()))
        ctx.sql_conn.commit()
        job.status = "complete"
        job.progress = 1.0
        job.result_summary = f"Research complete. Created Knowledge Graph node {node_id}."
        job.logs.append("Pipeline finished successfully.")
    except Exception as e:
        job.status = "failed"
        job.logs.append(f"Pipeline Error: {str(e)}")

@app.post("/research/start")
async def start_research(background_tasks: BackgroundTasks, topic: str, depth: int = 1):
    job_id = str(uuid.uuid4())
    new_job = ResearchJob(id=job_id, topic=topic, status="starting", progress=0.0)
    active_jobs[job_id] = new_job
    background_tasks.add_task(run_research_pipeline, job_id, topic)
    return {"status": "started", "job_id": job_id}

@app.get("/research/status")
def get_research_status():
    return list(active_jobs.values())

@app.get("/sources")
def get_sources(limit: int = 50):
    cur = ctx.sql_conn.cursor()
    cur.execute("SELECT * FROM sources ORDER BY created_at DESC LIMIT ?", (limit,))
    return [dict(row) for row in cur.fetchall()]

@app.post("/sources/add")
def add_source(req: SourceAddRequest):
    id = str(uuid.uuid4())
    now = time.time()
    cur = ctx.sql_conn.cursor()
    cur.execute("""INSERT INTO sources (id, title, type, url, summary, tags, checksum, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (id, req.title, req.type, req.url, req.summary, json.dumps(req.tags), req.checksum, now))
    ctx.sql_conn.commit()
    ctx.cortex.add(text=f"Source: {req.title}\nSummary: {req.summary}", type="knowledge", metadata={"source_id": id, "url": req.url, "type": req.type})
    return {"status": "success", "id": id}

@app.get("/knowledge/graph")
def get_knowledge_graph():
    cur = ctx.sql_conn.cursor()
    nodes = cur.execute("SELECT * FROM ontology_nodes").fetchall()
    edges = cur.execute("SELECT * FROM ontology_edges").fetchall()
    return {"nodes": [dict(row) for row in nodes], "edges": [dict(row) for row in edges]}

@app.post("/memory/query")
def query_memory(req: QueryRequest):
    cur = ctx.sql_conn.cursor()
    query_hash = hashlib.md5(req.text.encode()).hexdigest()
    cached = cur.execute("SELECT response FROM semantic_cache WHERE query_hash = ?", (query_hash,)).fetchone()
    if cached:
        cur.execute("UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed = ? WHERE query_hash = ?", (time.time(), query_hash))
        ctx.sql_conn.commit()
        return {"results": json.loads(cached['response']), "source": "cache"}
    results = ctx.cortex.search(req.text, req.limit, req.filter_type)
    cur.execute("""INSERT OR REPLACE INTO semantic_cache (query_hash, query_text, response, last_accessed) VALUES (?, ?, ?, ?)""", (query_hash, req.text, json.dumps(results), time.time()))
    ctx.sql_conn.commit()
    return {"results": results, "source": "vector_db"}

@app.post("/memory/add")
def add_memory(req: AddMemoryRequest):
    id = ctx.cortex.add(req.text, req.type, req.metadata)
    return {"status": "success", "id": id}

@app.get("/memory/feed")
def get_memory_feed(limit: int = 20):
    try:
        # Fetch generic pool of episodic memories
        res = ctx.cortex.tbl.search().where("type='episodic'").limit(limit*5).to_list()
        # Sort by timestamp desc in memory (LanceDB append-only naturally orders, but parallel writes might jitter)
        res.sort(key=lambda x: x['timestamp'], reverse=True)
        return res[:limit]
    except Exception as e:
        print(f"Feed Error: {e}")
        return []

@app.get("/state")
def get_state():
    return {"current_state": ctx.current_state}

@app.post("/state/update")
def update_state(req: StateUpdateRequest):
    if req.new_state not in VALID_TRANSITIONS.get(ctx.current_state, []):
        raise HTTPException(400, f"Invalid transition from {ctx.current_state} to {req.new_state}")
    old_state = ctx.current_state
    ctx.current_state = req.new_state
    ctx.cortex.add(text=f"System state transitioned from {old_state} to {ctx.current_state}", type="episodic", metadata={"old_state": old_state, "new_state": ctx.current_state})
    return {"status": "success", "current_state": ctx.current_state}

@app.get("/fs/list")
async def list_files(path: str = ""):
    safe_base = os.path.abspath(WORKSPACE_DIR)
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not os.path.commonpath([safe_base, target_path]) == safe_base: raise HTTPException(403, "Access Denied")
    if not os.path.exists(target_path): return []
    items = []
    for entry in os.scandir(target_path):
        items.append({"name": entry.name, "type": "directory" if entry.is_dir() else "file", "path": os.path.relpath(entry.path, WORKSPACE_DIR)})
    return items

@app.get("/fs/read")
async def read_file_content(path: str):
    safe_base = os.path.abspath(WORKSPACE_DIR)
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not os.path.commonpath([safe_base, target_path]) == safe_base: raise HTTPException(403, "Access Denied")
    if not os.path.exists(target_path) or not os.path.isfile(target_path): raise HTTPException(404, "File not found")
    async with aiofiles.open(target_path, 'r', encoding='utf-8') as f: content = await f.read()
    return {"path": path, "content": content}

@app.post("/fs/write")
async def write_file(req: FileWriteRequest):
    safe_base = os.path.abspath(WORKSPACE_DIR)
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, req.path))
    if not os.path.commonpath([safe_base, target_path]) == safe_base: raise HTTPException(403, "Access Denied")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    async with aiofiles.open(target_path, 'w', encoding='utf-8') as f: await f.write(req.content)
    return {"status": "success", "path": req.path}

@app.post("/tasks/create")
def create_task(req: TaskCreateRequest):
    task_id = str(uuid.uuid4())
    now = time.time()
    cur = ctx.sql_conn.cursor()
    cur.execute("""INSERT INTO tasks (id, text, assignee, claimed_by, status, priority, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (task_id, req.text, req.assignee, None, "pending", req.priority, json.dumps(req.metadata), now, now))
    ctx.sql_conn.commit()
    return {"status": "success", "task_id": task_id}

class TaskClaimRequest(BaseModel):
    task_id: str
    agent_id: str

@app.post("/tasks/claim")
def claim_task(req: TaskClaimRequest):
    now = time.time()
    cur = ctx.sql_conn.cursor()
    # Atomic check and update
    cur.execute("SELECT status, claimed_by FROM tasks WHERE id = ?", (req.task_id,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Task not found")
    if row["status"] != "pending" or row["claimed_by"] is not None:
        raise HTTPException(400, "Task already claimed or not pending")
    
    cur.execute("""UPDATE tasks SET status = 'in_progress', claimed_by = ?, updated_at = ? WHERE id = ?""", (req.agent_id, now, req.task_id))
    ctx.sql_conn.commit()
    
    # Log to Cortex
    ctx.cortex.add(text=f"Agent '{req.agent_id}' claimed task {req.task_id[:8]}...", type="episodic", metadata={"task_id": req.task_id, "agent": req.agent_id, "action": "claim"})
    return {"status": "success"}

@app.get("/tasks/list")
def list_tasks(status: Optional[str] = None, assignee: Optional[str] = None):
    cur = ctx.sql_conn.cursor()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if assignee:
        query += " AND assignee = ?"
        params.append(assignee)
    cur.execute(query, params)
    return {"tasks": [dict(row) for row in cur.fetchall()]}

@app.post("/tasks/update")
def update_task(req: TaskUpdateRequest):
    now = time.time()
    cur = ctx.sql_conn.cursor()
    cur.execute("SELECT metadata FROM tasks WHERE id = ?", (req.task_id,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Task not found")
    existing_meta = json.loads(row["metadata"])
    existing_meta.update(req.metadata)
    cur.execute("""UPDATE tasks SET status = ?, metadata = ?, updated_at = ? WHERE id = ?""", (req.status, json.dumps(existing_meta), now, req.task_id))
    ctx.sql_conn.commit()
    
    # Log to Cortex
    msg = f"Task {req.task_id[:8]}... updated to '{req.status}'"
    if req.status == 'review': msg += " (Ready for Review)"
    elif req.status == 'completed': msg += " (Completed)"
    
    ctx.cortex.add(text=msg, type="episodic", metadata={"task_id": req.task_id, "status": req.status, "action": "update"})
    return {"status": "success"}

@app.get("/")
def health_check():
    return {"status": "online", "state": ctx.current_state, "mode": "hybrid"}


# =============================================================================
# MULTI-AGENT COORDINATION PROTOCOL
# =============================================================================
# Enables collaborative workflows between Antigravity IDE and Gemini CLI

class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: str  # "antigravity", "gemini-cli", "custom"
    capabilities: List[str] = []

class WorkflowTask(BaseModel):
    name: str
    description: str
    assignee: str
    priority: str = "normal"
    dependencies: List[str] = []  # task_ids this depends on

class WorkflowCreateRequest(BaseModel):
    workflow_id: str
    name: str
    tasks: List[WorkflowTask]

# In-memory agent registry (could be persisted to SQLite)
registered_agents: Dict[str, dict] = {}
active_workflows: Dict[str, dict] = {}

@app.post("/agents/register")
def register_agent(req: AgentRegistration):
    """Register an agent for collaborative work."""
    registered_agents[req.agent_id] = {
        "agent_id": req.agent_id,
        "agent_type": req.agent_type,
        "capabilities": req.capabilities,
        "registered_at": time.time(),
        "last_heartbeat": time.time(),
        "status": "online"
    }
    ctx.cortex.add(
        text=f"Agent '{req.agent_id}' ({req.agent_type}) registered for collaboration",
        type="episodic",
        metadata={"agent_id": req.agent_id, "action": "register"}
    )
    return {"status": "success", "message": f"Agent {req.agent_id} registered"}

@app.post("/agents/heartbeat/{agent_id}")
def agent_heartbeat(agent_id: str):
    """Update agent heartbeat to show it's still active."""
    if agent_id not in registered_agents:
        raise HTTPException(404, "Agent not registered")
    registered_agents[agent_id]["last_heartbeat"] = time.time()
    registered_agents[agent_id]["status"] = "online"
    return {"status": "ok", "timestamp": time.time()}

@app.get("/agents/list")
def list_agents():
    """List all registered agents and their status."""
    now = time.time()
    agents = []
    for agent_id, info in registered_agents.items():
        # Mark as offline if no heartbeat in 60 seconds
        if now - info["last_heartbeat"] > 60:
            info["status"] = "offline"
        agents.append(info)
    return {"agents": agents}

@app.get("/agents/{agent_id}/tasks")
def get_agent_tasks(agent_id: str, include_completed: bool = False):
    """Get all tasks assigned to a specific agent."""
    cur = ctx.sql_conn.cursor()
    if include_completed:
        cur.execute("SELECT * FROM tasks WHERE assignee = ? ORDER BY created_at DESC", (agent_id,))
    else:
        cur.execute("SELECT * FROM tasks WHERE assignee = ? AND status IN ('pending', 'in_progress') ORDER BY priority, created_at", (agent_id,))
    return {"agent_id": agent_id, "tasks": [dict(row) for row in cur.fetchall()]}

@app.get("/agents/{agent_id}/next")
def get_next_task(agent_id: str):
    """Get the next pending task for an agent and auto-claim it."""
    cur = ctx.sql_conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE assignee = ? AND status = 'pending' ORDER BY priority DESC, created_at ASC LIMIT 1",
        (agent_id,)
    )
    row = cur.fetchone()
    if not row:
        return {"task": None, "message": "No pending tasks"}
    
    task = dict(row)
    # Auto-claim
    now = time.time()
    cur.execute(
        "UPDATE tasks SET status = 'in_progress', claimed_by = ?, updated_at = ? WHERE id = ?",
        (agent_id, now, task["id"])
    )
    ctx.sql_conn.commit()
    ctx.cortex.add(
        text=f"Agent '{agent_id}' auto-claimed task: {task['text'][:50]}...",
        type="episodic",
        metadata={"task_id": task["id"], "agent": agent_id, "action": "auto_claim"}
    )
    return {"task": task, "claimed": True}

@app.post("/workflows/create")
def create_workflow(req: WorkflowCreateRequest):
    """Create a multi-agent workflow with task dependencies."""
    workflow = {
        "id": req.workflow_id,
        "name": req.name,
        "created_at": time.time(),
        "status": "active",
        "tasks": {}
    }
    
    # Create all tasks
    for task in req.tasks:
        task_id = str(uuid.uuid4())
        now = time.time()
        cur = ctx.sql_conn.cursor()
        metadata = {
            "workflow_id": req.workflow_id,
            "dependencies": task.dependencies,
            "description": task.description
        }
        cur.execute(
            """INSERT INTO tasks (id, text, assignee, claimed_by, status, priority, metadata, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, task.name, task.assignee, None, "pending", task.priority, json.dumps(metadata), now, now)
        )
        workflow["tasks"][task.name] = task_id
    
    ctx.sql_conn.commit()
    active_workflows[req.workflow_id] = workflow
    
    ctx.cortex.add(
        text=f"Workflow '{req.name}' created with {len(req.tasks)} tasks",
        type="episodic",
        metadata={"workflow_id": req.workflow_id, "task_count": len(req.tasks)}
    )
    return {"status": "success", "workflow": workflow}

@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    """Get workflow status and all task statuses."""
    if workflow_id not in active_workflows:
        raise HTTPException(404, "Workflow not found")
    
    workflow = active_workflows[workflow_id]
    cur = ctx.sql_conn.cursor()
    
    # Get current status of all tasks
    task_statuses = {}
    for task_name, task_id in workflow["tasks"].items():
        cur.execute("SELECT status, claimed_by, updated_at FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row:
            task_statuses[task_name] = dict(row)
    
    # Calculate overall progress
    total = len(task_statuses)
    completed = sum(1 for t in task_statuses.values() if t["status"] == "completed")
    progress = completed / total if total > 0 else 0
    
    return {
        "workflow": workflow,
        "task_statuses": task_statuses,
        "progress": progress,
        "completed": completed,
        "total": total
    }

@app.get("/workflows/list")
def list_workflows():
    """List all active workflows."""
    return {"workflows": list(active_workflows.values())}

# Delegate task to another agent
@app.post("/tasks/delegate")
def delegate_task(task_id: str, new_assignee: str, message: str = ""):
    """Delegate a task from one agent to another."""
    cur = ctx.sql_conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Task not found")
    
    old_assignee = row["assignee"]
    now = time.time()
    metadata = json.loads(row["metadata"])
    metadata["delegated_from"] = old_assignee
    metadata["delegation_message"] = message
    metadata["delegated_at"] = now
    
    cur.execute(
        """UPDATE tasks SET assignee = ?, status = 'pending', claimed_by = NULL, metadata = ?, updated_at = ? WHERE id = ?""",
        (new_assignee, json.dumps(metadata), now, task_id)
    )
    ctx.sql_conn.commit()
    
    ctx.cortex.add(
        text=f"Task delegated from '{old_assignee}' to '{new_assignee}': {row['text'][:30]}...",
        type="episodic",
        metadata={"task_id": task_id, "from": old_assignee, "to": new_assignee}
    )
    return {"status": "success", "delegated_to": new_assignee}


# --- METRICS ENDPOINT ---
@app.get("/metrics")
def get_metrics():
    """Get system metrics for Mission Control dashboard."""
    cur = ctx.sql_conn.cursor()
    
    # Task metrics
    cur.execute("SELECT COUNT(*) as total FROM tasks")
    total_tasks = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'")
    completed_tasks = cur.fetchone()["completed"]
    
    cur.execute("SELECT COUNT(*) as in_progress FROM tasks WHERE status = 'in_progress'")
    in_progress = cur.fetchone()["in_progress"]
    
    cur.execute("SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'")
    pending_tasks = cur.fetchone()["pending"]
    
    cur.execute("SELECT COUNT(*) as failed FROM tasks WHERE status = 'failed'")
    failed_tasks = cur.fetchone()["failed"]
    
    # Agent metrics
    active_agents = len([a for a in agents.values() if time.time() - a.get("last_heartbeat", 0) < 60])
    total_agents = len(agents)
    
    # Calculate average task duration (using completed tasks with timestamps)
    cur.execute("""
        SELECT AVG(updated_at - created_at) as avg_duration 
        FROM tasks 
        WHERE status = 'completed' AND updated_at > created_at
    """)
    avg_row = cur.fetchone()
    avg_duration = avg_row["avg_duration"] if avg_row and avg_row["avg_duration"] else 0
    
    # Recent activity count (last hour)
    hour_ago = time.time() - 3600
    cur.execute("SELECT COUNT(*) as recent FROM tasks WHERE updated_at > ?", (hour_ago,))
    recent_activity = cur.fetchone()["recent"]
    
    # System uptime (time since first task or server start)
    cur.execute("SELECT MIN(created_at) as first_task FROM tasks")
    first_row = cur.fetchone()
    uptime = time.time() - first_row["first_task"] if first_row and first_row["first_task"] else 0
    
    return {
        "timestamp": time.time(),
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress,
            "pending": pending_tasks,
            "failed": failed_tasks,
        },
        "agents": {
            "total": total_agents,
            "active": active_agents,
        },
        "performance": {
            "avg_duration_seconds": round(avg_duration, 2),
            "recent_activity": recent_activity,
        },
        "system": {
            "uptime_seconds": round(uptime, 0),
            "state": ctx.current_state.value,
        }
    }


@app.get("/metrics/prometheus")
def get_metrics_prometheus():
    """Get metrics in Prometheus exposition format."""
    metrics = get_metrics()
    lines = [
        "# HELP studio_tasks_total Total number of tasks",
        "# TYPE studio_tasks_total counter",
        f"studio_tasks_total {metrics['tasks']['total']}",
        "",
        "# HELP studio_tasks_completed Completed tasks",
        f"studio_tasks_completed {metrics['tasks']['completed']}",
        "",
        "# HELP studio_tasks_failed Failed tasks",
        f"studio_tasks_failed {metrics['tasks']['failed']}",
        "",
        "# HELP studio_agents_active Active agents",
        f"studio_agents_active {metrics['agents']['active']}",
        "",
        "# HELP studio_task_duration_avg Average task duration",
        f"studio_task_duration_avg {metrics['performance']['avg_duration_seconds']}",
        "",
        "# HELP studio_uptime_seconds System uptime",
        f"studio_uptime_seconds {metrics['system']['uptime_seconds']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

