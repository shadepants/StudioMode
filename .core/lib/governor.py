"""
Governor Proxy for Studio Mode
===============================
Implements "Bounded Autonomy" guardrails for the multi-agent system.
Provides rate limiting, action whitelisting, human escalation, and audit logging.
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps
import threading

# --- CONFIGURATION ---
AUDIT_LOG_PATH = "./.core/logs/governor_audit.jsonl"
REJECT_LOG_PATH = "./.core/logs/governor_rejects.md"
MAX_LLM_CALLS_PER_MINUTE = int(os.getenv("GOVERNOR_LLM_RATE", "30"))
MAX_FILE_OPS_PER_MINUTE = int(os.getenv("GOVERNOR_FILE_RATE", "60"))
ESCALATION_THRESHOLD = float(os.getenv("GOVERNOR_ESCALATION_THRESHOLD", "0.7"))


class RiskLevel(str, Enum):
    """Risk classification for agent actions."""
    LOW = "LOW"           # Auto-approve
    MEDIUM = "MEDIUM"     # Log and proceed
    HIGH = "HIGH"         # Require human approval
    CRITICAL = "CRITICAL" # Block outright


class ActionType(str, Enum):
    """Types of agent actions that can be governed."""
    LLM_CALL = "llm_call"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    HTTP_REQUEST = "http_request"
    SHELL_COMMAND = "shell_command"
    STATE_TRANSITION = "state_transition"


@dataclass
class GovernorPolicy:
    """Defines guardrails for agent actions."""
    
    # Whitelisted paths for file operations (relative to workspace)
    allowed_write_paths: List[str] = field(default_factory=lambda: [
        "./workspace/",
        "./.core/logs/",
        "./.core/memory/",
        "./agent_output/"
    ])
    
    # Blocked file patterns (never allow)
    blocked_patterns: List[str] = field(default_factory=lambda: [
        ".env",
        "*.key",
        "*.pem",
        "*password*",
        "*secret*",
        ".git/",
        "node_modules/"
    ])
    
    # Allowed shell commands (whitelist approach)
    allowed_commands: List[str] = field(default_factory=lambda: [
        "git status",
        "git log",
        "git diff",
        "npm run",
        "pytest",
        "python",
        "node"
    ])
    
    # Blocked shell patterns (always reject)
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf",
        "del /f",
        "format",
        "curl",  # External requests need review
        "wget",
        "powershell -enc",
        "bash -c"
    ])
    
    # Rate limits
    llm_rate_limit: int = MAX_LLM_CALLS_PER_MINUTE
    file_rate_limit: int = MAX_FILE_OPS_PER_MINUTE


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    timestamp: str
    action_type: ActionType
    agent_id: str
    action_detail: str
    risk_level: RiskLevel
    decision: str  # APPROVED, REJECTED, ESCALATED
    reason: str
    checksum: str = ""
    
    def __post_init__(self):
        # Create tamper-evident checksum
        content = f"{self.timestamp}{self.action_type}{self.agent_id}{self.action_detail}{self.decision}"
        self.checksum = hashlib.sha256(content.encode()).hexdigest()[:16]


class RateLimiter:
    """Thread-safe sliding window rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if action is allowed under rate limit."""
        with self.lock:
            now = time.time()
            # Remove old requests outside window
            self.requests = [t for t in self.requests if now - t < self.window_seconds]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def remaining(self) -> int:
        """Get remaining requests in current window."""
        with self.lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.window_seconds]
            return max(0, self.max_requests - len(self.requests))


class Governor:
    """
    The Governor: Central safety and governance layer for Studio Mode agents.
    
    Responsibilities:
    1. Rate limiting (LLM calls, file operations)
    2. Action whitelisting (file paths, shell commands)
    3. Risk assessment and escalation
    4. Comprehensive audit logging
    """
    
    def __init__(self, policy: GovernorPolicy = None):
        self.policy = policy or GovernorPolicy()
        self.llm_limiter = RateLimiter(self.policy.llm_rate_limit)
        self.file_limiter = RateLimiter(self.policy.file_rate_limit)
        self.pending_escalations: List[Dict] = []
        
        # Ensure log directories exist
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    
    def assess_risk(self, action_type: ActionType, detail: str) -> RiskLevel:
        """Assess the risk level of an action."""
        
        # File deletion is always high risk
        if action_type == ActionType.FILE_DELETE:
            return RiskLevel.HIGH
        
        # Shell commands need careful review
        if action_type == ActionType.SHELL_COMMAND:
            for blocked in self.policy.blocked_commands:
                if blocked.lower() in detail.lower():
                    return RiskLevel.CRITICAL
            for allowed in self.policy.allowed_commands:
                if detail.lower().startswith(allowed.lower()):
                    return RiskLevel.LOW
            return RiskLevel.HIGH
        
        # File writes - check path whitelisting
        if action_type == ActionType.FILE_WRITE:
            for blocked in self.policy.blocked_patterns:
                if self._match_pattern(blocked, detail):
                    return RiskLevel.CRITICAL
            for allowed in self.policy.allowed_write_paths:
                if detail.startswith(allowed) or detail.startswith(allowed.replace("./", "")):
                    return RiskLevel.LOW
            return RiskLevel.MEDIUM
        
        # LLM calls are generally low risk
        if action_type == ActionType.LLM_CALL:
            return RiskLevel.LOW
        
        # HTTP requests need review
        if action_type == ActionType.HTTP_REQUEST:
            if "localhost" in detail or "127.0.0.1" in detail:
                return RiskLevel.LOW
            return RiskLevel.MEDIUM
        
        return RiskLevel.MEDIUM
    
    def _match_pattern(self, pattern: str, path: str) -> bool:
        """Simple glob-like pattern matching."""
        import fnmatch
        return fnmatch.fnmatch(path.lower(), pattern.lower())
    
    def check_action(
        self,
        action_type: ActionType,
        detail: str,
        agent_id: str = "unknown"
    ) -> tuple[bool, str]:
        """
        Check if an action should be allowed.
        
        Returns:
            (allowed: bool, reason: str)
        """
        risk = self.assess_risk(action_type, detail)
        timestamp = datetime.utcnow().isoformat()
        
        # Rate limiting
        if action_type == ActionType.LLM_CALL:
            if not self.llm_limiter.is_allowed():
                self._log_audit(AuditEntry(
                    timestamp=timestamp,
                    action_type=action_type,
                    agent_id=agent_id,
                    action_detail=detail[:100],
                    risk_level=risk,
                    decision="REJECTED",
                    reason="Rate limit exceeded"
                ))
                return False, "LLM rate limit exceeded. Wait before retrying."
        
        if action_type in [ActionType.FILE_READ, ActionType.FILE_WRITE, ActionType.FILE_DELETE]:
            if not self.file_limiter.is_allowed():
                self._log_audit(AuditEntry(
                    timestamp=timestamp,
                    action_type=action_type,
                    agent_id=agent_id,
                    action_detail=detail[:100],
                    risk_level=risk,
                    decision="REJECTED",
                    reason="File operation rate limit exceeded"
                ))
                return False, "File operation rate limit exceeded."
        
        # Risk-based decision
        if risk == RiskLevel.CRITICAL:
            self._log_audit(AuditEntry(
                timestamp=timestamp,
                action_type=action_type,
                agent_id=agent_id,
                action_detail=detail[:100],
                risk_level=risk,
                decision="REJECTED",
                reason="Critical risk: Action blocked by policy"
            ))
            self._log_rejection(action_type, detail, agent_id, "Critical risk policy violation")
            return False, "Action blocked: Critical security risk detected."
        
        if risk == RiskLevel.HIGH:
            # Add to escalation queue
            self.pending_escalations.append({
                "timestamp": timestamp,
                "action_type": action_type.value,
                "agent_id": agent_id,
                "detail": detail,
                "status": "pending"
            })
            self._log_audit(AuditEntry(
                timestamp=timestamp,
                action_type=action_type,
                agent_id=agent_id,
                action_detail=detail[:100],
                risk_level=risk,
                decision="ESCALATED",
                reason="High risk: Requires human approval"
            ))
            return False, "Action requires human approval. Added to escalation queue."
        
        # Allow LOW and MEDIUM risk
        self._log_audit(AuditEntry(
            timestamp=timestamp,
            action_type=action_type,
            agent_id=agent_id,
            action_detail=detail[:100],
            risk_level=risk,
            decision="APPROVED",
            reason=f"Auto-approved: {risk.value} risk"
        ))
        return True, "Action approved."
    
    def _log_audit(self, entry: AuditEntry):
        """Append to immutable audit log."""
        try:
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception as e:
            print(f"[Governor] Audit log error: {e}")
    
    def _log_rejection(self, action_type: ActionType, detail: str, agent_id: str, reason: str):
        """Log rejection to markdown file for human review."""
        try:
            with open(REJECT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n## Rejection: {datetime.utcnow().isoformat()}\n")
                f.write(f"- **Agent:** {agent_id}\n")
                f.write(f"- **Action:** {action_type.value}\n")
                f.write(f"- **Detail:** `{detail[:200]}`\n")
                f.write(f"- **Reason:** {reason}\n")
        except Exception as e:
            print(f"[Governor] Reject log error: {e}")
    
    def get_pending_escalations(self) -> List[Dict]:
        """Get all pending human approval requests."""
        return [e for e in self.pending_escalations if e["status"] == "pending"]
    
    def approve_escalation(self, index: int) -> bool:
        """Human approves a pending escalation."""
        if 0 <= index < len(self.pending_escalations):
            self.pending_escalations[index]["status"] = "approved"
            return True
        return False
    
    def reject_escalation(self, index: int) -> bool:
        """Human rejects a pending escalation."""
        if 0 <= index < len(self.pending_escalations):
            self.pending_escalations[index]["status"] = "rejected"
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get governor statistics."""
        return {
            "llm_remaining": self.llm_limiter.remaining(),
            "file_ops_remaining": self.file_limiter.remaining(),
            "pending_escalations": len(self.get_pending_escalations()),
            "policy": {
                "llm_rate_limit": self.policy.llm_rate_limit,
                "file_rate_limit": self.policy.file_rate_limit,
                "allowed_write_paths": len(self.policy.allowed_write_paths)
            }
        }


