"""MORWEN walk candidate: PNG transparency, dimensions, and frame differences."""
from pathlib import Path
import json
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/mvp-blockout-01"
summary={}
for direction in ("front","left","right","back"):
    frames=[]
    bounds=[]
    for frame in range(1,9):
        path=OUT/"walk_views"/direction/f"{frame:02d}.png"
        with Image.open(path) as im:
            assert im.size==(512,768),(path,im.size)
            assert im.mode=="RGBA",(path,im.mode)
            alpha=im.getchannel("A")
            bbox=alpha.getbbox()
            assert bbox is not None,(path,"empty")
            assert bbox[0]>0 and bbox[1]>0 and bbox[2]<512 and bbox[3]<768,(path,bbox)
            assert alpha.getextrema()[0]==0,(path,"no transparency")
            frames.append(im.copy())
            bounds.append(bbox)
    differences=[]
    for i in range(8):
        diff=ImageChops.difference(frames[i],frames[(i+1)%8])
        differences.append(diff.getbbox() is not None)
    assert all(differences),(direction,"identical neighboring frames",differences)
    summary[direction]={"frame_count":8,"size":[512,768],"alpha":"PASS",
                        "nonempty":"PASS","changed_between_adjacent_frames":"PASS",
                        "bounds":bounds}
(OUT/"walk_visual_qa.json").write_text(json.dumps({
 "status":"TECHNICAL_PASS","art_qa":"NOT_RUN",
 "ground_contact":"NOT_RUN","joint_anatomy":"NOT_RUN",
 "directions":summary},indent=2)+"\n")
print("MORWEN_WALK_IMAGE_QA_PASS")
