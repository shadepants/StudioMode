"""
Vector Store Service (SmartCortex)
==================================
Encapsulates LanceDB vector storage and hybrid memory logic.
"""

import time
import json
import uuid
from typing import List, Dict, Any, Optional

import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

try:
    from ..config import (
        EMBEDDING_MODEL_NAME, 
        BUFFER_SIZE, 
        DECAY_RATE,
        DB_URI
    )
except ImportError:
    from config import (
        EMBEDDING_MODEL_NAME, 
        BUFFER_SIZE, 
        DECAY_RATE,
        DB_URI
    )

# --- MODELS ---
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

# --- SERVICE ---
class VectorStore:
    def __init__(self, db_path: str):
        self.db = lancedb.connect(db_path)
        self.tbl = self.db.create_table("memory", schema=MemoryEntry, exist_ok=True)
        self.tbl_hashes = self.db.create_table("file_hashes", schema=FileHash, exist_ok=True)
        self.buffer: List[Dict[str, Any]] = []
        self.last_episodic_id: Optional[str] = None
        
        # Restore last state
        try:
            last_entry = self.tbl.search().where("type='episodic'").limit(1).to_list()
            if last_entry:
                self.last_episodic_id = last_entry[0]['id']
        except Exception:
            pass

    def add(self, text: str, type: str, metadata: Dict[str, Any] = {}) -> str:
        """Add entry to memory."""
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
        """Flush buffer to long-term memory."""
        if not self.buffer: return
        print(f"[Cortex] Flushing {len(self.buffer)} items to Long-Term Memory...")
        self.tbl.add(self.buffer)
        self.buffer = []

    def search(self, query: str, limit: int = 5, filter_type: Optional[str] = None) -> List[Dict]:
        """Hybrid search with time decay."""
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
    
    def get_feed(self, limit: int = 20) -> List[Dict]:
        """Get recent episodic memory feed."""
        try:
            res = self.tbl.search().where("type='episodic'").limit(limit*5).to_list()
            res.sort(key=lambda x: x['timestamp'], reverse=True)
            return res[:limit]
        except Exception as e:
            print(f"Feed Error: {e}")
            return []
