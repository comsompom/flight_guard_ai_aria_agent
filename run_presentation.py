#!/usr/bin/env python3
"""
Run backend and frontend for the demo. The backend serves the map UI at http://localhost:8000.
One process, one port. Press Ctrl+C to stop.
"""
import os
import socket
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 8000


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def get_pids_on_port(port: int) -> list[int]:
    """On Windows, return PIDs that are listening on the given port."""
    pids = []
    try:
        kwargs = {"capture_output": True, "text": True, "timeout": 5}
        if sys.platform == "win32":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        out = subprocess.run(["netstat", "-ano"], **kwargs)
        if out.returncode != 0:
            return pids
        for line in out.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    try:
                        pids.append(int(parts[-1]))
                    except ValueError:
                        pass
    except Exception:
        pass
    return list(dict.fromkeys(pids))  # unique, keep order


if __name__ == "__main__":
    os.chdir(REPO_ROOT)  # ensure frontend/ is found relative to repo root

    if port_in_use(BACKEND_PORT):
        print(f"Port {BACKEND_PORT} is already in use.\n")
        pids = get_pids_on_port(BACKEND_PORT)
        if pids:
            print("Process(es) using the port:", ", ".join(str(p) for p in pids))
            if sys.platform == "win32" and "--kill" in sys.argv:
                for pid in pids:
                    try:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, timeout=5)
                        print(f"  Stopped PID {pid}")
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        print(f"  Could not stop PID {pid} (try running as Administrator)")
                time.sleep(1)
                if port_in_use(BACKEND_PORT):
                    print("Port still in use. Run again:  python run_presentation.py --kill")
                    sys.exit(1)
                print("Port free. Starting server...\n")
            else:
                print("\nTo free the port, either:")
                print("  1. Run:  python run_presentation.py --kill")
                print("  2. Or in a new terminal run:  taskkill /PID <PID> /F")
                print("     Then run:  python run_presentation.py")
                sys.exit(1)
        else:
            print(f"Could not detect which process uses port {BACKEND_PORT}.")
            print("Close other terminals or apps that might use it, then run again.")
            sys.exit(1)

    # Add backend to path so "app" module is found
    backend_dir = os.path.join(REPO_ROOT, "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("Starting FlightGuard (API + map UI)...")
    print(f"  Map UI:  http://localhost:{BACKEND_PORT}/   or  http://localhost:{BACKEND_PORT}/map")
    print(f"  Check:   http://localhost:{BACKEND_PORT}/ping   (should show pong)")
    print(f"  API:     http://localhost:{BACKEND_PORT}/docs")
    print("Press Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
    )
