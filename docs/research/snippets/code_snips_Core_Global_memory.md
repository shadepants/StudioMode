import os
import json
import lancedb
import pandas as pd
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# --- CONFIGURATION ---
DB_PATH = "./data/studio_global_memory"
TABLE_NAME = "master_index"
# [NEED: GEMINI_API_KEY] - Required for embedding generation

class SourceMetadata(BaseModel):
    notebook_id: str
    source_name: str
    tags: List[str]
    timestamp: str

class GlobalMemoryManager:
    """
    Manages the Tier 1 & Tier 2 logic: Local Vector Mirroring and Semantic Routing.
    """
    def __init__(self, uri: str = DB_PATH):
        self.db = lancedb.connect(uri)
        # Using a placeholder for embedding logic - easily replaced by Gemini/OpenAI embeddings
        self.table = self._get_or_create_table()

    def _get_or_create_table(self):
        # Schema includes the vector, raw text, and metadata for routing
        if TABLE_NAME in self.db.table_names():
            return self.db.open_table(TABLE_NAME)
        
        # Initial dummy data to define schema if table doesn't exist
        schema_data = [{
            "vector": [0.1] * 768, # Standard Gemini embedding dimension
            "text": "initialization anchor",
            "notebook_id": "root",
            "source_name": "system",
            "tags": ["system"],
            "timestamp": datetime.now().isoformat()
        }]
        return self.db.create_table(TABLE_NAME, data=schema_data)

    def add_to_index(self, text: str, meta: SourceMetadata):
        """Tier 1: Mirroring logic."""
        # TODO: Implement actual embedding call here
        vector = [0.1] * 768 
        
        self.table.add([{
            "vector": vector,
            "text": text,
            "notebook_id": meta.notebook_id,
            "source_name": meta.source_name,
            "tags": meta.tags,
            "timestamp": meta.timestamp
        }])

    def semantic_route(self, query: str, limit: int = 3) -> pd.DataFrame:
        """Tier 2: Finding which notebook IDs contain relevant context."""
        # Search across all notebooks mirrored in local memory
        results = self.table.search(query).limit(limit).to_pandas()
        return results[["notebook_id", "source_name", "text", "score"]]

class HeritageGenerator:
    """
    Tier 3: Generates the 'Heritage Document' to seed new notebooks.
    """
    @staticmethod
    def create_seed_doc(query: str, memory: GlobalMemoryManager) -> str:
        results = memory.semantic_route(query)
        
        header = f"# Heritage Context: {query}\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        header += "## Cross-Notebook Insights\n"
        
        body = ""
        for _, row in results.iterrows():
            body += f"### From Notebook: {row['notebook_id']} (Source: {row['source_name']})\n"
            body += f"> {row['text'][:500]}...\n\n"
            
        return header + body

# Example Initialization
if __name__ == "__main__":
    memory = GlobalMemoryManager()
    print("Global Memory Engine Initialized.")