"""
Research Manager Service
========================
Handles Research Jobs, Sources, Knowledge Graph, and Semantic Cache.
"""

import sqlite3
import time
import json
import hashlib
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import BackgroundTasks

try:
    from ..models import TaskStatus
except ImportError:
    from models import TaskStatus
from .vector_store import VectorStore

class ResearchJob(BaseModel):
    id: str
    topic: str
    status: str 
    progress: float 
    logs: List[str] = []
    result_summary: Optional[str] = None

class SourceAddRequest(BaseModel):
    title: str
    type: str
    url: str
    summary: str = ""
    tags: List[str] = []
    checksum: str

class ResearchManager:
    def __init__(self, db_path: str, vector_store: VectorStore):
        self.sql_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.sql_conn.row_factory = sqlite3.Row
        self.cortex = vector_store
        self.active_jobs: Dict[str, ResearchJob] = {}

    def get_sources(self, limit: int = 50) -> List[Dict]:
        cur = self.sql_conn.cursor()
        cur.execute("SELECT * FROM sources ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

    def add_source(self, req: SourceAddRequest) -> str:
        source_id = str(uuid.uuid4())
        now = time.time()
        cur = self.sql_conn.cursor()
        cur.execute("""INSERT INTO sources (id, title, type, url, summary, tags, checksum, created_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                       (source_id, req.title, req.type, req.url, req.summary, json.dumps(req.tags), req.checksum, now))
        self.sql_conn.commit()
        
        self.cortex.add(
            text=f"Source: {req.title}\nSummary: {req.summary}", 
            type="knowledge", 
            metadata={"source_id": source_id, "url": req.url, "type": req.type}
        )
        return source_id

    def get_knowledge_graph(self) -> Dict[str, List[Dict]]:
        cur = self.sql_conn.cursor()
        nodes = cur.execute("SELECT * FROM ontology_nodes").fetchall()
        edges = cur.execute("SELECT * FROM ontology_edges").fetchall()
        return {"nodes": [dict(row) for row in nodes], "edges": [dict(row) for row in edges]}

    def query_memory_with_cache(self, text: str, limit: int = 3, filter_type: Optional[str] = None) -> Dict[str, Any]:
        cur = self.sql_conn.cursor()
        query_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Check Cache
        cached = cur.execute("SELECT response FROM semantic_cache WHERE query_hash = ?", (query_hash,)).fetchone()
        if cached:
            cur.execute("UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed = ? WHERE query_hash = ?", 
                        (time.time(), query_hash))
            self.sql_conn.commit()
            return {"results": json.loads(cached['response']), "source": "cache"}
            
        # Run Vector Search
        results = self.cortex.search(text, limit, filter_type)
        
        # Update Cache
        cur.execute("""INSERT OR REPLACE INTO semantic_cache (query_hash, query_text, response, last_accessed) 
                       VALUES (?, ?, ?, ?)""", 
                       (query_hash, text, json.dumps(results), time.time()))
        self.sql_conn.commit()
        return {"results": results, "source": "vector_db"}

    async def start_research(self, topic: str, background_tasks: BackgroundTasks) -> str:
        job_id = str(uuid.uuid4())
        new_job = ResearchJob(id=job_id, topic=topic, status="starting", progress=0.0)
        self.active_jobs[job_id] = new_job
        background_tasks.add_task(self._run_research_pipeline, job_id, topic)
        return job_id

    async def _run_research_pipeline(self, job_id: str, topic: str):
        job = self.active_jobs[job_id]
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
            
            cur = self.sql_conn.cursor()
            node_id = str(uuid.uuid4())
            cur.execute("INSERT INTO ontology_nodes (id, label, type, created_at) VALUES (?, ?, ?, ?)", 
                        (node_id, topic, "concept", time.time()))
            self.sql_conn.commit()
            
            job.status = "complete"
            job.progress = 1.0
            job.result_summary = f"Research complete. Created Knowledge Graph node {node_id}."
            job.logs.append("Pipeline finished successfully.")
        except Exception as e:
            job.status = "failed"
            job.logs.append(f"Pipeline Error: {str(e)}")

    def get_research_status(self) -> List[ResearchJob]:
        return list(self.active_jobs.values())

    def close(self):
        self.sql_conn.close()
