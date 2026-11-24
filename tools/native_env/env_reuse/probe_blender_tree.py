#!/usr/bin/env python3
"""Qualification probe for #493 (NOT a cache implementation; #493/Codex owns that).

Measures, on an already SHA-verified official Blender extraction:
  * tree manifest (files: SHA-256 + mode, symlinks: target, dirs), unsafe symlinks / special files
  * whether one headless startup mutates the installed tree, under three run modes
Usage: probe_blender_tree.py EXTRACTED_DIR OUT.json   (run as root to test the non-root mode)
"""
import hashlib, json, os, shutil, stat, subprocess, sys, tempfile, time


def manifest(root):
    rows, unsafe = [], []
    for d, ds, fs in os.walk(root):
        for n in sorted(ds + fs):
            p = os.path.join(d, n); rel = os.path.relpath(p, root); st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                tgt = os.readlink(p)
                if os.path.isabs(tgt) or os.path.normpath(os.path.join(os.path.dirname(rel), tgt)).startswith(".."):
                    unsafe.append(rel)
                rows.append([rel, "l", tgt])
            elif stat.S_ISREG(st.st_mode):
                h = hashlib.sha256()
                with open(p, "rb") as f:
                    for b in iter(lambda: f.read(1 << 20), b""):
                        h.update(b)
                rows.append([rel, "f", h.hexdigest(), st.st_mode & 0o777])
            elif stat.S_ISDIR(st.st_mode):
                rows.append([rel, "d"])
            else:
                unsafe.append(rel)
    rows.sort()
    return dict(sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(), entries=len(rows),
                files=sum(r[1] == "f" for r in rows), symlinks=sum(r[1] == "l" for r in rows), unsafe=unsafe), rows


def trial(src, mode):
    work = tempfile.mkdtemp(prefix="probe-")
    os.chmod(work, 0o755)
    tree = os.path.join(work, "app")
    shutil.copytree(src, tree, symlinks=True)
    cmd, env, args = [], dict(os.environ), []
    if mode == "nonroot_readonly":
        subprocess.run(["chmod", "-R", "a-w,a+rX", tree], check=True)
        cmd, env["HOME"] = ["runuser", "-u", "nobody", "--"], work
    elif mode == "system_env_no_bytecode":
        env["PYTHONDONTWRITEBYTECODE"], args = "1", ["--python-use-system-env"]
    t = time.monotonic()
    p = subprocess.run([*cmd, os.path.join(tree, "blender"), "-b", "--factory-startup", *args, "--python-expr",
                        "import bpy;print('TWO_PROBE', bpy.app.version_string, bpy.app.build_hash)"],
                       capture_output=True, text=True, env=env, cwd=work, timeout=300)
    sec = time.monotonic() - t
    subprocess.run(["chmod", "-R", "u+w", tree], check=True)
    after, rows = manifest(tree)
    shutil.rmtree(work)
    line = [l for l in p.stdout.splitlines() if l.startswith("TWO_PROBE")]
    return dict(mode=mode, startup_ok=bool(line), version=line[0][10:] if line else None,
                startup_sec=round(sec, 2), manifest_after=after["sha256"], entries_after=after["entries"])


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    t = time.monotonic(); base, _ = manifest(src); msec = time.monotonic() - t
    trials = [trial(src, m) for m in ("default", "system_env_no_bytecode", "nonroot_readonly")]
    for tr in trials:
        tr["tree_unchanged"] = tr["manifest_after"] == base["sha256"]
        tr["entries_added"] = tr.pop("entries_after") - base["entries"]
    json.dump(dict(manifest=base, manifest_sec=round(msec, 2), trials=trials), open(out, "w"), indent=1)
    print(json.dumps(dict(manifest=base, trials=trials), indent=1))
