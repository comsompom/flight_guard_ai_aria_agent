#!/usr/bin/env python3
"""
Run backend and frontend for the demo. The backend serves the map UI at http://localhost:8000.
One process, one port. Press Ctrl+C to stop.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 8000

# Add backend to path so "app" module is found
backend_dir = os.path.join(REPO_ROOT, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    os.chdir(REPO_ROOT)  # ensure frontend/ is found relative to repo root
    print("Starting FlightGuard (API + map UI)...")
    print(f"  Open: http://localhost:{BACKEND_PORT}  — map UI and landing")
    print(f"  API docs: http://localhost:{BACKEND_PORT}/docs")
    print("Press Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
    )
