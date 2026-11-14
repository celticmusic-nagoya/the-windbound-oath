#!/usr/bin/env python3
"""Validate fixed-scope map agent request. No arbitrary prompts or shell commands."""
import json, pathlib, sys

ALLOWED = {
    "claude": {"MAP-ASSET-RESEARCH-01": "docs/map-development/CLAUDE_MAP_ASSET_RESEARCH_01.md"},
    "codex": {
        "MAP-PIPELINE-01": "docs/map-development/CODEX_MAP_PIPELINE_01.md",
        "MAP-INTEGRATION-AUDIT-01": "docs/map-development/CODEX_MAP_INTEGRATION_AUDIT_01.md",
    },
}
def validate(request):
    if not isinstance(request,dict): raise ValueError("request must be object")
    if set(request)!={"agent","task","mode"}:raise ValueError("unexpected or missing keys")
    agent,task,mode=(request[k] for k in ("agent","task","mode"))
    if agent not in ALLOWED or task not in ALLOWED[agent]:raise ValueError("agent/task not allowlisted")
    if mode != "dry_run":raise ValueError("paid execution is disabled during safety verification")
    return {"agent":agent,"task":task,"mode":mode,"packet":ALLOWED[agent][task]}
if __name__=="__main__":
    try:
        req=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf8"))
        print(json.dumps(validate(req)))
    except (ValueError,OSError,KeyError,IndexError) as exc:
        print(f"INVALID_REQUEST: {exc}",file=sys.stderr)
        sys.exit(2)
