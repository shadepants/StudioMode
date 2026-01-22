"""
Core Task Models
================
Shared models for task management.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class TaskStatus(str, Enum):
    """Status of a task in the lifecycle."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REVIEW = "review"
