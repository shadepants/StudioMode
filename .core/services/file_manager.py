"""
File Manager Service
====================
Handles file system operations and workspace synchronization.
"""

import os
import hashlib
import time
import asyncio
import aiofiles
from typing import Dict, List, Optional
from fastapi import HTTPException

try:
    from ..config import WORKSPACE_DIR, DOCS_DIR
except ImportError:
    from config import WORKSPACE_DIR, DOCS_DIR
from .vector_store import VectorStore, FileHash

class FileManager:
    def __init__(self, vector_store: VectorStore):
        self.cortex = vector_store
        self.tbl_hashes = vector_store.tbl_hashes

    async def list_files(self, path: str = "") -> List[Dict]:
        """List files in workspace safely."""
        safe_base = os.path.abspath(WORKSPACE_DIR)
        target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
        
        if not os.path.commonpath([safe_base, target_path]) == safe_base:
            raise HTTPException(403, "Access Denied")
            
        if not os.path.exists(target_path): return []
        
        items = []
        for entry in os.scandir(target_path):
            items.append({
                "name": entry.name, 
                "type": "directory" if entry.is_dir() else "file", 
                "path": os.path.relpath(entry.path, WORKSPACE_DIR)
            })
        return items

    async def read_file(self, path: str) -> Dict[str, str]:
        """Read file content safely."""
        safe_base = os.path.abspath(WORKSPACE_DIR)
        target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
        
        if not os.path.commonpath([safe_base, target_path]) == safe_base:
            raise HTTPException(403, "Access Denied")
            
        if not os.path.exists(target_path) or not os.path.isfile(target_path):
            raise HTTPException(404, "File not found")
            
        async with aiofiles.open(target_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            
        return {"path": path, "content": content}

    async def write_file(self, path: str, content: str) -> Dict[str, str]:
        """Write file content safely."""
        safe_base = os.path.abspath(WORKSPACE_DIR)
        target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
        
        if not os.path.commonpath([safe_base, target_path]) == safe_base:
            raise HTTPException(403, "Access Denied")
            
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
            await f.write(content)
            
        return {"status": "success", "path": path}

    def sync_documentation(self):
        """Sync documentation files to vector store."""
        if not os.path.exists(DOCS_DIR): return
        
        try:
            if self.tbl_hashes:
                stored_hashes = {
                    row["file_path"]: row["content_hash"] 
                    for row in self.tbl_hashes.to_pandas().to_dict('records')
                }
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
                    self.cortex.add(content, "knowledge", meta)
                    self.tbl_hashes.add([
                        FileHash(file_path=full_path, content_hash=current_hash, last_updated=time.time())
                    ])
