"""Read-only Studio handoff preflight. Never generates Factory targets or observations."""
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from production_qa.shared_blueprint_contract import metric_state

SOURCE_BLOB = "300fa1fa080886abdb1493039a41fe6449633cb0"
CONTRACT = {"axes": "X east Y north Z up", "unit": "metre", "origin": None,
            "yaw": "degrees_ccw_about_positive_z"}
IDS = ("RILDE_VILLAGE", "WINDWAITING_CLIFF", "COASTAL_MEADOW", "RIVER_CORRIDOR",
       "MOSS_FOREST_A1", "MOSS_FOREST_A2", "MOSS_FOREST_A3", "DUNVAR_FORTRESS")
FIELDS = ("x_m", "y_m", "z_m", "yaw_deg")
LIMIT = 512 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bounded(value, limit=1000000):
    return type(value) in (int, float) and -limit <= value <= limit


def revision(value):
    return type(value) is int and 0 <= value < 2**53 - 1


def transform(row, area, allow_null=False):
    require(isinstance(row, dict) and row.get("id") == area, "placement ID")
    require(all(k in row and ((allow_null and row[k] is None)
                or bounded(row[k], 360 if k == "yaw_deg" else 1000000))
                for k in FIELDS), "placement values")
    return {k: row[k] for k in ("id", *FIELDS)}


def measure(placements, local, t, u):
    world = []
    for p, (x, y, z) in zip(placements, local):
        a = math.radians(p["yaw_deg"])
        world.append([p["x_m"] + x * math.cos(a) - y * math.sin(a),
                      p["y_m"] + x * math.sin(a) + y * math.cos(a),
                      p["z_m"] + z])
    delta = [b - a for a, b in zip(*world)]
    r = math.hypot(*delta)
    eps = 64 * sys.float_info.epsilon * max(1, *(abs(x) for p in world for x in p), r, t, u)
    verdict = metric_state(r, t, u)
    # Same conservative boundary guard as Studio, never promotes an engine HOLD.
    if verdict == "PASS" and not r + u < t - eps:
        verdict = "HOLD"
    if verdict == "OUTSIDE" and not r - u > t + eps:
        verdict = "HOLD"
    return {"r": r, "delta_m": delta, "verdict": verdict, "roundoff_guard_m": eps}


def pairs(p):
    result = {}
    for k, v in p:
        require(k not in result, "duplicate JSON key")
        result[k] = v
    return result


def preflight(raw):
    require(len(raw) <= LIMIT, "file exceeds 512 KiB")
    d = json.loads(raw, object_pairs_hook=pairs)
    require(isinstance(d, dict) and d.get("schema") == "two.studio.anchor_batch_handoff.v1"
            and d.get("status") == "PROVISIONAL" and d.get("source_blob") == SOURCE_BLOB
            and d.get("coordinate_contract") == CONTRACT
            and revision(d.get("placement_revision"))
            and d.get("mode") in ("STRICT", "BASELINE_COMPARE"), "handoff contract")
    require(isinstance(d.get("placement"), list) and len(d["placement"]) == len(IDS),
            "placement inventory")
    by_id = {}
    for row in d["placement"]:
        require(isinstance(row, dict) and row.get("id") in IDS
                and row["id"] not in by_id, "placement inventory ID")
        by_id[row["id"]] = transform(row, row["id"], True)
    require(isinstance(d.get("items"), list) and 1 <= len(d["items"]) <= 32, "item count")
    out = []
    seen = set()
    for i, item in enumerate(d["items"]):
        try:
            require(isinstance(item, dict), "item shape")
            require(item.get("verdict") != "REJECTED", "source rejected; input review required")
            areas = item.get("area_ids")
            require(isinstance(areas, list) and len(areas) == 2
                    and all(a in IDS for a in areas) and areas[0] != areas[1], "pair IDs")
            local = item.get("local_xyz_m")
            require(isinstance(local, list) and len(local) == 2 and all(
                isinstance(p, list) and len(p) == 3 and all(bounded(v) for v in p)
                for p in local), "local coordinates")
            t, u = item.get("tolerance_m"), item.get("uncertainty_m")
            require(bounded(t) and bounded(u) and t >= 0 and u >= 0, "t/u")
            ps = item.get("placement")
            require(isinstance(ps, list) and len(ps) == 2, "pair placement")
            ps = [transform(p, a) for p, a in zip(ps, areas)]
            require(all(p == by_id[a] for p, a in zip(ps, areas)), "snapshot mismatch")
            baseline = None
            bp = None
            if d["mode"] == "BASELINE_COMPARE":
                bp = item.get("baseline_placement")
                require(isinstance(bp, list) and len(bp) == 2
                        and revision(item.get("baseline_revision")), "baseline")
                bp = [transform(p, a) for p, a in zip(bp, areas)]
                baseline = measure(bp, local, t, u)
            else:
                require(item.get("baseline_placement") is None
                        and item.get("baseline_revision") is None, "unexpected baseline")
            key = json.dumps([sorted([(a, xyz, [b[k] for k in FIELDS] if bp else None)
                                     for a, xyz, b in zip(areas, local, bp or ps)]), t, u])
            require(key not in seen, "duplicate pair input")
            seen.add(key)
            result = measure(ps, local, t, u)
            claimed = item.get("result")
            match = isinstance(claimed, dict) and bounded(claimed.get("r"), 10000000) and (
                abs(claimed["r"] - result["r"]) <= result["roundoff_guard_m"]
                and claimed.get("verdict") == result["verdict"])
            out.append({"index": i, "area_ids": areas, "placement": ps,
                        "local_xyz_m": local, "tolerance_m": t, "uncertainty_m": u,
                        "result": result, "baseline_result": baseline,
                        "claimed_result_matches": match,
                        "evidence_class": "PROVISIONAL_DESIGN",
                        "action": "REVIEW_INPUT" if not match else
                                  {"PASS": "NO_POSITION_ACTION", "HOLD": "REMEASURE",
                                   "OUTSIDE": "REVIEW_PLACEMENT"}[result["verdict"]]})
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            out.append({"index": i, "verdict": "REJECTED", "reason": str(exc),
                        "action": "REVIEW_INPUT"})
    return {"schema": "two.studio.anchor_handoff_preflight.v1",
            "input_sha256": hashlib.sha256(raw).hexdigest(), "source_blob": SOURCE_BLOB,
            "placement_revision": d["placement_revision"], "items": out,
            "factory_ready": False, "native_observation": False, "independent_qa": "NOT_RUN",
            "missing_engine_evidence": ["owner_verified_source_sha256", "native_sha256",
                "target_and_measurement_id", "qualified_operation_evidence_sha256",
                "dependency_fingerprint", "protected_scope_baseline_sha256",
                "native_measurement_and_independent_qa"]}


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 2, "usage: python anchor-handoff-preflight.py handoff.json")
        with open(sys.argv[1], "rb") as stream:
            raw = stream.read(LIMIT + 1)
        print(json.dumps(preflight(raw), ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        sys.exit(2)
