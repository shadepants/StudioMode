"""
Health Check Service
====================
Monitors all Governed Hive services and reports their health status.

Usage:
    python .core/lib/health_check.py
    
Endpoints:
    GET /health - Returns JSON with all service statuses
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx

# Service configuration
SERVICES = {
    "memory_server": {"url": "http://localhost:8000/state", "port": 8000},
    "engineer": {"url": "http://localhost:8001/health", "port": 8001},
    "critic": {"url": "http://localhost:8002/health", "port": 8002},
    "scout": {"url": "http://localhost:8003/health", "port": 8003},
}

HEALTH_CHECK_PORT = 8080


def check_service(name: str, config: dict) -> dict:
    """Check if a service is healthy."""
    try:
        r = httpx.get(config["url"], timeout=2.0)
        return {
            "name": name,
            "status": "healthy" if r.status_code == 200 else "unhealthy",
            "port": config["port"],
            "response_code": r.status_code
        }
    except httpx.ConnectError:
        return {
            "name": name,
            "status": "offline",
            "port": config["port"],
            "response_code": None
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "port": config["port"],
            "error": str(e)
        }


def get_all_health() -> dict:
    """Get health status of all services."""
    results = {}
    healthy_count = 0
    
    for name, config in SERVICES.items():
        status = check_service(name, config)
        results[name] = status
        if status["status"] == "healthy":
            healthy_count += 1
    
    return {
        "overall": "healthy" if healthy_count == len(SERVICES) else "degraded" if healthy_count > 0 else "offline",
        "healthy_services": healthy_count,
        "total_services": len(SERVICES),
        "services": results
    }


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check requests."""
    
    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            health = get_all_health()
            
            self.send_response(200 if health["overall"] == "healthy" else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(health, indent=2).encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found. Try /health")
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server():
    """Run the health check server."""
    server = HTTPServer(("", HEALTH_CHECK_PORT), HealthCheckHandler)
    print(f"🏥 Health Check Server running on http://localhost:{HEALTH_CHECK_PORT}/health")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Health Check Server stopped.")
        server.shutdown()


if __name__ == "__main__":
    run_server()
