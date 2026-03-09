# Airia Deployment Process (FlightGuard)

This guide documents the exact deployment and validation steps for the Airia-hosted `FlightGuard Orchestrator` agent.

---

## 1) Prerequisites

- Airia project created: `FlightGuard Mission Planner`
- Agent canvas created: `FlightGuard Orchestrator`
- Model configured (Claude Haiku 4.5 is acceptable)
- Two MCP deployments attached:
  - `Anthropic Sequential Thinking`
  - `AnyBrowse` (or equivalent web search/scrape MCP)

---

## 2) MCP Deployment Setup in Airia

## 2.1 Deploy Anthropic Sequential Thinking

1. In the agent config panel, open `MCP Servers`.
2. Click `Create new deployment`.
3. Search and choose `Anthropic Sequential Thinking`.
4. Fill:
   - Name: `FlightGuard_Sequential_Reasoner`
   - Description: `Structured mission risk reasoning`
   - Project: `FlightGuard Mission Planner`
   - Credential level: `Tenant`
5. Save configuration.
6. Ensure the `Sequentialthinking` tool is enabled.
7. Click `Create Deployment`.

## 2.2 Deploy AnyBrowse

1. In `MCP Servers`, create another deployment.
2. Search and choose `AnyBrowse`.
3. Fill:
   - Name: `FlightGuard_Web_Intel`
   - Description: `Live weather and airspace intelligence`
   - Project: `FlightGuard Mission Planner`
   - Credential level: `Tenant`
4. Save credentials/configuration.
5. Enable tools (recommended: all available for hackathon demo).
6. Click `Create Deployment`.

---

## 3) Recommended Model Settings

- Temperature: `0.1`
- Reasoning effort: `Balanced`
- Include chat history: `Do not include` (or very short window)
- Retry on failure: `ON`
- Include attachments: `OFF` unless you actively use file inputs

Important:
- Keep `Structured output` set to `OFF` for demo stability.
- During tests, `Structured output ON` produced schema/runtime validation errors in this setup.

---

## 4) System Prompt Baseline

Use a prompt that enforces:

1. Required mission inputs collection
2. Mandatory MCP usage for weather/airspace checks
3. Fixed-wing launch heading into wind
4. HITL gate with explicit `APPROVED` requirement before final authorization

Tip:
- Ask the model to return clear sections (Mission Summary, Findings, Risk, Next Steps, HITL Status).
- Do not require strict JSON schema in production demo runs.

## 4.1 Hardened Prompt (Copy/Paste)

Use this version to reduce repetitive clarification loops:

```text
You are FlightGuard Orchestrator, an enterprise mission-planning agent for drone operations.

MANDATORY INPUTS (collect once):
1) Operator ID/callsign, organization, clearance level
2) Drone type/model, weight (kg), wingspan (m if fixed-wing), max cruise speed
3) Mission date and start time (local or UTC)
4) Region/country and airspace class/context
5) Waypoints (lat, lon, altitude AGL, speed), plus takeoff/landing coordinates
6) Mission type and expected duration
7) Weather snapshot (wind speed + wind direction at minimum) and ATC/authorization status

TOOL POLICY:
- Use available MCP tools for live weather, terrain, and airspace/NOTAM checks.
- If tools fail, explicitly report failure and request only the minimum missing fallback values.
- Never invent external facts.

FLIGHT RULE:
- For fixed-wing drones, compute takeoff heading INTO the wind:
  heading = (wind_direction_degrees + 180) mod 360

HITL RULE:
- Do not authorize mission execution automatically.
- Always stop with: "Awaiting APPROVED".
- Finalize only after user sends exactly APPROVED.

QUESTION STYLE:
- If required fields are missing, ask ONCE with a compact checklist.
- After user responds, proceed directly to risk assessment and mission briefing.
```

---

## 5) Validation in Playground (Before Publishing)

1. Open Playground (left panel Play/Test).
2. Clear chat.
3. Send a mission request with partial data:

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
Please generate a pre-flight briefing and stop at the HITL gate.
```

4. Confirm the agent asks for missing mandatory fields.
5. Provide missing fields:

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

after agent response input this:
```text
Missing mission details:

1) Operator Identification
Operator name/callsign: OP-774
Organization/company: FlightGuard Test Unit

2) Mission Location & Airspace
Region/country: Paris, France (Ile-de-France)
Mission date: 2026-03-09
Takeoff coordinate: 48.8566, 2.3522
Landing coordinate: 48.8740, 2.3900
Operating altitude window: 80–100 m AGL
Waypoints:
- WP1: 48.8566, 2.3522, 80m AGL, 12 m/s
- WP2: 48.8666, 2.3700, 90m AGL, 12 m/s
- WP3: 48.8740, 2.3900, 100m AGL, 10 m/s

3) Mission Scope
Operation type: Aerial survey
Duration: 25 minutes
Drone type designation: Fixed-wing UAV (recon class)

4) Airspace Clarification
ATC pre-cleared class: Class D (Paris CTR)
Nearby restrictions: No active TFR known at briefing time; request live NOTAM confirmation
Nearby airport context: Paris CTR environment, controlled airspace

Proceed with live weather/terrain/airspace checks, compute fixed-wing takeoff heading, produce risk briefing, and stop at HITL gate awaiting APPROVED.
```

Then after it returns briefing + “awaiting approval”, send:

```text
APPROVED
```

6. Confirm output contains:
   - Updated risk level
   - Takeoff heading logic
   - Explicit HITL hold (`Awaiting APPROVED`)
7. Send `APPROVED`.
8. Confirm final mission authorization summary.

## Optional: One-shot Mission Request (Preferred for demos)

To avoid extra follow-up questions, use this complete request in one message:

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

Do not publish until the full interaction succeeds once end-to-end.

---

## 6) Publish Steps

1. Click `Publish` in top-right.
2. Set visibility to public/community per hackathon requirement.
3. Copy public URL.
4. Add URL to Devpost project links.

---

## 7) Known Issues and Mitigation

## Issue A: `invalid_request_error` / empty text content block

Mitigation:
- Clear chat
- Disable chat history
- Disable structured output

## Issue B: Structured output schema validation errors

Mitigation:
- Keep structured output OFF for demo
- Use sectioned plain-text output format

## Issue C: MCP web tools temporarily unavailable

Mitigation:
- Keep retry ON
- Let agent report tool status and request operator-provided weather fallback

---

## 8) Go/No-Go Checklist

- [ ] MCP Servers attached: Sequential Thinking + AnyBrowse
- [ ] Retry on failure ON
- [ ] Structured output OFF
- [ ] End-to-end Playground test passed
- [ ] Agent published
- [ ] Public URL copied for submission
