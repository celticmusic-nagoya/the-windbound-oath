"""Validate candidate topology without changing official game maps."""
import json
from pathlib import Path

path = Path(__file__).with_name("rilde_topology_candidate_01.json")
data = json.loads(path.read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in data["nodes"]}
assert len(nodes) == len(data["nodes"]), "duplicate node id"
assert data["status"] == "CANDIDATE_NOT_CANON"
for n in nodes.values():
    assert 0 <= n["x"] <= 1 and 0 <= n["y"] <= 1, n["id"]
for name, route in data["routes"].items():
    assert len(route) >= 2, name
    assert all(node in nodes for node in route), name
assert nodes["coastal_cliff"]["x"] < nodes["village"]["x"]
assert nodes["harbor"]["x"] < nodes["village"]["x"]
assert nodes["harbor"]["y"] > nodes["village"]["y"]
assert nodes["fortress_road"]["y"] < nodes["village"]["y"]
assert nodes["river_cliff"]["x"] > nodes["village"]["x"]
assert nodes["moss_forest"]["x"] > nodes["village"]["x"]
assert nodes["moss_forest"]["y"] > nodes["river_cliff"]["y"]
assert nodes["coastal_cliff"]["id"] != nodes["river_cliff"]["id"]
assert data["routes"]["raid_escape"][-1] == "altar"
assert data["routes"]["return_departure"][-1] == "fortress_road"
assert data["hydrology"] == ["bridge", "river_cliff", "moss_forest"]
print("PASS: candidate topology, cardinal geography, prologue route continuity")
