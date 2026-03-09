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

Optional MCP server:

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

- `AIRIA_API_URL`, `AIRIA_API_KEY`: enables live Router execution.
- `OPENWEATHER_API_KEY`: enables live weather in MCP weather tool.
- `OPEN_TOPO_BASE_URL`: elevation source (default OpenTopoData).

## 4) Production Notes

- Replace in-memory mission store with Redis/PostgreSQL.
- Add authentication (JWT/OIDC) for military deployment.
- Restrict CORS to trusted origins.
- Enable TLS and API gateway policies.
- Add audit logging for all approval actions (HITL compliance).
