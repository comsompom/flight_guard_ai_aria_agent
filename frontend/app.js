// Same origin when frontend is served from backend (e.g. http://localhost:8000)
const API_BASE = "";

const waypoints = [];
let missionId = null;
const markers = [];

const map = L.map("map").setView([48.8566, 2.3522], 7);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const waypointsView = document.getElementById("waypointsView");
const reviewView = document.getElementById("reviewView");
const approvalButtons = document.getElementById("approvalButtons");

function syncWaypointView() {
  waypointsView.textContent = JSON.stringify(waypoints, null, 2);
}

function setReview(data) {
  reviewView.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

map.on("click", (e) => {
  const waypoint = {
    lat: Number(e.latlng.lat.toFixed(6)),
    lon: Number(e.latlng.lng.toFixed(6)),
    alt_m: 80,
    speed_m_s: 12,
  };
  waypoints.push(waypoint);

  const marker = L.marker([waypoint.lat, waypoint.lon]).addTo(map);
  marker.bindPopup(`WP ${waypoints.length}: ${waypoint.alt_m}m / ${waypoint.speed_m_s}m/s`);
  markers.push(marker);
  syncWaypointView();
});

document.getElementById("clearWp").addEventListener("click", () => {
  waypoints.length = 0;
  markers.forEach((m) => map.removeLayer(m));
  markers.length = 0;
  missionId = null;
  approvalButtons.classList.add("hidden");
  syncWaypointView();
  setReview("Waypoints cleared.");
});

document.getElementById("planMission").addEventListener("click", async () => {
  if (!waypoints.length) {
    setReview("Add at least one waypoint.");
    return;
  }

  const payload = {
    operator_id: document.getElementById("operatorId").value.trim(),
    clearance_level: document.getElementById("clearance").value.trim(),
    drone_type: document.getElementById("droneType").value,
    drone_weight_kg: Number(document.getElementById("weightKg").value),
    wingspan_meters: Number(document.getElementById("wingspanM").value),
    waypoints,
    launch_mode_hint: "auto",
  };

  setReview("Planning mission...");
  const res = await fetch(`${API_BASE}/api/plan-mission`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    setReview(`Planning failed: ${err}`);
    return;
  }
  const data = await res.json();
  missionId = data.mission_id;
  approvalButtons.classList.remove("hidden");
  setReview(data);
});

async function resolveMission(approved) {
  if (!missionId) {
    setReview("No mission selected.");
    return;
  }
  const body = {
    approved,
    commander_note: approved ? "Approved for execution." : "Aborted by commander.",
  };
  const res = await fetch(`${API_BASE}/api/approve-mission/${missionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  setReview(data);
}

document.getElementById("approveMission").addEventListener("click", async () => resolveMission(true));
document.getElementById("abortMission").addEventListener("click", async () => resolveMission(false));

syncWaypointView();
