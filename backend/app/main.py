import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.config import settings
from app.models import ApproveMissionRequest, MissionRecord, MissionStatus, MissionRequest
from app.services.mission_service import MissionService

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

missions = MissionService()

# Frontend dir: try from this file's location, then from cwd (e.g. repo root)
def _frontend_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "frontend",
        Path(os.getcwd()) / "frontend",
        Path(os.getcwd()).parent / "frontend",
    ]
    for d in candidates:
        if d.is_dir() and (d / "index.html").exists():
            return d
    return candidates[0]  # fallback so mount still runs if dir created later

_FRONTEND_DIR = _frontend_dir()

# Pre-read index.html so root always serves HTML (avoids path/FileResponse issues)
_INDEX_HTML: str | None = None


def _read_index_html() -> str:
    global _INDEX_HTML
    if _INDEX_HTML is None:
        index_path = _FRONTEND_DIR / "index.html"
        if not index_path.is_file():
            raise RuntimeError(f"Frontend index not found: {index_path}")
        _INDEX_HTML = index_path.read_text(encoding="utf-8")
    return _INDEX_HTML


@app.on_event("startup")
def _log_frontend_path():
    index = _FRONTEND_DIR / "index.html"
    import sys
    print(f"[FlightGuard] Frontend dir: {_FRONTEND_DIR}", file=sys.stderr)
    print(f"[FlightGuard] index.html exists: {index.exists()}", file=sys.stderr)
    if index.exists():
        _read_index_html()
        print("[FlightGuard] Root (/) will serve map UI", file=sys.stderr)


def _safe_frontend_file(filename: str) -> FileResponse:
    """Serve a file from frontend dir; 404 if missing."""
    path = _FRONTEND_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(str(path))


@app.get("/ping")
def ping():
    """Verify you're hitting this server: returns pong."""
    return {"message": "pong", "service": "FlightGuard"}


@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Serve map UI at root."""
    return HTMLResponse(content=_read_index_html())


@app.get("/map", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
def serve_map_alt():
    """Same map UI at /map and /app in case root (/) is not matched."""
    return HTMLResponse(content=_read_index_html())


@app.get("/index.html", response_class=FileResponse)
def serve_index_html():
    return _safe_frontend_file("index.html")


@app.get("/styles.css", response_class=FileResponse)
def serve_css():
    return _safe_frontend_file("styles.css")


@app.get("/app.js", response_class=FileResponse)
def serve_js():
    return _safe_frontend_file("app.js")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.post("/api/plan-mission")
def plan_mission(payload: MissionRequest) -> dict:
    response = missions.plan_mission(payload)
    return response.model_dump(mode="json")


@app.post("/api/approve-mission/{mission_id}")
def approve_mission(mission_id: str, payload: ApproveMissionRequest) -> dict:
    try:
        response = missions.approve_mission(
            mission_id=mission_id,
            approved=payload.approved,
            commander_note=payload.commander_note,
        )
        return response.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Mission not found") from exc


@app.get("/api/missions/{mission_id}")
def get_mission(mission_id: str) -> dict:
    record: MissionRecord | None = missions.get_mission(mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return record.model_dump(mode="json")


@app.get("/api/missions/{mission_id}/status")
def mission_status(mission_id: str) -> dict:
    record = missions.get_mission(mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"mission_id": mission_id, "status": MissionStatus(record.status)}


# Fallback: serve frontend for any other GET (so / always works even if root route is skipped)
@app.get("/{path:path}", response_class=HTMLResponse)
def serve_frontend_fallback(path: str):
    if path.startswith("api/") or path in ("docs", "redoc", "openapi.json", "health", "ping"):
        raise HTTPException(status_code=404, detail="Not Found")
    return HTMLResponse(content=_read_index_html())
