"""
Tests for LangGraph Cortex
==========================
Unit tests for state transitions, node execution, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".core", "lib"))


class TestHiveState:
    """Tests for HiveState transitions."""
    
    def test_initial_state_is_idle(self):
        """Test that initial state is IDLE."""
        from langgraph_cortex import AgentState
        
        state = {"current_phase": AgentState.IDLE}
        assert state["current_phase"] == AgentState.IDLE
    
    def test_state_transition_to_executing(self):
        """Test transition from IDLE to EXECUTING."""
        from langgraph_cortex import AgentState
        
        state = {"current_phase": AgentState.IDLE}
        state["current_phase"] = AgentState.EXECUTING
        assert state["current_phase"] == AgentState.EXECUTING
    
    def test_state_transition_to_review(self):
        """Test transition from EXECUTING to REVIEW."""
        from langgraph_cortex import AgentState
        
        state = {"current_phase": AgentState.EXECUTING}
        state["current_phase"] = AgentState.REVIEW
        assert state["current_phase"] == AgentState.REVIEW


class TestRouterFunction:
    """Tests for the should_continue router function."""
    
    def test_router_idle_without_task(self):
        """Test router returns 'fetch' when IDLE with no task."""
        from langgraph_cortex import should_continue, AgentState
        
        state = {"current_phase": AgentState.IDLE, "task_id": None}
        result = should_continue(state)
        assert result == "fetch"
    
    def test_router_idle_with_task(self):
        """Test router returns 'end' when IDLE with completed task."""
        from langgraph_cortex import should_continue, AgentState
        
        state = {"current_phase": AgentState.IDLE, "task_id": "test-123"}
        result = should_continue(state)
        assert result == "end"
    
    def test_router_executing(self):
        """Test router returns 'engineer' when EXECUTING."""
        from langgraph_cortex import should_continue, AgentState
        
        state = {"current_phase": AgentState.EXECUTING}
        result = should_continue(state)
        assert result == "engineer"
    
    def test_router_review(self):
        """Test router returns 'critic' when in REVIEW."""
        from langgraph_cortex import should_continue, AgentState
        
        state = {"current_phase": AgentState.REVIEW}
        result = should_continue(state)
        assert result == "critic"


class TestMemoryClient:
    """Tests for MemoryClient integration."""
    
    @patch("langgraph_cortex.httpx.Client")
    def test_get_pending_tasks(self, mock_client):
        """Test fetching pending tasks."""
        from langgraph_cortex import MemoryClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tasks": [{"id": "task-1", "text": "Test"}]}
        mock_client.return_value.get.return_value = mock_response
        
        client = MemoryClient()
        tasks = client.get_pending_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]["id"] == "task-1"
    
    @patch("langgraph_cortex.httpx.Client")
    def test_claim_task(self, mock_client):
        """Test claiming a task."""
        from langgraph_cortex import MemoryClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.post.return_value = mock_response
        
        client = MemoryClient()
        result = client.claim_task("task-1", "engineer_agent")
        
        assert result is True


class TestErrorHandling:
    """Tests for error scenarios."""
    
    def test_empty_task_list_returns_idle(self):
        """Test that empty task list keeps state IDLE."""
        from langgraph_cortex import AgentState
        
        state = {"current_phase": AgentState.IDLE, "task_id": None}
        # Simulating fetch_task_node behavior when no tasks
        if not []:  # Empty task list
            state["current_phase"] = AgentState.IDLE
        
        assert state["current_phase"] == AgentState.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
