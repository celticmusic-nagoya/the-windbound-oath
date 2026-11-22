"""Discover bounded production image candidates from known owning branches."""
import json, os, pathlib, re, subprocess, zipfile, hashlib
ROOT=pathlib.Path(os.environ["RUNNER_TEMP"])
REPO=os.environ["GITHUB_REPOSITORY"]
BRANCHES={"feature/lind-cliff-rock-art-study-20261118":"cliff","feature/morwen-artdirected-sculpt-20261119":"morwen","feature/lind-home-01":"village","feature/lind-buildings-01":"village","feature/lind-village-world-integration-plan-01":"village"}
def api(path):
    return json.loads(subprocess.check_output(["gh","api",path]))
def allowed(name,cat):
    p=pathlib.PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or chr(92) in name:return False
    if cat=="morwen":return bool(re.fullmatch(r"view-reopened(?:close)?-(front|back|left|right)\.png",p.name))
    return bool(re.fullmatch(r"(?:[\w-]+/)*(?:review|renders|render|previews)/[\w.-]+\.(?:png|jpg|jpeg)",name,re.I))
def discover():
    selection=json.loads(pathlib.Path(__file__).with_name("sync-selection.json").read_text())
    known={x["artifact_id"] for x in selection}
    saved=ROOT/"studio-zips";saved.mkdir(exist_ok=True)
    for branch,cat in BRANCHES.items():
        runs=api(f"repos/{REPO}/actions/runs?branch={branch}&status=success&per_page=3")["workflow_runs"]
        found=False
        for run in runs:
            if run["head_branch"]!=branch or run["head_repository"]["full_name"]!=REPO:continue
            for a in api(f"repos/{REPO}/actions/runs/{run['id']}/artifacts?per_page=20")["artifacts"]:
                if a["id"] in known or a["expired"] or not 0<a["size_in_bytes"]<=64*1024*1024:continue
                if not re.search(r"morwen|cliff|lind|rild|village|home|building",a["name"],re.I):continue
                target=saved/f"{a['id']}.zip"
                with target.open("wb") as out:subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{a['id']}/zip"],stdout=out,check=True)
                with target.open("rb") as stream:
                    if "sha256:"+hashlib.file_digest(stream,"sha256").hexdigest()!=a.get("digest"):raise ValueError("archive digest mismatch")
                with zipfile.ZipFile(target) as z:
                    entries=[i.filename for i in z.infolist() if 0<i.file_size<=8*1024*1024 and allowed(i.filename,cat)][:8]
                if entries:
                    selection.append(dict(run_id=run["id"],artifact_id=a["id"],head=run["head_sha"],category=cat,stage=a["name"][:80],cover=entries[0],entries=entries))
                    known.add(a["id"]);found=True;break
                target.unlink()
            if found:break
    (ROOT/"studio-discovered.json").write_text(json.dumps(selection,ensure_ascii=False))
    print(json.dumps([{"artifact":x["artifact_id"],"category":x["category"],"count":len(x["entries"])} for x in selection]))
if __name__=="__main__":discover()
