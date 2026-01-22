"""
Studio Mode - Centralized Configuration
========================================
Single source of truth for all configuration constants.
Import this module instead of defining constants inline.

Usage:
    from .core.config.settings import MEMORY_SERVER_URL, DEFAULT_MODEL
    # Or with relative import:
    from ..config.settings import MEMORY_SERVER_URL
"""

import os

# --- Server URLs ---
# Memory Server: Central state, tasks, and memory management
MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "http://127.0.0.1:8000")

# Agent Services
ENGINEER_SERVICE_URL = os.getenv("ENGINEER_SERVICE_URL", "http://127.0.0.1:8001")
CRITIC_SERVICE_URL = os.getenv("CRITIC_SERVICE_URL", "http://127.0.0.1:8002")
SCOUT_SERVICE_URL = os.getenv("SCOUT_SERVICE_URL", "http://127.0.0.1:8003")

# --- LLM Configuration ---
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))  # seconds

# --- Directories ---
WORKSPACE_DIR = os.path.abspath("./workspace")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "agent_output")
INCOMING_DIR = os.path.join(WORKSPACE_DIR, "incoming")
PROCESSED_DIR = os.path.join(WORKSPACE_DIR, "processed")
DOCS_DIR = os.path.abspath("./docs")

# --- Database Paths ---
DB_URI = os.path.abspath("./.core/memory/lancedb")
SQLITE_DB = os.path.abspath("./.core/memory/tasks.db")

# --- API Keys (optional) ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SERP_API_KEY = os.getenv("SERP_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --- Governor Settings ---
MAX_LLM_CALLS_PER_MINUTE = int(os.getenv("GOVERNOR_LLM_RATE", "30"))
MAX_FILE_OPS_PER_MINUTE = int(os.getenv("GOVERNOR_FILE_RATE", "60"))
ESCALATION_THRESHOLD = float(os.getenv("GOVERNOR_ESCALATION_THRESHOLD", "0.7"))

# --- Polling / Timing ---
DEFAULT_POLL_INTERVAL = 10  # seconds
HEARTBEAT_TIMEOUT = 60  # seconds

# --- Vector Store ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SYNC_INTERVAL = 60  # Seconds between doc syncs
BUFFER_SIZE = 5     # Auto-flush memory buffer after N items
DECAY_RATE = 0.0001 # OpenMemory decay factor
