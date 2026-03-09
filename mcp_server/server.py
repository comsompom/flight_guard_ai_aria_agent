from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
import requests

from backend.app.config import settings
from backend.app.services.safety import calculate_takeoff

mcp = FastMCP("FlightGuard_MCP")


@mcp.tool()
def get_mission_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Gets wind speed/direction, temperature, and pressure for mission area.
    Uses OpenWeather when OPENWEATHER_API_KEY exists, else deterministic mock.
    """
    if not settings.openweather_api_key:
        base = abs(latitude) + abs(longitude)
        return {
            "temperature_celsius": round((base % 35) - 5, 1),
            "pressure_hpa": round(1000 + (base % 20), 1),
            "wind_speed_m_s": round(4 + (base % 10), 1),
            "wind_direction_degrees": int((base * 13) % 360),
            "source": "mcp_mock",
        }

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }
    r = requests.get(url, params=params, timeout=12)
    r.raise_for_status()
    payload = r.json()
    return {
        "temperature_celsius": payload["main"]["temp"],
        "pressure_hpa": payload["main"]["pressure"],
        "wind_speed_m_s": payload.get("wind", {}).get("speed", 0.0),
        "wind_direction_degrees": int(payload.get("wind", {}).get("deg", 0)),
        "source": "openweather",
    }


@mcp.tool()
def get_terrain_elevation(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Gets terrain elevation from OpenTopoData.
    """
    url = f"{settings.open_topo_base_url}/srtm90m"
    params = {"locations": f"{latitude},{longitude}"}
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        result = data["results"][0]
        elevation = float(result.get("elevation", 0.0))
        return {
            "elevation_meters": elevation,
            "terrain_type": "flat" if elevation < 120 else "hilly",
            "source": "opentopodata",
        }
    except Exception:
        return {
            "elevation_meters": 180.0,
            "terrain_type": "unknown",
            "source": "mcp_fallback",
        }


@mcp.tool()
def check_airspace_compliance(latitude: float, longitude: float, drone_type: str) -> dict[str, Any]:
    """
    Hackathon-safe compliance mock. Replace with OpenAIP/AirMap/defense policy APIs.
    """
    score = int((abs(latitude) * 10 + abs(longitude) * 3)) % 10
    status = "CLEARED" if score >= 2 else "RESTRICTED"
    return {
        "zone_status": status,
        "max_altitude_agl_meters": 120.0 if status == "CLEARED" else 0.0,
        "allowed_drone_types": ["quadcopter", "uav_fixed_wing", "plane", "uav"],
        "required_certificates": ["Mission Ops Certificate", "BVLOS Endorsement"],
        "license_check": "PASS" if status == "CLEARED" else "REVIEW_REQUIRED",
        "source": "mcp_mock",
    }


@mcp.tool()
def calculate_takeoff_vectors(drone_type: str, wingspan_m: float, wind_dir: int) -> dict[str, Any]:
    """
    Calculates takeoff vectors for fixed-wing and VTOL.
    """
    recommendation = calculate_takeoff(drone_type=drone_type, wind_direction_degrees=wind_dir)
    recommendation["wingspan_m"] = wingspan_m
    return recommendation


if __name__ == "__main__":
    mcp.run()
