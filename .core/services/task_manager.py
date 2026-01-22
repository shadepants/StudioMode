"""
Task Manager Service
====================
Handles task lifecycle, SQLite persistence, and assignment logic.
"""

import sqlite3
import time
import json
import uuid
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import HTTPException
try:
    from ..models import TaskStatus
except ImportError:
    from models import TaskStatus

class TaskCreateRequest(BaseModel):
    text: str
    assignee: str
    priority: str = "normal"
    metadata: dict = {}

class TaskUpdateRequest(BaseModel):
    task_id: str
    status: str
    metadata: dict = {}

class TaskClaimRequest(BaseModel):
    task_id: str
    agent_id: str

class TaskManager:
    def __init__(self, db_path: str):
        self.sql_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.sql_conn.row_factory = sqlite3.Row
        self._init_schema()
        
    def _init_schema(self):
        cur = self.sql_conn.cursor()
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
        # Additional tables can be moved here if needed
        cur.execute("""CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, title TEXT, type TEXT, url TEXT, summary TEXT, tags TEXT, checksum TEXT, created_at REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS ontology_nodes (id TEXT PRIMARY KEY, label TEXT, type TEXT, metadata TEXT, created_at REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS ontology_edges (source_id TEXT, target_id TEXT, relation TEXT, weight REAL, PRIMARY KEY (source_id, target_id, relation))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, name TEXT, description TEXT, schema TEXT, row_count INTEGER, storage_path TEXT, created_at REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS semantic_cache (query_hash TEXT PRIMARY KEY, query_text TEXT, response TEXT, embedding BLOB, hit_count INTEGER DEFAULT 1, last_accessed REAL)""")
        self.sql_conn.commit()

    def create_task(self, req: TaskCreateRequest) -> str:
        task_id = str(uuid.uuid4())
        now = time.time()
        cur = self.sql_conn.cursor()
        cur.execute("""INSERT INTO tasks (id, text, assignee, claimed_by, status, priority, metadata, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                       (task_id, req.text, req.assignee, None, "pending", req.priority, json.dumps(req.metadata), now, now))
        self.sql_conn.commit()
        return task_id

    def list_tasks(self, status: Optional[str] = None, assignee: Optional[str] = None) -> List[Dict]:
        cur = self.sql_conn.cursor()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)
        # Order by priority (high/normal/low) could be refined, but for now just created_at
        query += " ORDER BY created_at ASC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def claim_task(self, req: TaskClaimRequest) -> Dict[str, str]:
        now = time.time()
        cur = self.sql_conn.cursor()
        cur.execute("SELECT status, claimed_by FROM tasks WHERE id = ?", (req.task_id,))
        row = cur.fetchone()
        
        if not row: 
            raise HTTPException(404, "Task not found")
        if row["status"] != "pending" or row["claimed_by"] is not None:
            raise HTTPException(400, "Task already claimed or not pending")
        
        cur.execute("""UPDATE tasks SET status = 'in_progress', claimed_by = ?, updated_at = ? WHERE id = ?""", 
                    (req.agent_id, now, req.task_id))
        self.sql_conn.commit()
        return {"status": "success"}

    def update_task(self, req: TaskUpdateRequest) -> Dict[str, str]:
        now = time.time()
        cur = self.sql_conn.cursor()
        cur.execute("SELECT metadata FROM tasks WHERE id = ?", (req.task_id,))
        row = cur.fetchone()
        if not row: 
            raise HTTPException(404, "Task not found")
        
        existing_meta = json.loads(row["metadata"])
        existing_meta.update(req.metadata)
        
        cur.execute("""UPDATE tasks SET status = ?, metadata = ?, updated_at = ? WHERE id = ?""", 
                    (req.status, json.dumps(existing_meta), now, req.task_id))
        self.sql_conn.commit()
        return {"status": "success"}

    def get_next_task(self, agent_id: str) -> Optional[Dict]:
        cur = self.sql_conn.cursor()
        # Simple heuristic: Pending tasks assigned to agent
        cur.execute(
            "SELECT * FROM tasks WHERE assignee = ? AND status = 'pending' ORDER BY created_at ASC LIMIT 1",
            (agent_id,)
        )
        row = cur.fetchone()
        if not row: return None
        
        task = dict(row)
        # Auto-claim
        now = time.time()
        cur.execute(
            "UPDATE tasks SET status = 'in_progress', claimed_by = ?, updated_at = ? WHERE id = ?",
            (agent_id, now, task["id"])
        )
        self.sql_conn.commit()
        return task

    def close(self):
        self.sql_conn.close()
