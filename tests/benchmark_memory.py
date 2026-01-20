import time
import requests
import uuid
import random
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def test_ingestion_firehose(count=1000):
    """
    Scenario: 'The Firehose'
    Injects `count` episodic memories rapidly.
    Measures: Latency per request, Throughput (req/sec).
    """
    log(f"--- STARTING FIREHOSE ({count} items) ---")
    
    latencies = []
    errors = 0
    start_time = time.time()
    
    def send_req(i):
        t0 = time.time()
        try:
            payload = {
                "text": f"Agent performed action #{i}: {uuid.uuid4()}",
                "type": "episodic",
                "metadata": {"seq": i}
            }
            requests.post(f"{BASE_URL}/memory/add", json=payload)
            latencies.append(time.time() - t0)
        except Exception:
            nonlocal errors
            errors += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(count):
            executor.submit(send_req, i)
            
    total_time = time.time() - start_time
    
    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0
    throughput = count / total_time
    
    log(f"Total Time: {total_time:.2f}s")
    log(f"Throughput: {throughput:.2f} ops/sec")
    log(f"Latency (Avg): {avg_latency*1000:.2f}ms")
    log(f"Latency (P95): {p95_latency*1000:.2f}ms")
    log(f"Errors: {errors}")
    
    return throughput, p95_latency

def test_retrieval_accuracy(needle_id):
    """
    Scenario: 'Needle in a Haystack'
    Searches for a specific unique string injected earlier.
    """
    log(f"--- STARTING RETRIEVAL TEST ---")
    
    # 1. Inject the Needle
    needle_text = f"CRITICAL_SECRET_CODE_{needle_id}"
    requests.post(f"{BASE_URL}/memory/add", json={
        "text": f"The secret launch code is {needle_text}",
        "type": "knowledge", # Immediate write (bypass buffer)
        "metadata": {"importance": "high"}
    })
    
    # Allow indexing (if async)
    time.sleep(1)
    
    # 2. Search
    t0 = time.time()
    resp = requests.post(f"{BASE_URL}/memory/query", json={
        "text": "What is the secret launch code?",
        "limit": 5
    })
    latency = time.time() - t0
    
    data = resp.json()
    found = False
    rank = -1
    
    for i, res in enumerate(data.get("results", [])):
        if needle_text in res["text"]:
            found = True
            rank = i
            break
            
    log(f"Search Latency: {latency*1000:.2f}ms")
    log(f"Needle Found: {found} (Rank: {rank})")
    
    return found, latency

def main():
    # Health Check
    try:
        r = requests.get(BASE_URL)
        if r.status_code != 200:
            log("Server not ready. Start '.core/services/memory_server.py' first.")
            return
        log(f"Server Online: {r.json()}")
    except Exception:
        log("Connection Failed. Is the server running?")
        return

    # Run Tests
    tp, lat = test_ingestion_firehose(200) # Small batch for dev
    found, search_lat = test_retrieval_accuracy(str(uuid.uuid4())[:8])
    
    # Report Card
    print("\n--- BENCHMARK REPORT ---")
    print(f"Ingest Throughput: {'PASS' if tp > 50 else 'FAIL'} ({tp:.1f} > 50)")
    print(f"Ingest Latency:    {'PASS' if lat < 0.2 else 'FAIL'} ({lat*1000:.0f}ms < 200ms)")
    print(f"Search Accuracy:   {'PASS' if found else 'FAIL'}")
    print(f"Search Latency:    {'PASS' if search_lat < 0.1 else 'FAIL'} ({search_lat*1000:.0f}ms < 100ms)")

if __name__ == "__main__":
    main()
