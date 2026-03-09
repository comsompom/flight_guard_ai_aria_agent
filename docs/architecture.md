# FlightGuard Architecture

## Core Components

1. **Frontend Mission Console** (`frontend/`)
   - Operator enters mission metadata.
   - Click-to-place waypoints on map.
   - Displays mission review and executes HITL approval.

2. **FlightGuard Backend API** (`backend/app/`)
   - Exposes mission planning and approval endpoints.
   - Orchestrates simulated multi-agent flow:
     - Intel&Compliance
     - METOC&Topo
     - FlightOps
   - Stores pending missions and generates final `flight_plan.json`.

3. **MCP Tool Server** (`mcp_server/server.py`)
   - Exposes tools for weather, terrain, compliance, and takeoff vectors.
   - Can use mock mode or external APIs.

4. **Airia Router Integration**
   - If `AIRIA_API_URL` and `AIRIA_API_KEY` are set, backend calls Router endpoint.
   - Otherwise local deterministic simulation is used for demos.

## HITL Control Point

`POST /api/plan-mission` returns `PENDING_APPROVAL` and mission review package.
Only `POST /api/approve-mission/{mission_id}` with `approved=true` generates final dynamic document.

## Mission Output

- Generated artifact in `artifacts/flight_plan_<mission_id>_<timestamp>.json`
- Includes:
  - Commander identity/clearance
  - Waypoint plan
  - Launch parameters
  - Risk and warnings
  - Clearance code
