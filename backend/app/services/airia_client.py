from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import random
from typing import Any

import requests

from app.config import settings


@dataclass
class AiriaClient:
    """
    Small adapter around Airia Router API.
    Falls back to deterministic local simulation for hackathon demos.
    """

    def execute_router(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        if settings.airia_api_url and settings.airia_api_key:
            return self._execute_remote(prompt, context)
        return self._execute_local_simulation(context)

    def _execute_remote(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        user_input = f"{prompt}\n\nContext (JSON):\n{json.dumps(context, indent=2)}"
        payload = {
            "userInput": user_input,
            "asyncOutput": False,
        }
        headers = {
            "X-API-KEY": settings.airia_api_key,
            "Content-Type": "application/json",
        }
        response = requests.post(
            settings.airia_api_url,
            headers=headers,
            json=payload,
            timeout=settings.airia_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return self._normalize_airia_response(data, context)

    def _normalize_airia_response(self, data: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Map Airia v2 pipeline execution response to our expected weather/terrain/compliance shape.
        If the response is plain text or unknown shape, fill from local simulation so the pipeline still runs.
        """
        waypoints = context.get("waypoints", [])
        first_wp = waypoints[0] if waypoints else {"lat": 0.0, "lon": 0.0}
        seed_input = (
            f'{first_wp.get("lat", 0):.4f}:{first_wp.get("lon", 0):.4f}:{context.get("operator_id", "")}'
        )
        seed = int(hashlib.sha256(seed_input.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        default_weather = {
            "temperature_celsius": round(rng.uniform(-5.0, 35.0), 1),
            "pressure_hpa": round(rng.uniform(995, 1024), 1),
            "wind_speed_m_s": round(rng.uniform(1.5, 20), 1),
            "wind_direction_degrees": int(rng.uniform(0, 359)),
            "source": "airia_fallback",
        }
        default_terrain = [
            {"lat": wp.get("lat", 0), "lon": wp.get("lon", 0), "elevation_meters": round(rng.uniform(30, 1200), 1)}
            for wp in waypoints
        ]
        default_compliance = {
            "zone_status": "CLEARED" if rng.random() > 0.15 else "RESTRICTED",
            "max_altitude_agl_meters": 120,
            "allowed_drone_types": ["quadcopter", "uav_fixed_wing", "plane", "uav"],
            "required_certificates": ["Mission Ops Certificate", "BVLOS Endorsement"],
            "license_check": "PASS",
        }
        out = data.get("output") or data.get("result") or data.get("message") or data
        if isinstance(out, str):
            return {
                "simulated_at": datetime.now(UTC).isoformat(),
                "airia_output": out,
                "weather": default_weather,
                "terrain": default_terrain,
                "compliance": default_compliance,
            }
        if isinstance(out, dict):
            return {
                "simulated_at": datetime.now(UTC).isoformat(),
                "weather": out.get("weather") or default_weather,
                "terrain": out.get("terrain") or default_terrain,
                "compliance": out.get("compliance") or default_compliance,
            }
        return {
            "simulated_at": datetime.now(UTC).isoformat(),
            "weather": default_weather,
            "terrain": default_terrain,
            "compliance": default_compliance,
        }

    def _execute_local_simulation(self, context: dict[str, Any]) -> dict[str, Any]:
        waypoints = context.get("waypoints", [])
        first_wp = waypoints[0] if waypoints else {"lat": 0.0, "lon": 0.0}
        seed_input = (
            f'{first_wp["lat"]:.4f}:{first_wp["lon"]:.4f}:{context.get("operator_id", "")}'
        )
        seed = int(hashlib.sha256(seed_input.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)

        weather = {
            "temperature_celsius": round(rng.uniform(-5.0, 35.0), 1),
            "pressure_hpa": round(rng.uniform(995, 1024), 1),
            "wind_speed_m_s": round(rng.uniform(1.5, 20), 1),
            "wind_direction_degrees": int(rng.uniform(0, 359)),
            "source": "local_simulation",
        }
        terrain = [
            {
                "lat": wp["lat"],
                "lon": wp["lon"],
                "elevation_meters": round(rng.uniform(30, 1200), 1),
            }
            for wp in waypoints
        ]
        zone_status = "CLEARED" if rng.random() > 0.15 else "RESTRICTED"
        compliance = {
            "zone_status": zone_status,
            "max_altitude_agl_meters": 120 if zone_status == "CLEARED" else 0,
            "allowed_drone_types": ["quadcopter", "uav_fixed_wing", "plane", "uav"],
            "required_certificates": ["Mission Ops Certificate", "BVLOS Endorsement"],
            "license_check": "PASS" if zone_status == "CLEARED" else "REVIEW_REQUIRED",
        }
        return {
            "simulated_at": datetime.now(UTC).isoformat(),
            "weather": weather,
            "terrain": terrain,
            "compliance": compliance,
        }
