"""Register the exact adopted PNG bytes; never resample or promote a substitute."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

EXPECTED_SHA256 = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
SOURCE_DIR = Path("assets/sources/lind-world-20261116")


def verified_bytes(path, expected=EXPECTED_SHA256):
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError(f"BLOCKED: SHA-256 mismatch; expected {expected}, actual {actual}")
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("BLOCKED: source is not a PNG")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    raw = verified_bytes(args.source)
    if args.check_only:
        print("SOURCE_SHA_VERIFIED", EXPECTED_SHA256)
        return
    repo = Path(__file__).resolve().parents[3]
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo, text=True).strip()
    if not branch.startswith("feature/"):
        raise ValueError("BLOCKED: registration requires a feature branch")
    directory = repo / SOURCE_DIR
    # A fresh directory is the transaction boundary: existing sources are never replaced.
    directory.mkdir(parents=True, exist_ok=False)
    original = directory / "original.png"
    with original.open("xb") as out:
        out.write(raw)
    assert original.read_bytes() == raw
    manifest = {
        "schema": "lind-source-registration-v1",
        "source": str(SOURCE_DIR / "original.png"),
        "sha256": EXPECTED_SHA256,
        "bytes": len(raw),
        "source_status": "DIRECTOR_ADOPTED_VISUAL_COMPOSITION",
        "registration": "EXACT_BYTES_SHA_VERIFIED",
        "processing": "NONE",
        "note": "Registration is not full G1/G2/G3/G4 approval or a metric spatial contract."
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("SOURCE_REGISTERED", original, EXPECTED_SHA256)


if __name__ == "__main__":
    main()
