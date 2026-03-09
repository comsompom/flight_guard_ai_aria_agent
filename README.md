# FlightGuard Agent (Airia Hackathon)

![FlightGuard Agent](./fg_logo.jpg)

FlightGuard Agent is a military/defense-focused AI mission planner for drone operators (plane, fixed-wing UAV, quadcopter).  
It implements the exact hackathon flow from `solution.md`:

- Multi-agent orchestration (Router + specialist agents)
- MCP tool integration (weather, terrain, compliance, takeoff vectors)
- Human-in-the-Loop (HITL) mission authorization
- Dynamic mission document generation (`flight_plan.json`)

---

## 1) What This Solves

Commercial and defense teams usually check weather, terrain, airspace legality, and launch strategy manually across multiple systems.  
FlightGuard compresses that workflow into one command-and-control flow:

1. Operator sets waypoints on map.
2. AI router gathers mission intelligence and safety analysis.
3. System pauses for commander decision (GO / NO-GO).
4. On approval, final mission document is generated.

---

## 2) Architecture

### Components

- `frontend/`  
  Map-based mission console (Leaflet + vanilla JS).
- `backend/app/`  
  FastAPI orchestration layer and HITL state machine.
- `mcp_server/server.py`  
  MCP tools for weather/elevation/compliance/takeoff calculations.
- `artifacts/`  
  Generated mission outputs (`flight_plan_*.json`).

### Multi-Agent Model (Implemented in Backend Trace)

The backend explicitly models the following specialist roles and returns an `agent_trace`:

- **FlightGuard Router**: delegates mission tasks.
- **Intel&Compliance**: validates zone status and required certificates.
- **METOC&Topo**: provides weather and terrain profile.
- **FlightOps**: computes launch mode and heading recommendation.

### HITL Gate

The system does **not** authorize execution at planning time.

- `POST /api/plan-mission` -> returns `PENDING_APPROVAL`
- `POST /api/approve-mission/{mission_id}` -> `approved=true` required for final document generation

---

## 3) API Endpoints

- `GET /health`  
  Service health.
- `POST /api/plan-mission`  
  Creates mission review package for human approval.
- `POST /api/approve-mission/{mission_id}`  
  Human command decision: approve/abort.
- `GET /api/missions/{mission_id}`  
  Full mission record.
- `GET /api/missions/{mission_id}/status`  
  Mission status only.

---

## 4) Quick Start (Local)

### Prerequisites

- Python 3.11+
- Optional: Docker Desktop for `docker compose` run

### A) Python Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run backend:

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

Open:

- Frontend: `http://localhost:8080`
- API docs: `http://localhost:8000/docs`

### B) Docker Compose Run

```powershell
Copy-Item .env.example .env
docker compose up --build
```

---

## 5) Demo Flow (4-Minute Pitch Ready)

1. Open frontend, enter operator/clearance/drone details.
2. Click map to place 3-5 waypoints.
3. Click **Generate Flight Plan**.
4. Show returned mission review:
   - weather, pressure, wind direction
   - terrain/elevation profile
   - compliance/license requirements
   - takeoff recommendation (fixed-wing launches into wind)
5. Click **Authorize Mission** (HITL).
6. Show returned `dynamic_document` and generated JSON in `artifacts/`.

---

## 6) Airia Integration Notes

The backend supports two modes:

1. **Demo mode (default)**  
   Deterministic local simulation for stable hackathon demo behavior.
2. **Live Airia mode**  
   Set `AIRIA_API_URL` and `AIRIA_API_KEY` (from Agent Settings > Interfaces > API).

**Weather and elevation (no registration):**  
The backend and MCP server use **Open-Meteo** (weather) and **Open-Elevation** (terrain) by default—no API key or signup required. Temperature, pressure, wind, and earth heights are fetched automatically for mission waypoints. Telemetry is collected **asynchronously in parallel** (one weather request + one batch elevation request) to minimize latency. Optionally set `OPENWEATHER_API_KEY` to use OpenWeather instead; `OPEN_TOPO_BASE_URL` is only used as a fallback if Open-Elevation is unavailable.

---

## 7) Airia Deployment + Demo Runbook

For the exact Airia setup and test flow used in this project:

- `docs/airia_deployment_process.md`
- `docs/demo_script_and_instructions.md`
- `docs/airia_full_creation_process.md`
- `docs/video_presentation_guide.md` — step-by-step silent demo video for the hackathon

These docs include:
- MCP deployment choices and settings
- Stable model settings
- Step-by-step Playground prompts
- HITL approval walkthrough
- Troubleshooting for structured output/tool failures

---

## 8) Security and Production Hardening (Post-Hackathon)

- Replace in-memory mission store with Redis/PostgreSQL.
- Add authentication and role-based access control.
- Add signed approval audit trails.
- Restrict CORS and protect APIs behind gateway + TLS.
- Add persistent Airia Memory integration for operator/drone profile reuse.

---

## 9) Repository Layout

```text
requirements.txt
.env.example
docker-compose.yml
Dockerfile.backend
Dockerfile.mcp
Dockerfile.frontend
backend/
  app/
    main.py
    config.py
    models.py
    services/
      airia_client.py
      mission_service.py
      document_service.py
      open_weather_elevation.py
      safety.py
mcp_server/
  server.py
frontend/
  index.html
  app.js
  styles.css
docs/
  architecture.md
  deployment.md
  airia_deployment_process.md
  airia_full_creation_process.md
  demo_script_and_instructions.md
  video_presentation_guide.md
solution.md
```

---

## 10) Why This Matches the Solution

From your solution requirements, this implementation includes:

- Drone mission planning with map-based waypoint capture
- Weather, pressure, wind direction, terrain/elevation analysis
- Airspace and compliance checks (mock-ready, API-upgradeable)
- Flight profile logic for plane/fixed-wing/quadcopter/UAV
- Human-in-the-loop approval gate
- Dynamic mission document generation for operational handoff

It is ready for hackathon demo execution and extensible for real defense integrations.
