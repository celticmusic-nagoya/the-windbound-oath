"""Run trusted Blender adapter with minimal environment and immutable input.
This does not sandbox untrusted .blend contents at the OS level.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
from validate_patch import validate

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(blender, source, proposal, output, timeout=300):
    source, proposal, output = Path(source).resolve(), Path(proposal).resolve(), Path(output).resolve()
    if not source.is_file() or source.suffix != ".blend":
        raise ValueError("source must be existing .blend")
    if output.exists():
        raise FileExistsError("refusing overwrite of output")
    if output == source or source in output.parents:
        raise ValueError("output must be separate from source")
    if proposal.stat().st_size > 8192:
        raise ValueError("proposal too large")
    safe = validate(json.loads(proposal.read_text(encoding="utf-8")))
    before = digest(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    patch = output.parent / (output.stem + ".normalized.json")
    if patch.exists():
        raise FileExistsError("normalized patch exists")
    patch.write_text(json.dumps(safe, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    # An explicit environment, not a copy of os.environ. Avoid HOME/PYTHONPATH and credential inheritance.
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
           "HOME": str(output.parent), "TMPDIR": str(output.parent)}
    command = [str(Path(blender).resolve()), "-b", "--factory-startup",
               "--disable-autoexec", str(source), "--python",
               str(HERE / "apply_render_patch.py"), "--",
               "--patch", str(patch), "--output", str(output)]
    try:
        proc = subprocess.run(command, env=env, timeout=timeout, check=False,
                              capture_output=True, text=True)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Blender timeout") from exc
    if digest(source) != before:
        raise RuntimeError("SOURCE HASH CHANGED")
    report = {"source_sha256": before, "proposal_sha256": digest(proposal),
              "patch_sha256": digest(patch), "returncode": proc.returncode,
              "output_sha256": digest(output) if output.is_file() else None,
              "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
    report_path = output.parent / (output.stem + ".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if proc.returncode or not output.is_file():
        raise RuntimeError("Blender render failed; see report")
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 1200:
        parser.error("timeout must be 1..1200")
    print(json.dumps(run(args.blender, args.source, args.proposal, args.output, args.timeout), indent=2))

if __name__ == "__main__":
    main()
