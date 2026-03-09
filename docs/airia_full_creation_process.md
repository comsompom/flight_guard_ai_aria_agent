# Full Airia Agent Creation Process (Start to Finish)

This document captures the complete process used to create and stabilize the `FlightGuard Orchestrator` agent in Airia, from first setup to final publish-ready validation.

---

## 1) Goal and Initial Scope

The target was to build a hackathon-ready enterprise drone planning agent with:

- Multi-agent style orchestration behavior
- Live external intelligence via MCP servers
- Human-in-the-Loop (HITL) approval gate
- A deterministic, demo-safe workflow for judges

The final workflow had to support:

1. Mission request intake
2. Safety/airspace/weather reasoning
3. Missing-input collection
4. Takeoff heading logic
5. Explicit `APPROVED` gate
6. Final mission summary

---

## 2) Project and Agent Initialization

## 2.1 Create project

In Airia Studio:

1. Open `Projects`
2. Create project `FlightGuard Mission Planner`
3. Set enterprise-focused description
4. Save project

## 2.2 Create agent

Inside the project:

1. Click `Add a New Agent`
2. Keep simple canvas:
   - `Input` -> `AI Model` -> `Output`
3. Rename agent to `FlightGuard Orchestrator`

Model remained `Claude Haiku 4.5` due workspace constraints; this was acceptable for speed and reliability.

---

## 3) Initial Prompt and Model Controls

A baseline system prompt was added to enforce:

- Required mission inputs (operator, drone, waypoints, timing)
- Mandatory tool usage for weather/airspace checks
- Fixed-wing takeoff into wind logic
- HITL stop before final authorization

Model settings used:

- Temperature: `0.1`
- Reasoning effort: `Balanced`
- Include chat history: `Do not include` (for cleaner test payloads)
- Retry on failure: `ON`

---

## 4) MCP Server Discovery and Selection

## 4.1 Initial options considered

The marketplace exploration included:

- `Mapbox DevKit`
- `Tavily`
- Other catalog servers

Observed issue:
- Some deployments (notably Mapbox in this run) showed `No tools available for this server` after credential setup, making them unusable for the demo.

## 4.2 Final MCP stack selected

To keep setup simple and working:

1. `Anthropic Sequential Thinking`
   - Role: structured risk reasoning and planning logic
2. `AnyBrowse`
   - Role: live search/crawl/scrape for weather/airspace intelligence

This pair gave the best setup speed and practical coverage.

---

## 5) MCP Deployment Configuration Used

## 5.1 Anthropic Sequential Thinking deployment

- Name: `FlightGuard_Sequential_Reasoner`
- Project: `FlightGuard Mission Planner`
- Credential Level: `Tenant`
- Tools: `Sequentialthinking` enabled (1/1)

## 5.2 AnyBrowse deployment

- Name: `FlightGuard_Web_Intel`
- Project: `FlightGuard Mission Planner`
- Credential Level: `Tenant`
- Credentials: configured successfully
- Tools: all selected for demo flexibility (`Search`, `Crawl`, `Scrape`, etc.)

Both deployments were attached to the model (`MCP Servers (2)` visible).

---

## 6) Structured Output Attempt and Failure Pattern

Structured JSON output was enabled and a schema was created, but repeated runtime failures occurred:

- `invalid_request_error` related to empty text content blocks
- `JsonSchema.Net expected object` validation/runtime issues

Even with history disabled and clean prompts, failures persisted when structured output/schema was ON.

Root practical conclusion:
- In this specific tool-heavy Airia run, strict structured schema reduced reliability.

---

## 7) Stabilization Steps That Worked

The stable configuration that restored execution:

1. `Structured output` -> `OFF`
2. `Include attachments` -> `OFF` (unless needed)
3. `Include chat history` -> `Do not include`
4. `Retry on failure` -> `ON`
5. Keep sectioned prompt format (plain text output with fixed headings)

After this, Playground runs completed successfully.

---

## 8) End-to-End Playground Validation Flow

The validation sequence executed:

1. Send mission request with partial details
2. Agent returns preliminary briefing and requests missing safety-critical data
3. Provide missing fields (clearance, drone specs, weather, timing, ATC status)
4. Agent computes risk and fixed-wing takeoff heading
5. Agent pauses at HITL gate with explicit approval requirement
6. Send `APPROVED`
7. Agent finalizes mission summary

Observed behavior:
- Tool status could degrade temporarily (search/crawl service unavailable), but the agent handled fallback and continued controlled workflow.

---

## 9) Final Publish-Ready State

The final publish-ready configuration was:

- Model: Claude Haiku 4.5
- MCP servers: Sequential Thinking + AnyBrowse
- Temperature: 0.1
- Retry on failure: ON
- Structured output: OFF
- Prompt: sectioned, HITL-enforcing, tool-aware

This state is stable for demo/video/judge interaction.

---

## 10) Recommended Operator Script (Short)

1. Submit mission request with waypoints and partial details
2. Let agent request missing mandatory fields
3. Provide missing operator/drone/weather inputs
4. Review risk + takeoff heading output
5. Send `APPROVED`
6. Capture final mission authorization response

---

## 11) Related Documents

- `docs/airia_deployment_process.md` - deployment checklist and settings
- `docs/demo_script_and_instructions.md` - exact prompts and demo flow
- `README.md` - project overview and execution entry points
