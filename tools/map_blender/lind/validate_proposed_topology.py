"""Validate proposed, unscaled LIND topology without inferring world coordinates."""
import argparse
import json
from pathlib import Path

SOURCE_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
ALLOWED = {"walk", "candidate_walk", "story", "story_jump"}
METRIC_FIELDS = ("origin", "meters_per_unit", "camera", "elevation_map")


def validate(data):
    errors = []
    if data.get("status") != "PROPOSED_UNSCALED":
        errors.append("topology must remain proposed and unscaled")
    if data.get("source", {}).get("sha256") != SOURCE_SHA:
        errors.append("canonical image SHA mismatch")
    metric = data.get("metric", {})
    if any(metric.get(k, "MISSING") is not None for k in METRIC_FIELDS):
        errors.append("world metric or camera invented or missing")
    nodes = data.get("nodes", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)) or not all(ids):
        errors.append("node IDs duplicate or missing")
    known = set(ids)
    edges = data.get("edges", [])
    for edge in edges:
        if edge.get("from") not in known or edge.get("to") not in known:
            errors.append("edge references missing node")
        if edge.get("kind") not in ALLOWED:
            errors.append("unapproved edge kind")
        if edge.get("kind") == "story_jump" and edge.get("bidirectional") is not False:
            errors.append("story jump must not be bidirectional")
    jump = [e for e in edges if e.get("from") == "raid_riverside_cliff"
            and e.get("to") == "downstream_landing"]
    if len(jump) != 1 or jump[0].get("kind") != "story_jump":
        errors.append("river cliff transition must remain a story jump")
    if any(e.get("kind") in ("walk", "candidate_walk") and
           {e.get("from"), e.get("to")} == {"raid_riverside_cliff", "downstream_landing"}
           for e in edges):
        errors.append("story jump illegally converted into traversable path")
    training = [n for n in nodes if n.get("id") == "east_training_area"]
    if len(training) != 1 or training[0].get("status") != "LOCATION_REVIEW_REQUIRED":
        errors.append("training area placement review marker lost")
    for node in nodes:
        if any(k in node for k in ("position", "coordinates", "meters", "elevation")):
            errors.append("fabricated node metric: " + str(node.get("id")))
    if not {"windward_cliffs_wnw", "raid_riverside_cliff", "harbor_sw",
            "north_farms", "road_to_dunvall"}.issubset(known):
        errors.append("required distinct geography missing")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    data = json.loads(Path(a.input).read_text())
    errors = validate(data)
    # Negative controls: the validator MUST reject each harmful mutation.
    controls = []
    def test(name, mutate):
        clone = json.loads(json.dumps(data))
        mutate(clone)
        detected = bool(validate(clone))
        controls.append({"name": name, "detected": detected})
        if not detected:
            errors.append("negative control escaped: " + name)
    test("invented_scale", lambda d: d["metric"].update({"meters_per_unit": 1.0}))
    test("invented_camera", lambda d: d["metric"].update({"camera": [0, 0, 0]}))
    test("wrong_source_sha", lambda d: d["source"].update({"sha256": "0" * 64}))
    test("story_jump_walk", lambda d: next(e for e in d["edges"] if e["from"] == "raid_riverside_cliff" and e["to"] == "downstream_landing").update({"kind": "walk"}))
    test("training_area_approved", lambda d: next(n for n in d["nodes"] if n["id"] == "east_training_area").update({"status": "APPROVED"}))
    test("fabricated_coordinates", lambda d: d["nodes"][0].update({"coordinates": [0, 0]}))
    report = {"status": "PASS" if not errors else "FAIL", "errors": errors,
              "negative_controls": controls, "G1": "BLOCKED",
              "G2": "NOT_RUN", "G3": "TOPOLOGY_VALIDATION_PASS" if not errors else "FAIL",
              "G4": "NOT_RUN", "official_world_placement": "NOT_RUN"}
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
