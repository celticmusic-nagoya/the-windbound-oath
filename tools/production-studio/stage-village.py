"""Stage existing commit-pinned village render images, never native sources."""
import hashlib, json, pathlib, subprocess, os
ROOT=pathlib.Path(os.environ["RUNNER_TEMP"])/"studio-site"
REPO=os.environ["GITHUB_REPOSITORY"]
SOURCES=[
(355,"d477176179af046db7ef86f3bdf8bbe92e47b1d2","assets/candidates/LIND-HOME-01/aidan_house_f9_c01","aidan-house-f9-c01",["front_three_quarter.png","rear_three_quarter.png","closeup_masonry_roof.png","interior_bedside.png","game_27deg.png","game/game_48px.png","game/game_48px_on_ground.png","game/game_48px_on_ground_x8_nearest.png","game/game_96px.png","game/game_96px_on_ground.png","game/game_96px_on_ground_x4_nearest.png"]),
(356,"f54a6856494d2cd5ad5124cf85b02981e05c8b63","assets/candidates/LIND-BUILD-01/lind_bld_kit_v1_c01","village-building-kit-c01",["lineup_peaceful_game27.png"]+[f"{kind}_{state}_game27.png" for kind in ["house_a","house_b","house_c","inn","shop","storage"] for state in ["peaceful","burning"]])]
def stage():
    manifest=ROOT/"gallery-manifest.json"
    data=json.loads(manifest.read_text())
    total=0
    for pr,head,base,stage_name,names in SOURCES:
        subprocess.run(["git","fetch","--no-tags","--depth=1","origin",head],check=True)
        for i,name in enumerate(names):
            path=base+"/"+name
            endpoint=f"repos/{REPO}/contents/{path}?ref={head}"
            meta=json.loads(subprocess.check_output(["gh","api",endpoint]))
            assert meta["type"]=="file" and 0<meta["size"]<=8*1024*1024
            raw=subprocess.check_output(["git","show",head+":"+path])
            assert len(raw)==meta["size"] and raw.startswith(b"\x89PNG\r\n\x1a\n")
            assert hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()==meta["sha"]
            total+=len(raw)
            assert total<=128*1024*1024
            sha=hashlib.sha256(raw).hexdigest()
            dest="published/"+sha+".png"
            (ROOT/dest).write_bytes(raw)
            data["entries"].append(dict(name=name,path=dest,sha256=sha,bytes=len(raw),head=head,category="village",stage=stage_name,cover=i==0,qa="NOT_RUN",adoption="UNDETERMINED",source_type="git",source_path=path,source_pr=pr,source_blob=meta["sha"]))
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":stage()
