"""
Agent Watchdog for Studio Mode
==============================
Monitors agent health and handles stalled/failed agents.

Features:
- Heartbeat monitoring with configurable timeout
- Auto-restart stalled workers
- Alert on service failures
- Health status aggregation
"""

import os
import time
import threading
import httpx
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

# Import our logger if available
try:
    from .logger import get_logger
    logger = get_logger("watchdog")
except ImportError:
    import logging
    logger = logging.getLogger("watchdog")


class ServiceStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    name: str
    url: str
    status: ServiceStatus
    last_check: float
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    consecutive_failures: int = 0


class Watchdog:
    """Monitors service health and agent heartbeats."""
    
    def __init__(
        self,
        memory_server_url: str = "http://127.0.0.1:8000",
        check_interval: int = 10,
        heartbeat_timeout: int = 60,
    ):
        self.memory_server_url = memory_server_url
        self.check_interval = check_interval
        self.heartbeat_timeout = heartbeat_timeout
        
        self.services: Dict[str, ServiceHealth] = {}
        self.alerts: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Configure services to monitor
        self._configure_services()
    
    def _configure_services(self):
        """Configure services to monitor."""
        services = [
            ("Memory Server", "http://127.0.0.1:8000/health"),
            ("Engineer Service", "http://127.0.0.1:8001/health"),
            ("Critic Service", "http://127.0.0.1:8002/health"),
            ("Scout Service", "http://127.0.0.1:8003/health"),
        ]
        
        for name, url in services:
            self.services[name] = ServiceHealth(
                name=name,
                url=url,
                status=ServiceStatus.UNKNOWN,
                last_check=0,
            )
    
    def check_service(self, service: ServiceHealth) -> ServiceHealth:
        """Check a single service's health."""
        try:
            start = time.time()
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(service.url)
                response_time = (time.time() - start) * 1000
                
                if resp.status_code == 200:
                    service.status = ServiceStatus.ONLINE
                    service.response_time_ms = response_time
                    service.error = None
                    service.consecutive_failures = 0
                else:
                    service.status = ServiceStatus.DEGRADED
                    service.error = f"HTTP {resp.status_code}"
                    service.consecutive_failures += 1
                    
        except httpx.TimeoutException:
            service.status = ServiceStatus.OFFLINE
            service.error = "Timeout"
            service.consecutive_failures += 1
        except httpx.ConnectError:
            service.status = ServiceStatus.OFFLINE
            service.error = "Connection refused"
            service.consecutive_failures += 1
        except Exception as e:
            service.status = ServiceStatus.UNKNOWN
            service.error = str(e)
            service.consecutive_failures += 1
        
        service.last_check = time.time()
        return service
    
    def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check all configured services."""
        for name, service in self.services.items():
            self.check_service(service)
            
            # Alert on consecutive failures
            if service.consecutive_failures >= 3:
                self._alert(
                    level="error",
                    service=name,
                    message=f"Service {name} has failed {service.consecutive_failures} consecutive checks",
                )
        
        return self.services
    
    def check_agent_heartbeats(self) -> List[Dict]:
        """Check agent heartbeats from Memory Server."""
        stale_agents = []
        
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.memory_server_url}/agents/list")
                if resp.status_code == 200:
                    data = resp.json()
                    agents = data.get("agents", [])
                    
                    now = time.time()
                    for agent in agents:
                        last_heartbeat = agent.get("last_heartbeat", 0)
                        if now - last_heartbeat > self.heartbeat_timeout:
                            stale_agents.append({
                                "agent_id": agent.get("agent_id"),
                                "last_seen": last_heartbeat,
                                "stale_seconds": now - last_heartbeat,
                            })
                            
                            self._alert(
                                level="warn",
                                service=f"agent:{agent.get('agent_id')}",
                                message=f"Agent {agent.get('agent_id')} heartbeat stale for {int(now - last_heartbeat)}s",
                            )
        except Exception as e:
            logger.error(f"Failed to check agent heartbeats: {e}")
        
        return stale_agents
    
    def retry_failed_tasks(self, max_retries: int = 3) -> List[Dict]:
        """Retry failed tasks that haven't exceeded max retries."""
        retried_tasks = []
        
        try:
            with httpx.Client(timeout=10.0) as client:
                # Get failed tasks
                resp = client.get(f"{self.memory_server_url}/tasks/list?status=failed")
                if resp.status_code != 200:
                    return retried_tasks
                
                data = resp.json()
                tasks = data.get("tasks", [])
                
                for task in tasks:
                    metadata = task.get("metadata", {})
                    if isinstance(metadata, str):
                        import json
                        metadata = json.loads(metadata)
                    
                    retry_count = metadata.get("retry_count", 0)
                    
                    if retry_count < max_retries:
                        # Retry the task
                        retry_resp = client.post(
                            f"{self.memory_server_url}/tasks/update",
                            json={
                                "task_id": task["id"],
                                "status": "pending",
                                "metadata": {
                                    **metadata,
                                    "retry_count": retry_count + 1,
                                    "last_retry": time.time(),
                                }
                            }
                        )
                        
                        if retry_resp.status_code == 200:
                            retried_tasks.append({
                                "task_id": task["id"],
                                "retry_count": retry_count + 1,
                            })
                            logger.info(f"Retried task {task['id'][:8]} (attempt {retry_count + 1})")
                        
        except Exception as e:
            logger.error(f"Failed to retry tasks: {e}")
        
        return retried_tasks
    
    def _alert(self, level: str, service: str, message: str):
        """Create an alert."""
        alert = {
            "timestamp": time.time(),
            "level": level,
            "service": service,
            "message": message,
        }
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Log the alert
        log_method = getattr(logger, level, logger.info)
        log_method(message, service=service)
    
    def get_health_summary(self) -> Dict:
        """Get overall health summary."""
        online = sum(1 for s in self.services.values() if s.status == ServiceStatus.ONLINE)
        total = len(self.services)
        
        return {
            "timestamp": time.time(),
            "status": "healthy" if online == total else "degraded" if online > 0 else "critical",
            "services_online": online,
            "services_total": total,
            "services": {
                name: {
                    "status": s.status.value,
                    "response_time_ms": s.response_time_ms,
                    "error": s.error,
                    "consecutive_failures": s.consecutive_failures,
                }
                for name, s in self.services.items()
            },
            "recent_alerts": self.alerts[-10:],
        }
    
    def _run_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_all_services()
                self.check_agent_heartbeats()
                self.retry_failed_tasks()
            except Exception as e:
                logger.error(f"Watchdog loop error: {e}")
            
            time.sleep(self.check_interval)
    
    def start(self):
        """Start the watchdog in background."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Watchdog started", interval=self.check_interval)
    
    def stop(self):
        """Stop the watchdog."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Watchdog stopped")


# Singleton instance
_watchdog: Optional[Watchdog] = None


def get_watchdog() -> Watchdog:
    """Get or create the global watchdog instance."""
    global _watchdog
    if _watchdog is None:
        _watchdog = Watchdog()
    return _watchdog


if __name__ == "__main__":
    # Demo / standalone run
    import json
    
    print("🐕 Starting Watchdog...")
    watchdog = get_watchdog()
    
    # Run one check cycle
    watchdog.check_all_services()
    stale = watchdog.check_agent_heartbeats()
    retried = watchdog.retry_failed_tasks()
    
    print("\n=== Health Summary ===")
    print(json.dumps(watchdog.get_health_summary(), indent=2))
    
    if stale:
        print(f"\n⚠️  Stale agents: {len(stale)}")
    if retried:
        print(f"\n🔄 Retried tasks: {len(retried)}")
    
    print("\n✅ Watchdog check complete")
