from __future__ import annotations


def normalize_heading(value: int | float) -> int:
    return int(value) % 360


def calculate_takeoff(drone_type: str, wind_direction_degrees: int) -> dict:
    drone_type = drone_type.lower()
    if drone_type in {"plane", "fixed-wing", "uav", "uav_fixed_wing"}:
        # Fixed-wing should launch into the wind.
        heading = normalize_heading(wind_direction_degrees + 180)
        return {
            "takeoff_mode": "Catapult or wheels (fixed-wing)",
            "optimal_heading_degrees": heading,
            "wheel_landing_capable": True,
        }

    return {
        "takeoff_mode": "Vertical takeoff (VTOL/quadcopter)",
        "optimal_heading_degrees": None,
        "wheel_landing_capable": False,
    }


def risk_from_conditions(
    wind_speed_m_s: float,
    zone_status: str,
    waypoint_count: int,
) -> tuple[str, list[str]]:
    warnings: list[str] = []

    if zone_status != "CLEARED":
        warnings.append("Airspace is restricted or denied.")
        return "CRITICAL", warnings

    if wind_speed_m_s >= 18:
        warnings.append("High wind conditions may exceed safe envelope.")
        return "HIGH", warnings

    if wind_speed_m_s >= 12:
        warnings.append("Moderate-high wind; confirm airframe stability.")
        return "MEDIUM", warnings

    if waypoint_count >= 8:
        warnings.append("Long mission route increases operational complexity.")
        return "MEDIUM", warnings

    return "LOW", warnings
