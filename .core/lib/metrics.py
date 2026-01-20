"""
Metrics Collection Service for Studio Mode
==========================================
Collects and exposes system metrics for monitoring.

Usage:
    from .core.lib.metrics import MetricsCollector, get_metrics
    
    metrics = get_metrics()
    metrics.increment("tasks_completed")
    metrics.gauge("active_agents", 3)
    metrics.timing("task_duration", 1.5)
    
    # Get all metrics as dict
    metrics.snapshot()
"""

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"


class MetricsCollector:
    """Thread-safe metrics collector with Prometheus-style metrics."""
    
    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._metrics: Dict[str, MetricPoint] = {}
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._histograms: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._initialized = True
    
    # --- Counter Methods ---
    
    def increment(self, name: str, value: float = 1.0, **tags):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            self._update_metric(name, self._counters[key], "counter", tags)
    
    def decrement(self, name: str, value: float = 1.0, **tags):
        """Decrement a counter metric."""
        self.increment(name, -value, **tags)
    
    # --- Gauge Methods ---
    
    def gauge(self, name: str, value: float, **tags):
        """Set a gauge metric (point-in-time value)."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self._update_metric(name, value, "gauge", tags)
    
    # --- Timing Methods ---
    
    def timing(self, name: str, duration: float, **tags):
        """Record a timing metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._timings[key].append(duration)
            # Keep only last 1000 timings
            if len(self._timings[key]) > 1000:
                self._timings[key] = self._timings[key][-1000:]
            self._update_metric(name, duration, "timing", tags)
    
    def time(self, name: str, **tags):
        """Context manager for timing blocks."""
        return TimingContext(self, name, tags)
    
    # --- Histogram Methods ---
    
    def histogram(self, name: str, value: float, buckets: List[float] = None, **tags):
        """Record a histogram metric."""
        if buckets is None:
            buckets = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
        
        with self._lock:
            key = self._make_key(name, tags)
            for bucket in buckets:
                if value <= bucket:
                    bucket_key = f"{key}_le_{bucket}"
                    self._histograms[name][bucket_key] += 1
                    break
            self._update_metric(name, value, "histogram", tags)
    
    # --- Utility Methods ---
    
    def _make_key(self, name: str, tags: Dict[str, str]) -> str:
        """Create a unique key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def _update_metric(self, name: str, value: float, metric_type: str, tags: Dict[str, str]):
        """Update internal metrics storage."""
        key = self._make_key(name, tags)
        self._metrics[key] = MetricPoint(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags,
            metric_type=metric_type
        )
    
    def snapshot(self) -> Dict[str, Any]:
        """Get current snapshot of all metrics."""
        with self._lock:
            uptime = time.time() - self._start_time
            
            # Calculate timing stats
            timing_stats = {}
            for key, values in self._timings.items():
                if values:
                    timing_stats[key] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "last": values[-1],
                    }
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "uptime_seconds": uptime,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timing_stats": timing_stats,
                "histograms": {k: dict(v) for k, v in self._histograms.items()},
            }
    
    def prometheus_format(self) -> str:
        """Export metrics in Prometheus exposition format."""
        lines = []
        
        # Add uptime
        uptime = time.time() - self._start_time
        lines.append(f"# HELP studio_uptime_seconds System uptime in seconds")
        lines.append(f"# TYPE studio_uptime_seconds gauge")
        lines.append(f"studio_uptime_seconds {uptime:.2f}")
        
        # Add counters
        for key, value in self._counters.items():
            name = key.split("{")[0].replace(".", "_")
            lines.append(f"studio_{name} {value}")
        
        # Add gauges
        for key, value in self._gauges.items():
            name = key.split("{")[0].replace(".", "_")
            lines.append(f"studio_{name} {value}")
        
        return "\n".join(lines)
    
    def json_format(self) -> str:
        """Export metrics as JSON."""
        return json.dumps(self.snapshot(), indent=2)
    
    def reset(self):
        """Reset all metrics (for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timings.clear()
            self._histograms.clear()
            self._metrics.clear()


class TimingContext:
    """Context manager for timing code blocks."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.timing(self.name, duration, **self.tags)
        return False


# Singleton accessor
def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return MetricsCollector()


# Pre-defined metrics helpers
def task_started(task_id: str, agent: str = "unknown"):
    """Record a task started event."""
    metrics = get_metrics()
    metrics.increment("tasks.started", agent=agent)
    metrics.gauge("tasks.active", metrics._counters.get("tasks.started", 0) - 
                  metrics._counters.get("tasks.completed", 0))


def task_completed(task_id: str, duration: float, agent: str = "unknown"):
    """Record a task completed event."""
    metrics = get_metrics()
    metrics.increment("tasks.completed", agent=agent)
    metrics.timing("task.duration", duration, agent=agent)
    metrics.histogram("task.duration.histogram", duration)


def task_failed(task_id: str, error: str, agent: str = "unknown"):
    """Record a task failed event."""
    metrics = get_metrics()
    metrics.increment("tasks.failed", agent=agent, error_type=error[:20])


def agent_heartbeat(agent_id: str):
    """Record an agent heartbeat."""
    metrics = get_metrics()
    metrics.gauge(f"agent.last_seen.{agent_id}", time.time())
    metrics.increment("agent.heartbeats", agent_id=agent_id)


if __name__ == "__main__":
    # Demo
    metrics = get_metrics()
    
    # Simulate some activity
    task_started("task-001", agent="engineer")
    time.sleep(0.1)
    task_completed("task-001", duration=0.1, agent="engineer")
    
    metrics.increment("api.requests", endpoint="/tasks/list")
    metrics.gauge("memory.usage_mb", 256.5)
    
    with metrics.time("api.response_time", endpoint="/state"):
        time.sleep(0.05)
    
    print("=== Metrics Snapshot ===")
    print(metrics.json_format())
    
    print("\n=== Prometheus Format ===")
    print(metrics.prometheus_format())
