from pathlib import Path
from PIL import Image
import json,sys
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path("render_output/morwen_walk")
sheet=Image.new("RGBA",(3072,2304),(0,0,0,0))
for row,view in enumerate(("front","right","back","left")):
    for col in range(8):
        with Image.open(out/f"{view}_{col+1:02d}.png") as image:
            if image.mode!="RGBA" or image.size!=(384,576):
                raise ValueError(f"Invalid RGBA image: {view}_{col+1:02d}")
            sheet.paste(image,(col*384,row*576))
sheet.save(out/"MORWEN_WALK_4x8.png")
(out/"sheet_qa.json").write_text(json.dumps({"frames":32,"size":[3072,2304],"G3":"PASS","G2":"NOT_RUN","production_approved":False},indent=2))
