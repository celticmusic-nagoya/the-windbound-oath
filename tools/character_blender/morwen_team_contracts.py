"""Independent non-generative team contracts. No artistic judgement is automated."""
import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument("--role",choices=["design","art-review"],required=True);p.add_argument("--output",required=True)
a=p.parse_args();root=pathlib.Path("assets/canonical/morwen/2026-11-16")
manifest=json.loads((root/"MANIFEST.json").read_text())
required={"LAYER0_FRONT.png","LAYER0_BACK.png","LAYER0_PROFILE_FACING_RIGHT.png","LAYER0_PROFILE_FACING_LEFT.png","MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg"}
files={f["filename"]:f for f in manifest["files"]}
checks={name: name in files and (root/name).is_file() and hashlib.sha256((root/name).read_bytes()).hexdigest()==files[name]["sha256"] for name in sorted(required)}
base={"team":a.role,"canonical_sha_checks":checks,"reference_manifest":"assets/canonical/morwen/2026-11-16/MANIFEST.json","canonical_unchanged":all(checks.values()),"geometry_created":False,"independent_visual_review":"NOT_RUN"}
if a.role=="design":
 base.update(status="PASS_REFERENCE_INPUTS_ONLY" if all(checks.values()) else "BLOCKED",production_requirements={"heads_range":[7.5,8.0],"directions":["front","back","facing_right","facing_left"],"garter":"anatomical right leg","modules":["head","hair","torso","arms","lower_garment","legs","socks","shoes","accessories"]},"geometry_qa":"NOT_RUN","design_conformance":"BLOCKED")
else:
 base.update(status="BLOCKED_VISUAL_REVIEW_REQUIRED",artistic_quality":"NOT_RUN",direction_conformance":"NOT_RUN",review_evidence_required=["four rendered PNGs","four canonical reference comparisons","independent human or actual vision-model review"])
pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True)
pathlib.Path(a.output).write_text(json.dumps(base,ensure_ascii=False,indent=2))
print(json.dumps(base,ensure_ascii=False))
if not all(checks.values()):raise SystemExit(1)
