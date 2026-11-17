"""Evidence-only acceptance gate for LIND candidate D routes (not gameplay approval)."""
import argparse
import json
from pathlib import Path

EXPECTED = {
    "Village_to_coastal_promontory": 423,
    "Village_to_east_bridge": 423,
    "Village_to_harbor_access": 423,
    "Village_to_north_farmland": 288,
}


def evaluate(occlusions, grades):
    failures = []
    names = [r.get("route") for r in occlusions]
    if len(names) != len(set(names)) or set(names) != set(EXPECTED):
        failures.append("route set mismatch or duplicates")
    for route in occlusions:
        name = route.get("route")
        if route.get("samples") != EXPECTED.get(name):
            failures.append(f"{name}: sample count mismatch")
        if route.get("buried_samples") != 0 or route.get("buried_center_samples") != 0:
            failures.append(f"{name}: route penetration")
        if not isinstance(route.get("max_gap"), (float, int)) or route["max_gap"] < 0:
            failures.append(f"{name}: invalid gap")
    if len(grades) != len(EXPECTED) or {r.get("name") for r in grades} != set(EXPECTED):
        failures.append("grade route set mismatch")
    for route in grades:
        if not isinstance(route.get("max_angle_degrees"), (float, int)) or route["max_angle_degrees"] > 25:
            failures.append(f"{route.get('name')}: grade exceeds provisional limit")
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occlusion", required=True)
    parser.add_argument("--grades", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    occlusions = json.loads(Path(args.occlusion).read_text())
    grades = json.loads(Path(args.grades).read_text())
    errors = evaluate(occlusions, grades)
    controls = []
    def negative(name, modify):
        data = json.loads(json.dumps(occlusions))
        gs = json.loads(json.dumps(grades))
        modify(data, gs)
        caught = bool(evaluate(data, gs))
        controls.append({"name": name, "caught": caught})
        if not caught:
            errors.append(f"negative control not caught: {name}")
    negative("buried_route", lambda d, g: d[1].update({"buried_samples": 1}))
    negative("missing_stations", lambda d, g: d[0].update({"samples": 1}))
    negative("duplicate_route", lambda d, g: d[1].update({"route": d[0]["route"]}))
    negative("excess_grade", lambda d, g: g[1].update({"max_angle_degrees": 40}))
    max_gap = max(float(r["max_gap"]) for r in occlusions)
    result = {
        "status": "PASS" if not errors else "FAIL",
        "candidate": "D",
        "scope": "historical independent sampled evidence only",
        "sample_count": sum(r["samples"] for r in occlusions),
        "max_gap_candidate_units": max_gap,
        "unsupported_road_gap_detected": max_gap > 0.4,
        "G1": "BLOCKED", "G2": "FAIL",
        "G3_sampled_nonburial": "PASS" if not errors else "FAIL",
        "G3_support_and_navmesh": "NOT_RUN", "G4": "NOT_RUN",
        "negative_controls": controls, "errors": errors,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
