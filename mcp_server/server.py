from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
import requests

from backend.app.config import settings
from backend.app.services.safety import calculate_takeoff
from backend.app.services.open_weather_elevation import get_weather, get_elevation

mcp = FastMCP("FlightGuard_MCP")


@mcp.tool()
def get_mission_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Gets wind speed/direction, temperature, and pressure for mission area.
    Uses Open-Meteo (no API key) by default; OpenWeather if OPENWEATHER_API_KEY is set.
    """
    if settings.openweather_api_key:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": settings.openweather_api_key,
            "units": "metric",
        }
        try:
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
        except Exception:
            pass
    return get_weather(latitude, longitude)


@mcp.tool()
def get_terrain_elevation(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Gets terrain elevation. Uses Open-Elevation (no API key) by default.
    Falls back to OpenTopoData if OPEN_TOPO_BASE_URL is set and Open-Elevation fails.
    """
    result = get_elevation(latitude, longitude)
    if result.get("source") == "open_weather_elevation_fallback" and getattr(settings, "open_topo_base_url", None):
        url = f"{settings.open_topo_base_url}/srtm90m"
        params = {"locations": f"{latitude},{longitude}"}
        try:
            r = requests.get(url, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
            res = data["results"][0]
            elevation = float(res.get("elevation", 0.0))
            return {
                "elevation_meters": elevation,
                "terrain_type": "flat" if elevation < 120 else "hilly",
                "source": "opentopodata",
            }
        except Exception:
            pass
    return {
        "elevation_meters": result["elevation_meters"],
        "terrain_type": result.get("terrain_type", "unknown"),
        "source": result.get("source", "open_elevation"),
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
