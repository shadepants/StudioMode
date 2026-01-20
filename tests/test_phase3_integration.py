import pytest
import requests
import time
import uuid
import json

# Configuration
SERVER_URL = "http://127.0.0.1:8000"

def test_memory_server_health():
    """Verify Memory Server is online."""
    resp = requests.get(SERVER_URL + "/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"

def test_full_workflow_loop():
    """
    Integration Test for Phase 3:
    1. Create a Workflow (IDLE -> PLANNING)
    2. Add Tasks (PLANNING)
    3. Claim Task (EXECUTING)
    4. Complete Task (REVIEW)
    """
    
    # 1. Create a Workflow
    workflow_id = f"test-flow-{uuid.uuid4()}"
    workflow_payload = {
        "workflow_id": workflow_id,
        "name": "Integration Test Workflow",
        "tasks": [
            {
                "name": "Test Task A",
                "description": "A simple task for integration testing",
                "assignee": "gemini-cli",
                "priority": "high",
                "dependencies": []
            }
        ]
    }
    
    resp = requests.post(f"{SERVER_URL}/workflows/create", json=workflow_payload)
    assert resp.status_code == 200
    print(f"\nWorkflow created: {workflow_id}")

    # 2. Verify Task Creation
    resp = requests.get(f"{SERVER_URL}/agents/gemini-cli/tasks")
    assert resp.status_code == 200
    tasks = resp.json().get("tasks", [])
    
    # Find our specific task
    target_task = None
    for t in tasks:
        meta = json.loads(t.get("metadata", "{{}}"))
        if meta.get("workflow_id") == workflow_id:
            target_task = t
            break
            
    assert target_task is not None
    task_id = target_task["id"]
    print(f"Task found: {task_id}")

    # 3. Simulate Agent Claiming Task
    # Note: The 'next' endpoint auto-claims, so we use that or manual claim
    claim_resp = requests.post(f"{SERVER_URL}/tasks/claim", json={
        "task_id": task_id,
        "agent_id": "gemini-cli"
    })
    
    # It might fail if already auto-claimed by the real agent running in background
    # So we check status first
    if claim_resp.status_code != 200:
        # Check if it's already in progress
        status_resp = requests.get(f"{SERVER_URL}/tasks/list")
        all_tasks = status_resp.json()["tasks"]
        t_status = next((t for t in all_tasks if t["id"] == task_id), None)
        assert t_status["status"] in ["in_progress", "completed"]
        print("Task already claimed or processed.")
    else:
        print("Task claimed successfully.")

    # 4. Update to Review (Simulating Engineer completion)
    update_resp = requests.post(f"{SERVER_URL}/tasks/update", json={
        "task_id": task_id,
        "status": "review",
        "metadata": {"output_path": "test_output.txt"}
    })
    assert update_resp.status_code == 200
    print("Task submitted for review.")
    
    # 5. Verify Status
    final_resp = requests.get(f"{SERVER_URL}/tasks/list")
    final_tasks = final_resp.json()["tasks"]
    final_task = next((t for t in final_tasks if t["id"] == task_id), None)
    assert final_task["status"] == "review"

if __name__ == "__main__":
    # Allow running directly
    try:
        test_memory_server_health()
        test_full_workflow_loop()
        print("\n✅ Integration Tests Passed!")
    except Exception as e:
        print(f"\n❌ Tests Failed: {e}")