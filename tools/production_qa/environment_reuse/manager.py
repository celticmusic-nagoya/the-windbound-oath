"""Verify an exact Blender application cache before starting its executable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
INSTALLER = HERE.parent / "install_blender_530.sh"
LOCK = HERE / "blender.lock.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def inventory(app, max_bytes):
    if app.is_symlink() or not app.is_dir():
        raise ValueError("invalid application directory")
    app = app.resolve()
    entries, total = {}, 0

    def visit(directory):
        nonlocal total
        for path in sorted(directory.iterdir()):
            name = path.relative_to(app).as_posix()
            if any(ord(char) < 32 for char in name):
                raise ValueError("unsafe application path")
            info = path.lstat()
            mode = stat.S_IMODE(info.st_mode)
            if mode & 0o7000:
                raise ValueError("unsafe application mode")
            if path.is_symlink():
                target = os.readlink(path)
                if Path(target).is_absolute() or not path.resolve(strict=True).is_relative_to(app):
                    raise ValueError("unsafe application symlink")
                entries[name] = ["link", target]
            elif stat.S_ISDIR(info.st_mode):
                entries[name] = ["directory", mode]
                visit(path)
            elif stat.S_ISREG(info.st_mode):
                total += info.st_size
                if total > max_bytes:
                    raise ValueError("application exceeds cache byte budget")
                entries[name] = ["file", mode, info.st_size, sha(path)]
            else:
                raise ValueError("unexpected application file type")

    visit(app)
    if entries.get("blender", [None])[0] != "file":
        raise ValueError("missing Blender executable")
    return dict(entries=entries, bytes=total)


def provenance():
    lock = json.loads(LOCK.read_text())
    image = {k: os.environ[k] for k in ("ImageOS", "ImageVersion", "RUNNER_OS", "RUNNER_ARCH")}
    if (image["RUNNER_OS"], image["RUNNER_ARCH"], image["ImageOS"]) != ("Linux", "X64", "ubuntu24"):
        raise ValueError("unsupported runner image")
    return dict(schema=lock["schema"], image=image, tool="blender", version=lock["version"],
                archive_sha256=lock["archive_sha256"], installer_sha256=sha(INSTALLER),
                dependency_lock_sha256=sha(LOCK), configuration_sha256=sha(Path(__file__)))


def verify(root, prov, expected, maximum):
    manifest = root / "manifest.json"
    if root.is_symlink() or set(p.name for p in root.iterdir()) != {"app", "manifest.json"}:
        raise ValueError("unexpected cache paths")
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size > 16_777_216:
        raise ValueError("unsafe manifest")
    if not re.fullmatch("[0-9a-f]{64}", expected) or sha(manifest) != expected:
        raise ValueError("untrusted manifest SHA")
    current = dict(provenance=prov, **inventory(root / "app", maximum))
    if manifest.read_bytes() != canonical(current):
        raise ValueError("cached application differs from trusted manifest")
    return current["bytes"]


def startup(app, fixture, lock):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               PULSE_SERVER="unix:/tmp/two-no-pulse-socket")
    prefix = [str(app / "blender"), "-b", "--factory-startup", "--disable-autoexec",
              "-t", "2", "--python-use-system-env", "--python-exit-code", "9"]
    check = f"assert bpy.app.version_string == {lock['version']!r}; assert bpy.app.build_hash.decode() == {lock['build']!r}; "
    subprocess.run(prefix + ["--python-expr", "import bpy; " + check +
                   f"bpy.ops.wm.save_as_mainfile(filepath={str(fixture)!r})"], env=env, check=True, timeout=45)
    subprocess.run(prefix + [str(fixture), "--python-expr", "import bpy; " + check +
                   "assert len(bpy.data.objects['Cube'].data.vertices) == 8"], env=env, check=True, timeout=45)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["key", "cold", "warm"])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expected")
    args = parser.parse_args()
    prov = provenance()
    key = f"two-env-v{prov['schema']}-" + hashlib.sha256(canonical(prov)).hexdigest()
    if args.mode == "key":
        print(key)
        return
    started = time.monotonic()
    root = args.root.absolute()
    lock = json.loads(LOCK.read_text())
    installer_calls = 0
    if args.mode == "cold":
        root.mkdir(exist_ok=False)
        env = {**os.environ, "TWO_BLENDER_ARCHIVE_SHA256": lock["archive_sha256"]}
        subprocess.run(["bash", str(INSTALLER), str(root / "app"), "extract-only"],
                       env=env, check=True, timeout=780, umask=0o022)
        installer_calls = 1
        (root / "manifest.json").write_bytes(canonical(dict(provenance=prov,
                                             **inventory(root / "app", lock["max_tree_bytes"]))))
        expected = sha(root / "manifest.json")
    else:
        expected = args.expected or ""
    size = verify(root, prov, expected, lock["max_tree_bytes"])
    fixture = args.report.parent / (args.mode + ".blend")
    startup(root / "app", fixture, lock)
    verify(root, prov, expected, lock["max_tree_bytes"])
    args.report.write_bytes(canonical(dict(key=key, mode=args.mode, provenance=prov,
                           installer_calls=installer_calls, manifest_sha256=expected,
                           application_bytes=size, version=lock["version"], build=lock["build"],
                           elapsed_seconds=round(time.monotonic()-started, 3), native_reopen=True)))


if __name__ == "__main__":
    main()