# --- DECORATOR FOR GOVERNED ACTIONS ---
def governed(action_type: ActionType, detail_extractor: Callable = None):
    """
    Decorator to wrap functions with Governor checks.
    
    Usage:
        @governed(ActionType.FILE_WRITE, lambda args: args[0])
        def write_file(path, content):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            gov = Governor()
            detail = detail_extractor(args) if detail_extractor else str(args)
            allowed, reason = gov.check_action(action_type, detail)
            
            if not allowed:
                raise PermissionError(f"[Governor] Action blocked: {reason}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# --- SINGLETON INSTANCE ---
_governor_instance: Optional[Governor] = None


def get_governor() -> Governor:
    """Get or create the singleton Governor instance."""
    global _governor_instance
    if _governor_instance is None:
        _governor_instance = Governor()
    return _governor_instance


# --- CLI INTERFACE ---
if __name__ == "__main__":
    import sys
    
    gov = get_governor()
    
    if len(sys.argv) < 2:
        print("Governor Status:")
        print(json.dumps(gov.get_stats(), indent=2))
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "escalations":
        escalations = gov.get_pending_escalations()
        if escalations:
            for i, e in enumerate(escalations):
                print(f"[{i}] {e['action_type']}: {e['detail'][:50]}...")
        else:
            print("No pending escalations.")
    
    elif cmd == "test":
        # Test various actions
        tests = [
            (ActionType.FILE_WRITE, "./workspace/test.txt"),
            (ActionType.FILE_WRITE, ".env"),
            (ActionType.SHELL_COMMAND, "git status"),
            (ActionType.SHELL_COMMAND, "rm -rf /"),
            (ActionType.LLM_CALL, "Generate hello world"),
        ]
        
        for action, detail in tests:
            allowed, reason = gov.check_action(action, detail, "test_agent")
            status = "✅" if allowed else "❌"
            print(f"{status} {action.value}: {detail[:30]}... -> {reason[:50]}")
