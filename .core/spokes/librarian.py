import time
import os
import shutil
import hashlib
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


try:
    from ..config import MEMORY_SERVER_URL, INCOMING_DIR, PROCESSED_DIR
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from .core.config import MEMORY_SERVER_URL, INCOMING_DIR, PROCESSED_DIR

# Ensure directories exist
os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

API_URL = f"{MEMORY_SERVER_URL}/sources/add"

class LibrarianHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        if filename.startswith("."): return # Ignore hidden/temp files

        print(f"[Librarian] Detected new file: {filename}")
        
        # Debounce / Wait for write to finish
        time.sleep(1.0)
        
        self.process_file(event.src_path, filename)

    def process_file(self, filepath, filename):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checksum = hashlib.md5(content.encode()).hexdigest()
            
            # Send to Memory Server
            payload = {
                "title": filename,
                "type": "upload",
                "url": f"file://{filename}",
                "summary": content[:500] + "..." if len(content) > 500 else content,
                "tags": ["manual_ingest"],
                "checksum": checksum
            }
            
            try:
                print(f"[Librarian] Ingesting {filename}...")
                res = requests.post(API_URL, json=payload)
                if res.status_code == 200:
                    print(f"[Librarian] Success! ID: {res.json()['id']}")
                    
                    # Move to processed
                    dest = os.path.join(PROCESSED_DIR, filename)
                    if os.path.exists(dest):
                        base, ext = os.path.splitext(filename)
                        dest = os.path.join(PROCESSED_DIR, f"{base}_{int(time.time())}{ext}")
                    
                    shutil.move(filepath, dest)
                    print(f"[Librarian] Archived to {dest}")
                else:
                    print(f"[!] API Error: {res.text}")
                    
            except requests.exceptions.ConnectionError:
                print(f"[!] Connection Error: Is memory_server.py running?")
                
        except Exception as e:
            print(f"[!] Processing Error: {e}")

if __name__ == "__main__":
    if not os.path.exists(INCOMING_DIR):
        os.makedirs(INCOMING_DIR)
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    # 1. Process existing files on startup
    print(f"[Librarian] Scanning {INCOMING_DIR} for existing files...")
    event_handler = LibrarianHandler()
    
    for filename in os.listdir(INCOMING_DIR):
        filepath = os.path.join(INCOMING_DIR, filename)
        if os.path.isfile(filepath) and not filename.startswith("."):
            print(f"[Librarian] Found existing file: {filename}")
            event_handler.process_file(filepath, filename)

    # 2. Start Watcher
    observer = Observer()
    observer.schedule(event_handler, INCOMING_DIR, recursive=False)
    observer.start()
    
    print(f"[Librarian] Watchdog active on {INCOMING_DIR}")
    print(f"[Librarian] Target API: {API_URL}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
