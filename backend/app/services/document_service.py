from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json

from app.models import FlightPlanDocument


class DocumentService:
    def __init__(self, artifacts_dir: str = "artifacts") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def generate_flight_plan(self, document: FlightPlanDocument) -> Path:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        file_path = self.artifacts_dir / f"flight_plan_{document.mission_id}_{ts}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(document.model_dump(mode="json"), f, indent=2)
        return file_path
