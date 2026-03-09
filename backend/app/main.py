from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import ApproveMissionRequest, MissionRecord, MissionStatus, MissionRequest
from app.services.mission_service import MissionService

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

missions = MissionService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.post("/api/plan-mission")
def plan_mission(payload: MissionRequest) -> dict:
    response = missions.plan_mission(payload)
    return response.model_dump(mode="json")


@app.post("/api/approve-mission/{mission_id}")
def approve_mission(mission_id: str, payload: ApproveMissionRequest) -> dict:
    try:
        response = missions.approve_mission(
            mission_id=mission_id,
            approved=payload.approved,
            commander_note=payload.commander_note,
        )
        return response.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Mission not found") from exc


@app.get("/api/missions/{mission_id}")
def get_mission(mission_id: str) -> dict:
    record: MissionRecord | None = missions.get_mission(mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return record.model_dump(mode="json")


@app.get("/api/missions/{mission_id}/status")
def mission_status(mission_id: str) -> dict:
    record = missions.get_mission(mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"mission_id": mission_id, "status": MissionStatus(record.status)}
