import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List

class CriticService:
    """
    Critic Service: runs static analysis and calculates RepoReason metrics.
    Listens for 'REVIEW' tasks.
    """
    
    def __init__(self, work_dir: str = "./workspace"):
        self.work_dir = os.path.abspath(work_dir)
        
    def review_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a review task.
        Expected task structure:
        {
            "id": "task-uuid",
            "metadata": {
                "repo_path": "path/relative/to/workspace" (optional),
                "target_file": "path/to/file.py" (optional)
            }
        }
        """
        print(f"[Critic] Reviewing task: {task.get('id')}")
        
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
            return {"error": f"Path not found: {full_path}"}
            
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
    service = CriticService()
    # Mock task for local testing
    print(service.review_task({"id": "test", "metadata": {"repo_path": "."}}))