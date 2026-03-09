# Demo Script and Instructions (FlightGuard)

Playground prompts and test flow for live testing, judging walkthrough, and video capture.

---

## 1) Demo Objective

Show a full Human-in-the-Loop mission cycle:

1. Mission request (full or partial)
2. Agent returns briefing and may ask for missing inputs; holds at HITL gate
3. If needed: provide missing inputs
4. Agent computes risk and takeoff heading; shows **Awaiting APPROVED**
5. Operator sends `APPROVED`
6. Agent finalizes mission summary

---

## 2) Environment (Optional Local Stack)

If you demo local backend/frontend:

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

- Frontend: `http://localhost:8080`
- API docs: `http://localhost:8000/docs`

---

## 3) Airia Playground Prompts (Copy/Paste)

### Option A: One-shot mission request (recommended for demos/video)

Paste this **once** in the Airia Playground. The agent should return a full briefing and stop at HITL.

```text
Mission request (complete):
Operator ID/callsign: OP-774
Organization: FlightGuard Test Unit
Operator clearance: EASA Category A3 with local authorization

Drone type/model: Fixed-wing UAV (recon class)
Drone weight: 2.0 kg
Wingspan: 1.6 m
Max cruise speed: 18 m/s

Mission type: Aerial survey
Duration: 25 minutes
Mission date: 2026-03-10
Mission start time: 09:00 local
Region/country: Paris, France (Ile-de-France)
Airspace class/context: Class D (Paris CTR), ATC pre-cleared

Takeoff: 48.8566, 2.3522
Landing: 48.8740, 2.3900
Operating altitude window: 80-100m AGL
Waypoints:
- WP1: 48.8566, 2.3522, 80m AGL, 12 m/s
- WP2: 48.8666, 2.3700, 90m AGL, 12 m/s
- WP3: 48.8740, 2.3900, 100m AGL, 10 m/s

Weather snapshot:
- Wind speed: 6 m/s
- Wind direction: 270 degrees
- Visibility: 10 km
- Cloud ceiling: 2500 ft AGL

Required output:
1) Mission Summary
2) Tool Calls Performed
3) Findings (Weather/Terrain/Airspace)
4) Takeoff heading for fixed-wing
5) Risk level with reasons
6) HITL gate with exact text: Awaiting APPROVED
```

Then after the agent responds with the briefing and **Awaiting APPROVED**, send:

```text
APPROVED
```

---

### Option B: Two-step flow (partial request, then missing details)

**Prompt 1 — Mission request (partial):**

```text
Mission request:
Operator ID: OP-774
Aircraft type: Fixed-wing UAV
Waypoints:
1) 48.8566,2.3522,80m AGL, 12m/s
2) 48.8666,2.3700,90m AGL, 12m/s
3) 48.8740,2.3900,100m AGL, 10m/s
Mission date: 2026-03-10
Region: Paris CTR
Please generate pre-flight briefing and stop at HITL gate.
```

**Prompt 2 — Missing inputs (if agent asks):**

```text
Missing inputs:
Operator clearance level: EASA Category A3 with local authorization
Drone weight: 2.0 kg
Wingspan: 1.6 m
Max cruise speed: 18 m/s
Planned mission start time: 09:00 local
Live weather:
- Wind speed: 6 m/s
- Wind direction: 270 degrees
- Visibility: 10 km
- Cloud ceiling: 2500 ft AGL
ATC coordination: Pre-cleared
```

**If agent still asks for operator/location details (Prompt 2B):**

```text
Missing mission details:
Operator name/callsign: OP-774
Organization/company: FlightGuard Test Unit
Region/country: Paris, France (Ile-de-France)
Takeoff coordinate: 48.8566, 2.3522
Landing coordinate: 48.8740, 2.3900
Operating altitude window: 80-100m AGL
Mission type: Aerial survey
Duration: 25 minutes
Drone designation: Fixed-wing UAV (recon class)
Airspace class: Class D (Paris CTR), ATC pre-cleared
Nearby restrictions: Request live NOTAM/TFR confirmation
```

**Prompt 3 — HITL approval:**

```text
APPROVED
```

---

## 4) What to Expect

- After mission request: preliminary briefing, possibly a request for missing fields.
- After missing data (if any): risk level, takeoff heading (fixed-wing into wind), **Awaiting APPROVED**.
- After `APPROVED`: final mission authorization summary.

---

## 5) Troubleshooting

- **Tool calls fail:** Keep Retry on failure ON; agent can request operator-provided weather/airspace.
- **Output errors:** Keep Structured output OFF; use sectioned plain-text format; clear chat and rerun.

---

## 6) Pre-Publish Checklist

- [ ] Playground run completed end-to-end
- [ ] HITL `APPROVED` gate confirmed
- [ ] MCP servers attached and active
- [ ] Agent saved and published
- [ ] Public URL copied into Devpost

---

## See also

- `docs/airia_deployment_process.md` — deployment and one-shot prompt in validation section
- `docs/video_presentation_guide.md` — silent demo video steps and same one-shot prompt
