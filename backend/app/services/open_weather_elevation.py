"""
Fetch real weather and elevation with no API key or registration.
Uses Open-Meteo (weather) and Open-Elevation (terrain) - both free and keyless.
"""
from __future__ import annotations

from typing import Any

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"
REQUEST_TIMEOUT = 12


def get_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Get current weather (temperature, pressure, wind) from Open-Meteo. No API key required.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "timezone": "auto",
    }
    try:
        r = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        cur = data.get("current", {})
        wind_kmh = cur.get("wind_speed_10m", 0) or 0
        wind_ms = round(float(wind_kmh) / 3.6, 1) if wind_kmh is not None else 0.0
        return {
            "temperature_celsius": round(float(cur.get("temperature_2m", 0) or 0), 1),
            "pressure_hpa": round(float(cur.get("surface_pressure", 1013) or 1013), 1),
            "wind_speed_m_s": wind_ms,
            "wind_direction_degrees": int(cur.get("wind_direction_10m", 0) or 0),
            "relative_humidity_percent": int(cur.get("relative_humidity_2m", 0) or 0),
            "source": "open_meteo",
        }
    except Exception:
        return {
            "temperature_celsius": 15.0,
            "pressure_hpa": 1013.0,
            "wind_speed_m_s": 5.0,
            "wind_direction_degrees": 270,
            "relative_humidity_percent": 60,
            "source": "open_weather_elevation_fallback",
        }


def get_elevation(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Get terrain elevation from Open-Elevation. No API key required.
    """
    params = {"locations": f"{latitude},{longitude}"}
    try:
        r = requests.get(OPEN_ELEVATION_URL, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return _fallback_elevation(latitude, longitude)
        elev = float(results[0].get("elevation", 0) or 0)
        return {
            "elevation_meters": round(elev, 1),
            "lat": latitude,
            "lon": longitude,
            "terrain_type": "flat" if elev < 120 else "hilly" if elev < 500 else "mountainous",
            "source": "open_elevation",
        }
    except Exception:
        return _fallback_elevation(latitude, longitude)


def _fallback_elevation(lat: float, lon: float) -> dict[str, Any]:
    return {
        "elevation_meters": 100.0,
        "lat": lat,
        "lon": lon,
        "terrain_type": "unknown",
        "source": "open_weather_elevation_fallback",
    }


def get_weather_and_elevation_for_waypoints(waypoints: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Get real weather for the first waypoint and real elevation for each waypoint.
    Returns (weather_dict, list of terrain dicts with lat, lon, elevation_meters).
    """
    weather = {
        "temperature_celsius": 15.0,
        "pressure_hpa": 1013.0,
        "wind_speed_m_s": 5.0,
        "wind_direction_degrees": 270,
        "source": "open_weather_elevation_fallback",
    }
    terrain_list: list[dict[str, Any]] = []

    if waypoints:
        first = waypoints[0]
        lat = first.get("lat", 0.0)
        lon = first.get("lon", 0.0)
        weather = get_weather(lat, lon)
        for wp in waypoints:
            wlat = wp.get("lat", 0.0)
            wlon = wp.get("lon", 0.0)
            elev_data = get_elevation(wlat, wlon)
            terrain_list.append({
                "lat": wlat,
                "lon": wlon,
                "elevation_meters": elev_data["elevation_meters"],
            })

    return weather, terrain_list
