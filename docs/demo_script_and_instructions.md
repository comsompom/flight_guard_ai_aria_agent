# Demo Script and Instructions (FlightGuard)

Use this script for live testing, judging walkthrough, and video capture.

---

## 1) Demo Objective

Show a full Human-in-the-Loop mission cycle:

1. Mission request (partial)
2. Agent asks missing inputs and holds at HITL gate
3. Operator provides missing inputs
4. Agent computes risk and takeoff heading
5. Operator sends `APPROVED`
6. Agent finalizes mission summary

---

## 2) Environment Instructions (Optional Local Stack)

If you demo local backend/frontend as companion app:

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

---

## 3) Airia Playground Prompt Script (Copy/Paste)

## Prompt 0: One-time instruction hardening (recommended)

Paste once at session start:

```text
Use this execution policy for this chat:
- If required fields are missing, ask once with a compact checklist only.
- After missing data is provided, proceed directly to briefing.
- For fixed-wing, compute takeoff heading into wind: (wind_direction + 180) mod 360.
- Do not auto-authorize; always stop at HITL with exact phrase: Awaiting APPROVED.
```

## Prompt 1: Mission request (intentionally incomplete)

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

Expected:
- Agent returns preliminary briefing.
- Agent asks for missing required fields (clearance, aircraft specs, wind/timing/ATC as needed).
- Agent does not authorize mission yet.

## Prompt 2: Provide missing inputs

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

Expected:
- Agent updates risk rating.
- Agent computes fixed-wing takeoff heading into wind.
- Agent explicitly says `Awaiting APPROVED`.

## Optional Prompt 2B: Provide full missing details in one block

If the agent asks for operator identity/location scope details, use:

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

## Prompt 3: HITL approval

```text
APPROVED
```

Expected:
- Agent finalizes mission authorization summary.
- Provides final risk posture and key operational constraints.

---

## 4) Judge-Facing Narration (Short Version)

Use this while operating:

1. "I submit a mission with waypoints and partial operator details."
2. "The agent checks completeness, then requests missing safety-critical inputs."
3. "After I provide clearance, aircraft specs, weather, and ATC status, it recalculates mission risk."
4. "For fixed-wing, it computes takeoff heading into wind."
5. "The system enforces Human-in-the-Loop; it halts until I type APPROVED."
6. "Once approved, it outputs the final mission summary."

---

## 5) Troubleshooting During Demo

## If tool calls fail temporarily

- Keep `Retry on failure` ON.
- Allow fallback: agent requests operator-provided weather/airspace values.
- Continue demo with explicit "tool recovery pending" note.

## If output formatting errors occur

- Keep `Structured output` OFF.
- Keep sectioned plain-text response format.
- Clear chat and rerun prompt sequence.

---

## 6) Final Pre-Publish Checklist

- [ ] Playground run completed end-to-end
- [ ] HITL `APPROVED` gate confirmed
- [ ] MCP servers connected and active
- [ ] Agent saved and published
- [ ] Public URL copied into Devpost
