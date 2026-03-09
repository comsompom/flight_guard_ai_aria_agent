from __future__ import annotations

from datetime import UTC, datetime
import threading
import uuid

from app.models import (
    AgentTraceStep,
    ApproveMissionResponse,
    FlightPlanDocument,
    MissionAnalysis,
    MissionRecord,
    MissionRequest,
    MissionStatus,
    PlanMissionResponse,
)
from app.services.airia_client import AiriaClient
from app.services.document_service import DocumentService
from app.services.safety import calculate_takeoff, risk_from_conditions


class MissionService:
    def __init__(self) -> None:
        self._missions: dict[str, MissionRecord] = {}
        self._lock = threading.Lock()
        self._airia = AiriaClient()
        self._documents = DocumentService()

    def plan_mission(self, req: MissionRequest) -> PlanMissionResponse:
        context = {
            "operator_id": req.operator_id,
            "clearance_level": req.clearance_level,
            "drone_type": req.drone_type,
            "drone_weight_kg": req.drone_weight_kg,
            "wingspan_meters": req.wingspan_meters,
            "waypoints": [wp.model_dump() for wp in req.waypoints],
            "launch_mode_hint": req.launch_mode_hint,
        }
        prompt = self._build_router_prompt(req)
        raw_router = self._airia.execute_router(prompt=prompt, context=context)

        weather = raw_router["weather"]
        terrain = raw_router["terrain"]
        compliance = raw_router["compliance"]

        takeoff = calculate_takeoff(req.drone_type, weather["wind_direction_degrees"])
        risk_level, warnings = risk_from_conditions(
            wind_speed_m_s=weather["wind_speed_m_s"],
            zone_status=compliance["zone_status"],
            waypoint_count=len(req.waypoints),
        )

        trace = [
            AgentTraceStep(
                agent="FlightGuard Router",
                action="Delegated to specialist sub-agents",
                output={"sub_agents": ["Intel&Compliance", "METOC&Topo", "FlightOps"]},
            ),
            AgentTraceStep(
                agent="Intel&Compliance",
                action="Validated zone and license/cert requirements",
                output=compliance,
            ),
            AgentTraceStep(
                agent="METOC&Topo",
                action="Collected weather and terrain profiles",
                output={"weather": weather, "terrain_samples": terrain[:3]},
            ),
            AgentTraceStep(
                agent="FlightOps",
                action="Calculated launch recommendation from wind and drone type",
                output=takeoff,
            ),
        ]

        mission_brief = (
            f"Risk={risk_level}. Wind {weather['wind_speed_m_s']} m/s at "
            f"{weather['wind_direction_degrees']} deg. Zone={compliance['zone_status']}."
        )
        analysis = MissionAnalysis(
            status="AWAITING_HUMAN_APPROVAL",
            mission_brief=mission_brief,
            risk_level=risk_level,
            takeoff_recommendation=takeoff,
            weather=weather,
            terrain=terrain,
            compliance=compliance,
            agent_trace=trace,
            warnings=warnings,
        )

        mission_id = str(uuid.uuid4())
        record = MissionRecord(
            mission_id=mission_id,
            request=req,
            analysis=analysis,
            status=MissionStatus.pending_approval,
        )
        with self._lock:
            self._missions[mission_id] = record

        return PlanMissionResponse(
            mission_id=mission_id,
            status=record.status,
            analysis=record.analysis,
        )

    def approve_mission(self, mission_id: str, approved: bool, commander_note: str) -> ApproveMissionResponse:
        with self._lock:
            record = self._missions.get(mission_id)
            if record is None:
                raise KeyError("mission_not_found")

            if not approved:
                record.status = MissionStatus.aborted
                record.commander_note = commander_note
                return ApproveMissionResponse(
                    status=record.status,
                    message="Mission aborted by human commander.",
                )

            record.status = MissionStatus.approved
            record.commander_note = commander_note
            doc = FlightPlanDocument(
                mission_id=mission_id,
                status=record.status,
                authorizing_officer=record.request.operator_id,
                clearance_level=record.request.clearance_level,
                approved_by_human=True,
                commander_note=commander_note,
                waypoints=record.request.waypoints,
                launch_parameters=record.analysis.takeoff_recommendation,
                risk_level=record.analysis.risk_level,
                warnings=record.analysis.warnings,
                generated_at_utc=datetime.now(UTC).isoformat(),
                clearance_code=str(uuid.uuid4()).split("-")[0].upper(),
            )
            record.dynamic_document = doc
            file_path = self._documents.generate_flight_plan(doc)

        return ApproveMissionResponse(
            status=MissionStatus.approved,
            message="Mission approved and flight plan generated.",
            document_path=str(file_path),
            dynamic_document=doc,
        )

    def get_mission(self, mission_id: str) -> MissionRecord | None:
        with self._lock:
            return self._missions.get(mission_id)

    @staticmethod
    def _build_router_prompt(req: MissionRequest) -> str:
        return f"""
You are FlightGuard Router Agent for mission planning.
Operator: {req.operator_id}
Clearance: {req.clearance_level}
Drone: type={req.drone_type}, weight_kg={req.drone_weight_kg}, wingspan_m={req.wingspan_meters}
Waypoints: {[wp.model_dump() for wp in req.waypoints]}

Delegate:
1) Intel&Compliance -> zone legality, licenses/certificates
2) METOC&Topo -> weather, pressure, wind, elevation
3) FlightOps -> launch mode and heading recommendation

Stop and return a mission review package for human approval (HITL).
""".strip()
