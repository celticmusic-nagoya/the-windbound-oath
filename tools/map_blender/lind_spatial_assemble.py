"""Explicit legacy-only gateway; new Lind geography has no approved metric contract yet.

Historical reproduction requires --legacy-layout. Never use pixel placements to
 author the adopted 2026-11-16 world. No Blender API is loaded on a blocked call.
"""
import argparse
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-layout", action="store_true",
                        help="reproduce the superseded pixel-layout contract only")
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if not args.legacy_layout:
        parser.error("BLOCKED: new-world metric spatial contract is not approved. "
                     "Legacy pixel placement is isolated; --legacy-layout is historical reproduction only.")
    output = Path(args.out).resolve()
    if output.exists():
        parser.error("BLOCKED: output already exists; refusing to overwrite " + str(output))
    layout = Path(args.layout).resolve()
    if output == layout:
        parser.error("BLOCKED: output would overwrite the layout source")
    # Preserve the legacy implementation, including its old SHA gate, separately.
    sys.argv = [sys.argv[0], "--", "--layout", str(layout), "--out", str(output)]
    runpy.run_path(str(Path(__file__).with_name("legacy") /
                       "lind_spatial_assemble_v1.py"), run_name="__main__")


if __name__ == "__main__":
    main()
