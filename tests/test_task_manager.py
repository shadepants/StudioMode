"""
Unit Tests for TaskManager Service
===================================
Tests SQLite-backed task lifecycle management.
"""

import pytest
import tempfile
import os
import sys

# Add .core to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".core")))

from services.task_manager import TaskManager, TaskCreateRequest, TaskUpdateRequest, TaskClaimRequest
from fastapi import HTTPException


class TestTaskManager:
    """Test suite for TaskManager class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a temporary database for each test."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_file.close()
        self.manager = TaskManager(self.temp_file.name)
        
        yield
        
        self.manager.close()
        os.unlink(self.temp_file.name)
    
    def test_create_task(self):
        """Test task creation returns valid ID."""
        req = TaskCreateRequest(
            text="Implement feature X",
            assignee="engineer-1",
            priority="high"
        )
        
        task_id = self.manager.create_task(req)
        
        assert task_id is not None
        assert len(task_id) == 36  # UUID format
    
    def test_list_tasks_empty(self):
        """Test listing tasks when none exist."""
        tasks = self.manager.list_tasks()
        assert tasks == []
    
    def test_list_tasks_with_filter(self):
        """Test filtering tasks by status and assignee."""
        # Create tasks
        self.manager.create_task(TaskCreateRequest(text="Task 1", assignee="agent-a"))
        self.manager.create_task(TaskCreateRequest(text="Task 2", assignee="agent-b"))
        
        # Filter by assignee
        tasks = self.manager.list_tasks(assignee="agent-a")
        assert len(tasks) == 1
        assert tasks[0]["assignee"] == "agent-a"
        
        # Filter by status
        pending = self.manager.list_tasks(status="pending")
        assert len(pending) == 2
    
    def test_claim_task_success(self):
        """Test successfully claiming a pending task."""
        task_id = self.manager.create_task(
            TaskCreateRequest(text="Test task", assignee="anyone")
        )
        
        result = self.manager.claim_task(
            TaskClaimRequest(task_id=task_id, agent_id="agent-1")
        )
        
        assert result["status"] == "success"
        
        # Verify status changed
        tasks = self.manager.list_tasks(status="in_progress")
        assert len(tasks) == 1
        assert tasks[0]["claimed_by"] == "agent-1"
    
    def test_claim_task_already_claimed(self):
        """Test claiming an already-claimed task fails."""
        task_id = self.manager.create_task(
            TaskCreateRequest(text="Test task", assignee="anyone")
        )
        
        # First claim succeeds
        self.manager.claim_task(TaskClaimRequest(task_id=task_id, agent_id="agent-1"))
        
        # Second claim fails
        with pytest.raises(HTTPException) as exc_info:
            self.manager.claim_task(TaskClaimRequest(task_id=task_id, agent_id="agent-2"))
        
        assert exc_info.value.status_code == 400
    
    def test_claim_task_not_found(self):
        """Test claiming non-existent task fails."""
        with pytest.raises(HTTPException) as exc_info:
            self.manager.claim_task(
                TaskClaimRequest(task_id="fake-id", agent_id="agent-1")
            )
        
        assert exc_info.value.status_code == 404
    
    def test_update_task(self):
        """Test updating task status and metadata."""
        task_id = self.manager.create_task(
            TaskCreateRequest(text="Test task", assignee="agent-1")
        )
        
        result = self.manager.update_task(
            TaskUpdateRequest(
                task_id=task_id,
                status="done",
                metadata={"result": "success"}
            )
        )
        
        assert result["status"] == "success"
        
        # Verify update
        tasks = self.manager.list_tasks(status="done")
        assert len(tasks) == 1
    
    def test_get_next_task(self):
        """Test getting next pending task for agent."""
        # Create tasks for different agents
        self.manager.create_task(TaskCreateRequest(text="Task 1", assignee="agent-a"))
        self.manager.create_task(TaskCreateRequest(text="Task 2", assignee="agent-b"))
        self.manager.create_task(TaskCreateRequest(text="Task 3", assignee="agent-a"))
        
        # Agent A should get Task 1 (oldest)
        task = self.manager.get_next_task("agent-a")
        
        assert task is not None
        assert task["text"] == "Task 1"
        
        # Verify it was auto-claimed in DB
        in_progress = self.manager.list_tasks(status="in_progress")
        assert len(in_progress) == 1
        assert in_progress[0]["claimed_by"] == "agent-a"
    
    def test_get_next_task_none_available(self):
        """Test getting next task when none are pending."""
        task = self.manager.get_next_task("agent-x")
        assert task is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
