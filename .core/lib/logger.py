"""
Structured Logger for Studio Mode
=================================
JSON-formatted logging with rotation, levels, and service tagging.

Usage:
    from .core.lib.logger import get_logger
    
    logger = get_logger("memory_server")
    logger.info("Server started", port=8000)
    logger.error("Connection failed", error=str(e), retry=3)
"""

import os
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum
import threading
from queue import Queue


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Level priority for filtering
LEVEL_PRIORITY = {
    LogLevel.DEBUG: 0,
    LogLevel.INFO: 1,
    LogLevel.WARN: 2,
    LogLevel.ERROR: 3,
    LogLevel.CRITICAL: 4,
}


class StructuredLogger:
    """JSON-structured logger with async file writing and rotation."""
    
    _instances: dict = {}
    _lock = threading.Lock()
    _write_queue: Queue = Queue()
    _writer_thread: Optional[threading.Thread] = None
    _running = False
    
    def __new__(cls, service_name: str, log_dir: str = ".core/logs"):
        """Singleton per service name."""
        with cls._lock:
            if service_name not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[service_name] = instance
            return cls._instances[service_name]
    
    def __init__(self, service_name: str, log_dir: str = ".core/logs"):
        if self._initialized:
            return
            
        self.service_name = service_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_level = LogLevel(os.getenv("LOG_LEVEL", "INFO").upper())
        self.console_enabled = os.getenv("LOG_CONSOLE", "true").lower() == "true"
        self.file_enabled = os.getenv("LOG_FILE", "true").lower() == "true"
        
        self._current_log_file: Optional[Path] = None
        self._current_date: Optional[str] = None
        self._file_handle = None
        
        # Start background writer
        self._start_writer()
        self._initialized = True
    
    def _start_writer(self):
        """Start background log writer thread."""
        if not StructuredLogger._running:
            StructuredLogger._running = True
            StructuredLogger._writer_thread = threading.Thread(
                target=self._background_writer,
                daemon=True
            )
            StructuredLogger._writer_thread.start()
    
    def _background_writer(self):
        """Background thread that writes logs to file."""
        while StructuredLogger._running:
            try:
                log_entry = StructuredLogger._write_queue.get(timeout=1.0)
                if log_entry is None:
                    continue
                self._write_to_file(log_entry)
            except:
                continue
    
    def _get_log_file(self) -> Path:
        """Get current log file, rotating daily."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._current_date != today:
            self._current_date = today
            self._current_log_file = self.log_dir / f"{self.service_name}_{today}.log"
            if self._file_handle:
                self._file_handle.close()
            self._file_handle = None
        return self._current_log_file
    
    def _write_to_file(self, log_entry: dict):
        """Write log entry to file."""
        if not self.file_enabled:
            return
            
        log_file = self._get_log_file()
        try:
            if self._file_handle is None:
                self._file_handle = open(log_file, "a", encoding="utf-8")
            self._file_handle.write(json.dumps(log_entry) + "\n")
            self._file_handle.flush()
        except Exception as e:
            print(f"[LOG ERROR] Failed to write to file: {e}", file=sys.stderr)
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if level meets minimum threshold."""
        return LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[self.min_level]
    
    def _format_console(self, entry: dict) -> str:
        """Format log entry for console output."""
        level = entry["level"]
        colors = {
            "DEBUG": "\033[90m",    # Gray
            "INFO": "\033[36m",     # Cyan
            "WARN": "\033[33m",     # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m", # Magenta
        }
        reset = "\033[0m"
        color = colors.get(level, "")
        
        timestamp = entry["timestamp"].split("T")[1][:8]
        service = entry["service"][:12].ljust(12)
        message = entry["message"]
        
        # Add extra fields if present
        extras = {k: v for k, v in entry.items() 
                  if k not in ["timestamp", "level", "service", "message"]}
        extra_str = f" {extras}" if extras else ""
        
        return f"{color}[{timestamp}] [{level:8}] [{service}] {message}{extra_str}{reset}"
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Core logging method."""
        if not self._should_log(level):
            return
            
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.value,
            "service": self.service_name,
            "message": message,
            **kwargs
        }
        
        # Console output (sync)
        if self.console_enabled:
            print(self._format_console(entry))
        
        # File output (async)
        if self.file_enabled:
            StructuredLogger._write_queue.put(entry)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARN, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def task_event(self, event_type: str, task_id: str, **kwargs):
        """Log a task-related event."""
        self.info(f"Task {event_type}", task_id=task_id[:8], event=event_type, **kwargs)
    
    def agent_event(self, event_type: str, agent_id: str, **kwargs):
        """Log an agent-related event."""
        self.info(f"Agent {event_type}", agent_id=agent_id, event=event_type, **kwargs)


def get_logger(service_name: str) -> StructuredLogger:
    """Get or create a logger for the given service."""
    return StructuredLogger(service_name)


# Convenience function for quick access
def log(message: str, level: str = "INFO", service: str = "system", **kwargs):
    """Quick logging without creating a logger instance."""
    logger = get_logger(service)
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, **kwargs)


if __name__ == "__main__":
    # Demo
    logger = get_logger("demo_service")
    logger.info("Service started", port=8000, version="1.0.0")
    logger.debug("Debug message", data={"key": "value"})
    logger.warn("Warning message", threshold=0.8)
    logger.error("Error occurred", error="Connection refused", retry=3)
    logger.task_event("claimed", "abc123def456", agent_id="engineer")
    
    time.sleep(1)  # Allow background writer to flush
    print("\n✅ Logger demo complete. Check .core/logs/ for output.")
