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
def model_allowed(name):
    p=pathlib.PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and chr(92) not in name and bool(re.fullmatch(r"(?:[\w-]+/)*(?:export|exports|models)/[\w.-]+\.(?:glb|vrm)",name,re.I))
def vroid_review_allowed(name):
    # Only actual model views; never desktop, dialog, OCR or native files.
    return bool(re.fullmatch(r"(?:evidence/)?(?:rear-calibration-[5-8]|view-isolated-reopen-(?:front|back|left|right))\.png",name))

def preview_vroid(selection,known,saved):
    """Exact trusted producing workflow, main only; never used by publishing job."""
    runs=api(f"repos/{REPO}/actions/workflows/morwen-vroid-macos-probe.yml/runs?branch=main&status=success&per_page=10")["workflow_runs"]
    for run in runs:
        if run["head_branch"]!="main" or (run.get("head_repository") or {}).get("full_name")!=REPO or run.get("conclusion")!="success":continue
        for a in api(f"repos/{REPO}/actions/runs/{run['id']}/artifacts?per_page=100")["artifacts"]:
            if a["id"] in known or a["expired"] or a["name"]!="morwen-isolated-vroid-reopen-review" or not 0<a["size_in_bytes"]<=16*1024*1024:continue
            target=saved/f"{a['id']}.zip"
            with target.open("wb") as out:subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{a['id']}/zip"],stdout=out,check=True)
            with target.open("rb") as stream:
                if "sha256:"+hashlib.file_digest(stream,"sha256").hexdigest()!=a.get("digest"):raise ValueError("archive digest mismatch")
            with zipfile.ZipFile(target) as z:
                entries=sorted(i.filename for i in z.infolist() if 0<i.file_size<=8*1024*1024 and vroid_review_allowed(i.filename))
            if entries:
                selection.append(dict(run_id=run["id"],artifact_id=a["id"],head=run["head_sha"],category="morwen",stage="VRoid isolated reopen / rear calibration / preview only",cover=entries[0],entries=entries,artifact_digest=a["digest"]))
                known.add(a["id"])
                return
            target.unlink()

# Exact producer receipts from the owning workflows. These are preview-only,
# not publication authorization; unknown archives stay outside this list.
PREVIEW_RECEIPTS = (
    (44983695054, 14738992328, "68da524b9fe74094c36e532549262a048d88a507", "feature/lind-cliff-rock-art-study-20261118", "lind-cliff-c11-normal-diagnostic.yml", "c11-normal-diagnostic-44983695054", "cliff", "C11 isolated normal diagnostic / preview only", r"auto_clay_close_(?:central|west)\.png"),
    (45574711897, 15003926824, "b652e0eb0006e9694d6b80ed5839b0cafbd007cc", "main", "morwen-vroid-macos-probe.yml", "morwen-isolated-vroid-reopen-review", "morwen", "VRoid editor framing evidence / preview only", r"frame-selected-(?:front|left4|left8|right4)\.png"),
    (45117436032, 14792665964, "5b47c2c7c0ab9f73b16e69ded05910da96038aa7", "feature/morwen-artdirected-sculpt-20261119", "morwen-isolated-vroid-reopen.yml", "morwen-isolated-vroid-reopen-review", "morwen", "VRoid editor reopen evidence / preview only", r"view-isolated-reopen-(?:front|back|left|right)\.png"),
    (44990707649, 14741951418, "99e09e44024e4f0bbaad6186133ee57a332b7124", "feature/lind-village-world-integration-plan-01", "aidan-interior-candidate.yml", "home-blueprint-batch-44990707649", "village", "HOME checkpoint render candidate / preview only", r"(?:front_three_quarter|interior_bedside)\.png"),
    (44853729639, 14686298362, "1405494117a4cf7f793b5814a280319fb2030bec", "feature/lind-village-world-integration-plan-01", "aidan-interior-candidate.yml", "aidan-interior-c03", "village", "HOME C03 comparison / preview only", r"(?:baseline|candidate)\.png"),
    (44850191454, 14684514477, "aa18ea5dd1d8304d35367f792f612cfed8e1880e", "feature/lind-village-world-integration-plan-01", "aidan-measured-blueprint.yml", "aidan-measured-blueprint", "blueprint", "Aidan measured candidate G1 BLOCKED / preview only", r"(?:exterior-(?:front|rear|left|right|roof)|interior-(?:floor-furniture|axonometric))\.png"),
    (45572622840, 15003297779, "41fac9e455910104a6d4b6121387f3d5da5b76e9", "main", "morwen-vroid-macos-probe.yml", "morwen-isolated-vroid-reopen-review", "morwen", "VRoid hair candidate / preview only", r"(?:evidence/)?hair-(?:before-selected|after-selected|reopened-geometry)\.png"),
    (45561010173, 14998780697, "3924c3708e5ed94efd898037664bb03141cfc285", "main", "morwen-vroid-macos-probe.yml", "morwen-isolated-vroid-reopen-review", "morwen", "VRoid selected framing / preview only", r"(?:evidence/)?frame-selected-(?:front|left4|left8|right4)\.png"),
    (44979340529, 14737506262, "cf0443ad1085d27f90127854ed48c9b168d87195", "feature/lind-cliff-rock-art-study-20261118", "lind-cliff-c11-method-e.yml", "c11-method-e-cf0443ad1085d27f90127854ed48c9b168d87195", "cliff", "C11 Method E / preview only", r"review/c11_(?:front|oblique|low)\.png"),
    (45028139012, 14756099327, "f7855075bd013ea10040111d8f67249f5f19d5f8", "feature/lind-village-world-integration-plan-01", "lind-bed-drape-isolated.yml", "isolated-bed-drape-45028139012", "village", "HOME isolated bed fixture / preview only", r"drape\.png"),
)

