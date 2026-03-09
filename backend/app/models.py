from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MissionStatus(str, Enum):
    pending_approval = "PENDING_APPROVAL"
    approved = "APPROVED"
    aborted = "ABORTED"


class Waypoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    alt_m: float = Field(ge=0, description="Altitude above ground level in meters.")
    speed_m_s: float = Field(default=10.0, gt=0)


class MissionRequest(BaseModel):
    operator_id: str = Field(min_length=2, max_length=80)
    clearance_level: str = Field(default="UNSPECIFIED", max_length=40)
    drone_type: str = Field(description="plane | fixed-wing | quadcopter | uav")
    drone_weight_kg: float = Field(gt=0)
    wingspan_meters: float = Field(default=0.0, ge=0.0)
    waypoints: list[Waypoint] = Field(min_length=1)
    launch_mode_hint: str = Field(
        default="auto", description="auto | catapult | wheels | vtol"
    )

    @field_validator("drone_type")
    @classmethod
    def normalize_drone_type(cls, v: str) -> str:
        return v.strip().lower()


class AgentTraceStep(BaseModel):
    agent: str
    action: str
    output: dict[str, Any]


class MissionAnalysis(BaseModel):
    status: str
    mission_brief: str
    risk_level: str
    takeoff_recommendation: dict[str, Any]
    weather: dict[str, Any]
    terrain: list[dict[str, Any]]
    compliance: dict[str, Any]
    agent_trace: list[AgentTraceStep]
    warnings: list[str]


class PlanMissionResponse(BaseModel):
    mission_id: str
    status: MissionStatus
    analysis: MissionAnalysis


class ApproveMissionRequest(BaseModel):
    approved: bool
    commander_note: str = Field(default="", max_length=400)


class FlightPlanDocument(BaseModel):
    document_type: str = "FlightGuard Pre-Flight Briefing"
    mission_id: str
    status: MissionStatus
    authorizing_officer: str
    clearance_level: str
    approved_by_human: bool
    commander_note: str
    waypoints: list[Waypoint]
    launch_parameters: dict[str, Any]
    risk_level: str
    warnings: list[str]
    generated_at_utc: str
    clearance_code: str


class ApproveMissionResponse(BaseModel):
    status: MissionStatus
    message: str
    document_path: str | None = None
    dynamic_document: FlightPlanDocument | None = None


class MissionRecord(BaseModel):
    mission_id: str
    request: MissionRequest
    analysis: MissionAnalysis
    status: MissionStatus
    commander_note: str = ""
    dynamic_document: FlightPlanDocument | None = None
