"""
Engineer Service for Studio Mode
================================
Autonomously generates code based on specifications using the 'C.O.R.E. Engineer' persona.
Implements the 'Refinist' approach: Functional Core first, then hardening.
"""

import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import litellm

import sys
# Ensure we can import libraries similarly to original file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")))

from governor import governed, ActionType, get_governor

try:
    from ..config import DEFAULT_MODEL
    from .base_service import BaseAgentService
except ImportError:
    from .core.config import DEFAULT_MODEL
    from .core.services.base_service import BaseAgentService

# --- MODELS ---
class CodeGenerationRequest(BaseModel):
    task_id: str
    task_text: str
    context: str = ""
    file_path: Optional[str] = None
    existing_content: Optional[str] = None

class CodeGenerationResponse(BaseModel):
    task_id: str
    code: str
    explanation: str
    file_path: Optional[str] = None

# --- PERSONA ---
ENGINEER_SYSTEM_PROMPT = """You are the C.O.R.E. Engineer, a specialized code generation agent.
Your primary objective is implementation, debugging, and optimization.
Follow the "Refinist" approach: Functional Core (v0.1) first, then hardening.
You must act as a Senior Software Architect.

Operational Constraints:
1. Safety Level: 2 (Standard Governor Compliance).
2. Tooling Isomorphism: Use standard tools (pwsh, git, npm).
3. Documentation: Write "Why-comments" explaining design choices.

Output Format:
Return ONLY the code block(s) requested. If explanation is needed, use comments within the code.
Do not wrap in markdown code blocks unless requested.
"""

class EngineerService(BaseAgentService):
    def __init__(self):
        super().__init__(agent_id="engineer-1", agent_type="engineer", capabilities=["code-generation", "refactoring", "polishing"])
        self.governor = get_governor()

    async def process_task(self, task: Dict[str, Any]):
        """
        Process tasks assigned to the engineer.
        Task Types:
        - "implementation": standard code gen
        - "polishing": refinement
        """
        print(f"[Engineer] Processing task: {task['id']}")
        await self.update_task(task['id'], "in_progress")

        try:
            # Parse metadata logic
            metadata = task.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}

            task_text = task["text"]
            file_path = metadata.get("target_file")
            
            # Read context if file exists
            existing_content = None
            if file_path:
                 # Using self.client (AsyncMemoryClient) to read file
                 try:
                     resp = await self.client.read_file(file_path)
                     existing_content = resp.get("content")
                 except Exception:
                     pass # File might not exist yet

            # Prepare Request
            gen_req = CodeGenerationRequest(
                task_id=task["id"],
                task_text=task_text,
                context=metadata.get("description", ""),
                file_path=file_path,
                existing_content=existing_content
            )

            # Generate
            gen_resp = await self.generate_code(gen_req)

            # Write to FS
            if gen_resp.file_path:
                print(f"[Engineer] Writing code to {gen_resp.file_path}...")
                success = await self.client.write_file(gen_resp.file_path, gen_resp.code)
                if not success:
                    raise Exception("FileSystem Write Failed")

            # Update to Review
            await self.update_task(task['id'], "review", {
                "output_path": gen_resp.file_path,
                "engineer_explanation": gen_resp.explanation
            })
            
        except Exception as e:
            print(f"[Engineer] Task failed: {e}")
            await self.update_task(task['id'], "failed", {"error": str(e)})

    @governed(ActionType.LLM_CALL, lambda args: args[1].task_text if len(args) > 1 else "Unknown Task")
    async def generate_code(self, req: CodeGenerationRequest) -> CodeGenerationResponse:
        """Core generation logic with Governor."""
        user_prompt = f"Task: {req.task_text}\n\n"
        
        if req.context:
            user_prompt += f"Context:\n{req.context}\n\n"
            
        if req.existing_content:
            user_prompt += f"Existing Content ({req.file_path}):\n```\n{req.existing_content}\n```\n\n"
            user_prompt += "Instructions: Modify the existing code to fulfill the task. Maintain existing style.\n"
        else:
            user_prompt += "Instructions: Generate new code to fulfill the task.\n"

        if req.file_path:
            user_prompt += f"Target File: {req.file_path}\n"

        response = await litellm.acompletion(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": ENGINEER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        code = self._extract_code(content)
        
        return CodeGenerationResponse(
            task_id=req.task_id,
            code=code,
            explanation="Generated by C.O.R.E. Engineer",
            file_path=req.file_path
        )

    def _extract_code(self, content: str) -> str:
        if "```" in content:
            try:
                start = content.find("```")
                end_first_line = content.find("\n", start)
                end = content.find("```", end_first_line)
                if end != -1:
                    return content[end_first_line+1:end].strip()
            except:
                pass
        return content

if __name__ == "__main__":
    service = EngineerService()
    asyncio.run(service.start())
