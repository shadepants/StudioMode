#!/usr/bin/env python3
"""
Engineer Worker for Studio Mode
===============================
Active spoke that polls the Memory Server for tasks assigned to 'engineer'
and coordinates with the Engineer Service to implement them.
"""

import os
import time
import requests
import json
from datetime import datetime

# --- CONFIGURATION ---

# --- CONFIGURATION ---
try:
    from ..config import MEMORY_SERVER_URL, ENGINEER_SERVICE_URL
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from .core.config import MEMORY_SERVER_URL, ENGINEER_SERVICE_URL

POLL_INTERVAL = 5  # Seconds
AGENT_ID = "engineer"

def poll_and_execute():
    """Main loop for the Engineer Worker."""
    print(f"\n[ENGINEER-WORKER] Started. Agent ID: {AGENT_ID}")
    print(f"   Memory Server: {MEMORY_SERVER_URL}")
    print(f"   Engineer Service: {ENGINEER_SERVICE_URL}")
    print(f"   Press Ctrl+C to stop\n")

    while True:
        try:
            # 1. Heartbeat to Memory Server
            try:
                requests.post(f"{MEMORY_SERVER_URL}/agents/heartbeat/{AGENT_ID}")
            except:
                pass

            # 2. Get next task
            resp = requests.get(f"{MEMORY_SERVER_URL}/agents/{AGENT_ID}/next")
            if resp.status_code == 200:
                data = resp.json()
                task = data.get("task")
                
                if task:
                    task_id = task["id"]
                    task_text = task["text"]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Claimed Task: {task_text[:50]}...")
                    
                    # 3. Call Engineer Service to implement
                    print(f"   [>] Requesting implementation from Engineer Service...")
                    impl_resp = requests.post(
                        f"{ENGINEER_SERVICE_URL}/engineer/implement",
                        json={
                            "task_id": task_id,
                            "agent_id": AGENT_ID
                        },
                        timeout=120
                    )
                    
                    if impl_resp.status_code == 200:
                        result = impl_resp.json()
                        print(f"   [OK] Task {task_id[:8]} implemented successfully.")
                        if result.get("file_path"):
                            print(f"   [+] Output: {result['file_path']}")
                    else:
                        print(f"   [ERR] Implementation failed: {impl_resp.text}")
                
            # Wait before next poll
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[BYE] Engineer Worker stopping...")
            break
        except Exception as e:
            print(f"\n[!] Error in Worker Loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # Ensure Agent is registered
    try:
        requests.post(
            f"{MEMORY_SERVER_URL}/agents/register",
            json={
                "agent_id": AGENT_ID,
                "agent_type": "engineer",
                "capabilities": ["code", "implementation", "refinist"]
            }
        )
        print(f"[ENGINEER-WORKER] Registered agent '{AGENT_ID}'")
    except Exception as e:
        print(f"[!] Warning: Could not register agent: {e}")

poll_and_execute()
