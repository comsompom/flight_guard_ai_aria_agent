"""
Fetch real weather and elevation with no API key or registration.
Uses Open-Meteo (weather) and Open-Elevation (terrain) - both free and keyless.
Supports async parallel fetching for minimal latency.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"
REQUEST_TIMEOUT = 12.0


# ---- Sync (kept for MCP and simple callers) ----

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
        return _default_weather()


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


def _default_weather() -> dict[str, Any]:
    return {
        "temperature_celsius": 15.0,
        "pressure_hpa": 1013.0,
        "wind_speed_m_s": 5.0,
        "wind_direction_degrees": 270,
        "relative_humidity_percent": 60,
        "source": "open_weather_elevation_fallback",
    }


def _fallback_elevation(lat: float, lon: float) -> dict[str, Any]:
    return {
        "elevation_meters": 100.0,
        "lat": lat,
        "lon": lon,
        "terrain_type": "unknown",
        "source": "open_weather_elevation_fallback",
    }


# ---- Async parallel telemetry (weather + batch elevation in one round-trip) ----

async def _fetch_weather_async(client: httpx.AsyncClient, latitude: float, longitude: float) -> dict[str, Any]:
    """Single async weather request."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "timezone": "auto",
    }
    try:
        r = await client.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
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
        return _default_weather()


async def _fetch_elevation_batch_async(
    client: httpx.AsyncClient,
    waypoints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Single async request for all waypoint elevations (Open-Elevation supports batch).
    Returns list of { lat, lon, elevation_meters } in same order as waypoints.
    """
    if not waypoints:
        return []
    locations = "|".join(
        f'{wp.get("lat", 0)},{wp.get("lon", 0)}'
        for wp in waypoints
    )
    params = {"locations": locations}
    try:
        r = await client.get(OPEN_ELEVATION_URL, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        terrain_list: list[dict[str, Any]] = []
        for i, wp in enumerate(waypoints):
            wlat = wp.get("lat", 0.0)
            wlon = wp.get("lon", 0.0)
            if i < len(results):
                elev = float(results[i].get("elevation", 0) or 0)
                terrain_list.append({
                    "lat": wlat,
                    "lon": wlon,
                    "elevation_meters": round(elev, 1),
                })
            else:
                terrain_list.append({
                    "lat": wlat,
                    "lon": wlon,
                    "elevation_meters": 100.0,
                })
        return terrain_list
    except Exception:
        return [
            {"lat": wp.get("lat", 0), "lon": wp.get("lon", 0), "elevation_meters": 100.0}
            for wp in waypoints
        ]


async def get_weather_and_elevation_for_waypoints_async(
    waypoints: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Fetch weather (first waypoint) and elevations (all waypoints) in parallel.
    Uses one weather request + one batch elevation request concurrently.
    Returns (weather_dict, list of { lat, lon, elevation_meters }).
    """
    weather = _default_weather()
    terrain_list: list[dict[str, Any]] = []

    if not waypoints:
        return weather, terrain_list

    first = waypoints[0]
    lat = first.get("lat", 0.0)
    lon = first.get("lon", 0.0)

    async with httpx.AsyncClient() as client:
        weather_task = _fetch_weather_async(client, lat, lon)
        elevation_task = _fetch_elevation_batch_async(client, waypoints)
        weather, terrain_list = await asyncio.gather(weather_task, elevation_task)

    return weather, terrain_list


def get_weather_and_elevation_for_waypoints(waypoints: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Sync entry point: runs async fetch in an event loop for parallel I/O.
    Get real weather for the first waypoint and real elevation for each waypoint (batch).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        import concurrent.futures
        def run_in_thread() -> tuple[dict[str, Any], list[dict[str, Any]]]:
            return asyncio.run(get_weather_and_elevation_for_waypoints_async(waypoints))
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(run_in_thread).result()
    return asyncio.run(get_weather_and_elevation_for_waypoints_async(waypoints))
