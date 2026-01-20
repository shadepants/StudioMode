"""
Critic Service for Studio Mode
==============================
Autonomous Quality Assurance agent (The Critic) that evaluates code against standards.
Combines LLM-based reasoning (RepoReason) with optional static analysis.
"""

import os
import json
import httpx
import asyncio
import subprocess
import shutil
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
import litellm
from pathlib import Path

# Fix relative import for governor
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")))
from governor import governed, ActionType, get_governor

# --- CONFIGURATION ---
MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "http://127.0.0.1:8000")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
WORKSPACE_DIR = os.path.abspath("./workspace")

# --- PERSONA DEFINITION ---
CRITIC_SYSTEM_PROMPT = """You are the Critic, a specialized QA agent.
Your role is to validate the output of the Engineer agent.

Evaluation Criteria (RepoReason Metrics):
1. Code Quality: Cleanliness, readability, PEP8, naming conventions.
2. Completeness: Does it fully address the task?
3. Safety: Security issues, unchecked inputs, hardcoded secrets.
4. Type Safety: Proper typing.
5. Reliability: Error handling.

Output Format:
VERDICT: PASS or FAIL
SCORE: 1-10
ISSUES: (Bulleted list)
SUGGESTIONS: (Bulleted list)
"""

class ReviewRequest(BaseModel):
    task_id: str
    task_text: str
    code_content: Optional[str] = None
    file_path: Optional[str] = None
    repo_path: Optional[str] = None # For full repo reviews

class ReviewResponse(BaseModel):
    task_id: str
    verdict: str # PASS / FAIL
    score: int
    critique: str
    static_analysis: Optional[Dict[str, Any]] = None

class CriticService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.governor = get_governor()

    @governed(ActionType.LLM_CALL, lambda args: args[0])
    async def review_task(self, req: ReviewRequest) -> ReviewResponse:
        """
        Review a task output using LLM and optional tools.
        """
        static_analysis_results = {}
        
        # 1. Run Static Analysis if path is provided
        if req.file_path or req.repo_path:
            target = req.file_path or req.repo_path
            # Check if exists in workspace
            full_path = os.path.join(WORKSPACE_DIR, target) if not os.path.isabs(target) else target
            
            if os.path.exists(full_path):
                # Run Flake8 (if python)
                if full_path.endswith(".py") or os.path.isdir(full_path):
                     static_analysis_results["flake8"] = self._run_flake8(full_path)
        
        # 2. Build Prompt
        user_prompt = f"Task: {req.task_text}\n\n"
        
        if req.code_content:
            user_prompt += f"Code to Review:\n```\n{req.code_content}\n```\n\n"
        elif req.file_path and os.path.exists(os.path.join(WORKSPACE_DIR, req.file_path)):
             with open(os.path.join(WORKSPACE_DIR, req.file_path), "r") as f:
                 user_prompt += f"Code to Review ({req.file_path}):\n```\n{f.read()}\n```\n\n"
        
        if static_analysis_results:
            user_prompt += f"Static Analysis Results:\n{json.dumps(static_analysis_results, indent=2)}\n\n"

        user_prompt += "Evaluate this against the criteria."

        # 3. Call LLM
        response = await litellm.acompletion(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        critique_text = response.choices[0].message.content
        
        # Parse Verdict
        verdict = "FAIL"
        if "VERDICT: PASS" in critique_text.upper():
            verdict = "PASS"
            
        # Parse Score (simple heuristic)
        score = 5
        try:
            for line in critique_text.split("\n"):
                if "SCORE:" in line.upper():
                    s = line.split(":")[1].strip()
                    score = int(s.split("/")[0]) if "/" in s else int(s)
        except:
            pass

        return ReviewResponse(
            task_id=req.task_id,
            verdict=verdict,
            score=score,
            critique=critique_text,
            static_analysis=static_analysis_results
        )

    def _run_flake8(self, path: str) -> Dict[str, Any]:
        """Run flake8 on the path."""
        try:
            # Basic check if flake8 is installed
            result = subprocess.run(
                ["flake8", path, "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"],
                capture_output=True,
                text=True,
                check=False
            )
            return {
                "exit_code": result.returncode,
                "output": result.stdout + result.stderr
            }
        except FileNotFoundError:
            return {"error": "flake8 not installed"}
        except Exception as e:
            return {"error": str(e)}

# --- FASTAPI APP ---
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Critic Service", version="1.0.0")
service = CriticService()

@app.post("/critic/review")
async def review_endpoint(req: ReviewRequest):
    try:
        return await service.review_task(req)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "online", "persona": "C.O.R.E. Critic"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
