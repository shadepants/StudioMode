"""
State Manager Service
=====================
Manages the global state of the Hive loop.
"""

from typing import Dict, List, Any
from pydantic import BaseModel
from fastapi import HTTPException
try:
    from ..models import AgentState, VALID_TRANSITIONS
except ImportError:
    from models import AgentState, VALID_TRANSITIONS
from .vector_store import VectorStore

class StateUpdateRequest(BaseModel):
    new_state: AgentState

class StateManager:
    def __init__(self, vector_store: VectorStore):
        self.current_state = AgentState.IDLE
        self.cortex = vector_store

    def get_state(self) -> AgentState:
        return self.current_state

    def update_state(self, req: StateUpdateRequest) -> Dict[str, Any]:
        """Update system state with transition validation."""
        allowed = VALID_TRANSITIONS.get(self.current_state, [])
        if req.new_state not in allowed:
            # Special case: Allow reset to IDLE from anywhere if needed (optional safety)
            if req.new_state == AgentState.IDLE:
                pass
            else:
                raise HTTPException(400, f"Invalid transition from {self.current_state} to {req.new_state}")
        
        old_state = self.current_state
        self.current_state = req.new_state
        
        # Log transition to episodic memory
        self.cortex.add(
            text=f"System state transitioned from {old_state} to {self.current_state}", 
            type="episodic", 
            metadata={"old_state": old_state, "new_state": self.current_state}
        )
        
        return {"status": "success", "current_state": self.current_state}
