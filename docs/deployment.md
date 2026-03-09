# Deployment Guide

## 1) Local Run (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run API:

```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run frontend:

```powershell
python -m http.server 8080 --directory frontend
```

Optional MCP server (from repo root; requires `backend` and `mcp_server` on PYTHONPATH):

```powershell
$env:PYTHONPATH="."
python mcp_server/server.py
```

## 2) Docker Deployment

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Services:
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`

## 3) Environment Variables

- `AIRIA_API_URL`, `AIRIA_API_KEY`: enable live Airia Pipeline Execution (v2). Get URL and key from Agent Settings > Interfaces > API.
- Weather and elevation use **Open-Meteo** and **Open-Elevation** by default (no key). Optionally `OPENWEATHER_API_KEY` uses OpenWeather in MCP; `OPEN_TOPO_BASE_URL` is fallback if Open-Elevation is unavailable.

## 4) Production Notes

- Replace in-memory mission store with Redis/PostgreSQL.
- Add authentication (JWT/OIDC) for military deployment.
- Restrict CORS to trusted origins.
- Enable TLS and API gateway policies.
- Add audit logging for all approval actions (HITL compliance).

## 5) See Also

- `docs/architecture.md` — component overview and data flow
- `docs/airia_deployment_process.md` — Airia agent and MCP setup
- `docs/demo_script_and_instructions.md` — Playground prompts and test flow
- `docs/video_presentation_guide.md` — silent demo video for hackathon
