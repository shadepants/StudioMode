"""
Core State Models
=================
Shared enums and state definitions for the agent system.
"""

from enum import Enum
from typing import Dict, List

class AgentState(str, Enum):
    """Represents the high-level state of an agent or the hive."""
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    REVIEW = "REVIEW"

VALID_TRANSITIONS: Dict[AgentState, List[AgentState]] = {
    AgentState.IDLE: [AgentState.PLANNING, AgentState.EXECUTING],
    AgentState.PLANNING: [AgentState.EXECUTING, AgentState.IDLE],
    AgentState.EXECUTING: [AgentState.REVIEW, AgentState.PLANNING], 
    AgentState.REVIEW: [AgentState.IDLE, AgentState.PLANNING]
}
