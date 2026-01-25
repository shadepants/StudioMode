import os
import sys
import subprocess
import shutil
from typing import Dict, Any, List

# Add the project root, .core, and current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.abspath(os.path.join(current_dir, ".."))
project_root = os.path.abspath(os.path.join(core_dir, ".."))

for d in [project_root, core_dir, current_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from base_service import BaseAgentService
except ImportError:
    try:
        from services.base_service import BaseAgentService
    except ImportError:
        try:
            from .base_service import BaseAgentService
        except (ImportError, ValueError):
            from .core.services.base_service import BaseAgentService

class CriticService(BaseAgentService):
    """
    Critic Service: runs static analysis and calculates RepoReason metrics.
    Listens for 'REVIEW' tasks.
    """
    
    def __init__(self, work_dir: str = "./workspace"):
        super().__init__(agent_id="critic-1", agent_type="critic", capabilities=["code-review", "linting", "testing"])
        self.work_dir = os.path.abspath(work_dir)
        
    async def process_task(self, task: Dict[str, Any]):
        """Process assigned review task."""
        print(f"[Critic] Reviewing task: {task.get('id')}")
        
        # 1. Update status to IN_PROGRESS
        await self.update_task(task['id'], "in_progress")
        
        # 2. Perform Review
        try:
            results = self._perform_review(task)
            status = "completed" if results["status"] == "pass" else "failed" # or 'needs_revision'
            
            # 3. Update Status
            await self.update_task(task['id'], status, {"review_results": results})
        except Exception as e:
            await self.update_task(task['id'], "failed", {"error": str(e)})

    def _perform_review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Internal synchronous review logic."""
        # Determine target path
        metadata = task.get("metadata", {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                
        repo_path = metadata.get("repo_path", ".")
        full_path = os.path.join(self.work_dir, repo_path)
        
        results = {
            "lint_score": 0,
            "errors": [],
            "status": "pass"
        }
        
        if not os.path.exists(full_path):
            results["errors"].append(f"Path not found: {full_path}")
            results["status"] = "failed"
            return results
            
        # 1. Run Linter (Flake8)
        print(f"[Critic] Running linter on {full_path}...")
        try:
            # Check if flake8 is installed, if not, skip or use a fallback
            lint_cmd = ["flake8", full_path, "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"]
            process = subprocess.run(lint_cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                results["errors"].append(process.stderr or process.stdout)
                results["status"] = "issues_found"
            else:
                results["lint_score"] = 10.0 # Placeholder for perfect score
                
        except FileNotFoundError:
            print("[Critic] Flake8 not found. Skipping linting.")
            results["errors"].append("Flake8 not installed")

        # 2. Run Tests (Pytest)
        print(f"[Critic] Running tests on {full_path}...")
        try:
            test_cmd = ["pytest", full_path, "-q"]
            process = subprocess.run(test_cmd, capture_output=True, text=True)
            
            results["test_output"] = process.stdout
            if process.returncode != 0:
                results["status"] = "tests_failed"
        except FileNotFoundError:
             print("[Critic] Pytest not found. Skipping tests.")
             
        return results

# Expose a standalone entry point if needed
if __name__ == "__main__":
    import asyncio
    service = CriticService()
    asyncio.run(service.start())