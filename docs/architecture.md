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
   - Uses Open-Meteo and Open-Elevation by default (no API key); optional OpenWeather.

4. **Weather & elevation** (`backend/app/services/open_weather_elevation.py`)
   - Fetches real temperature, pressure, wind, and terrain elevation.
   - Async parallel fetching (one weather + one batch elevation request) for speed.

5. **Airia Pipeline Integration**
   - If `AIRIA_API_URL` and `AIRIA_API_KEY` are set, backend calls Airia Pipeline Execution API (v2) with `X-API-KEY` header.
   - Otherwise local flow with real Open-Meteo/Open-Elevation data is used for demos.

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