def preview_receipts(selection, known, saved):
    for rid, aid, head, branch, workflow, name, cat, stage, pattern in PREVIEW_RECEIPTS:
        if aid in known:
            continue
        run=api(f"repos/{REPO}/actions/runs/{rid}")
        if (run.get("head_sha")!=head or run.get("head_branch")!=branch or
            run.get("path")!=f".github/workflows/{workflow}" or run.get("conclusion")!="success" or
            (run.get("head_repository") or {}).get("full_name")!=REPO):
            raise ValueError(f"producer receipt mismatch: {rid}")
        a=api(f"repos/{REPO}/actions/artifacts/{aid}")
        if a.get("expired"):
            print(f"NOT_RUN expired preview receipt {aid}")
            continue
        if (a.get("name")!=name or a.get("workflow_run",{}).get("id")!=rid or
            a.get("workflow_run",{}).get("head_sha")!=head or not 0<a["size_in_bytes"]<=32*1024*1024):
            raise ValueError(f"artifact receipt mismatch: {aid}")
        target=saved/f"{aid}.zip"
        with target.open("wb") as out:
            subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{aid}/zip"],stdout=out,check=True)
        with target.open("rb") as stream:
            if "sha256:"+hashlib.file_digest(stream,"sha256").hexdigest()!=a.get("digest"):
                raise ValueError(f"archive digest mismatch: {aid}")
        with zipfile.ZipFile(target) as z:
            entries=sorted(i.filename for i in z.infolist() if 0<i.file_size<=8*1024*1024 and re.fullmatch(pattern,i.filename))
            if not entries or len(entries)!=len(set(entries)) or len(entries)>8:
                raise ValueError(f"missing or ambiguous preview images: {aid}")
            entry_sha256={n:hashlib.sha256(z.read(n)).hexdigest() for n in entries}
        selection.append(dict(run_id=rid,artifact_id=aid,head=head,category=cat,stage=stage,cover=entries[0],entries=entries,entry_sha256=entry_sha256,artifact_digest=a["digest"]))
        known.add(aid)

def discover():
    selection=json.loads(pathlib.Path(__file__).with_name("sync-selection.json").read_text())
    known={x["artifact_id"] for x in selection}
    saved=ROOT/"studio-zips";saved.mkdir(exist_ok=True)
    if os.environ.get("STUDIO_PREVIEW_MODELS")=="1":
        preview_vroid(selection,known,saved)
        preview_receipts(selection,known,saved)
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
                    if os.environ.get("STUDIO_PREVIEW_MODELS")=="1":
                        models=[i.filename for i in z.infolist() if 0<i.file_size<=32*1024*1024 and model_allowed(i.filename)]
                        entries.extend(models[:1])
                if entries:
                    selection.append(dict(run_id=run["id"],artifact_id=a["id"],head=run["head_sha"],category=cat,stage=a["name"][:80],cover=next((n for n in entries if allowed(n,cat)),None),entries=entries))
                    known.add(a["id"]);found=True;break
                target.unlink()
            if found:break
    (ROOT/"studio-discovered.json").write_text(json.dumps(selection,ensure_ascii=False))
    print(json.dumps([{"artifact":x["artifact_id"],"category":x["category"],"count":len(x["entries"])} for x in selection]))
if __name__=="__main__":discover()
