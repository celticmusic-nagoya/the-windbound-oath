"""Plot V3's authored plan target and the held-camera visual registration."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
CG=ROOT/"assets/approved/game/cliff/sunset_background.png"
COLORS={"main":"#55c2e3","shoulder-a":"#efab63","shoulder-b":"#df73a2"}
# Manually registered image references, distinct from all native mesh measurements.
# A horizon match and horizontal sun match do not calibrate focal length/depth.
FIXED_RASTER=(605,341)
FIXED_HORIZON_Y=146
FIXED_SUN=(450,87)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("folder",type=Path)
    out=ap.parse_args().folder
    data=json.loads((out/"qa.json").read_text())
    mask_data=json.loads((out/"visibility.json").read_text())
    v2=json.loads((ROOT/"assets/candidates/lind/windwaiting-cliff-playable/cliff-v2/projected-exposure.json").read_text())
    raw=data["cg_image_landmarks_px"]
    cw,ch=data["cg_reference_image_px"]
    w,h=FIXED_RASTER
    dx=FIXED_SUN[0]/w-raw["sun"][0]/cw
    dy=FIXED_HORIZON_Y/h-raw["horizon"][0][1]/ch
    registered={k:[(p[0]/cw+dx)*w,(p[1]/ch+dy)*h] for k,p in raw.items() if k!="horizon"}
    registration={
      "kind":"two-dimensional normalized translation only",
      "source_CG_pixels":raw,
      "fixed_render_anchor_pixels":{"size":FIXED_RASTER,"horizon_y":FIXED_HORIZON_Y,"sun":FIXED_SUN},
      "normalized_shift_xy":(dx,dy),
      "guide_landmarks_fixed_image_px":registered,
      "sun_vertical_residual_px":registered["sun"][1]-FIXED_SUN[1],
      "unknown":["canonical focal length","absolute camera pose","occluded geometry and depth","world placement"],
      "visibility_by_part":mask_data["parts"],
      "v2_first_hit_rock_pixels":v2["captures"]["current"]["first_hit_pixels"],
      "v2_rock_pixels_at_or_below_4_8_BU":v2["captures"]["current"]["pixels_at_or_below_Z_4_8_BU"],
    }
    out.joinpath("reference-registration.json").write_text(json.dumps(registration,indent=2)+"\n")
    with PdfPages(out/"v3-target-and-sections.pdf") as pdf:
        fig,axs=plt.subplots(1,2,figsize=(14,8),layout="constrained")
        axs[0].imshow(Image.open(CG).resize((cw,ch)))
        axs[1].imshow(Image.open(out/"clay-sunset.png"))
        for label,point in raw.items():
            if label=="horizon":
                axs[0].plot(*zip(*point),color="#60dafa",lw=.8,ls="--")
                continue
            for ax,pt in ((axs[0],point),(axs[1],registered[label])):
                ax.plot(*pt,"o",markersize=3,color="#ffb461")
                ax.annotate(label.replace("_"," "),pt,xytext=(4,-9),textcoords="offset points",
                            fontsize=7,color="white",bbox={"facecolor":"#173553","alpha":.7,"pad":1})
        axs[1].axhline(FIXED_HORIZON_Y,ls="--",color="#60dafa",lw=.8)
        for ax,title in zip(axs,["Official CG | image landmarks","Fixed scene camera | projected guide"]):
            ax.set_title(title)
            ax.axis("off")
        fig.suptitle("V3 | Image registration guide",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        fig,axs=plt.subplots(1,2,figsize=(14,8),layout="constrained")
        for name,part in data["target_plan_controls_BU"].items():
            plan=part["plan"]
            axs[0].add_patch(Polygon(plan,facecolor=COLORS[name],edgecolor="#173553",alpha=.55,label=name))
            levels=np.asarray(part["levels"])
            axs[1].plot(levels[:,2],levels[:,0],marker=".",color=COLORS[name],label=name)
        if "landward_tie_footprint_BU" in data:
            axs[0].add_patch(Polygon(data["landward_tie_footprint_BU"],facecolor="#c0a776",
                                     edgecolor="#645130",alpha=.55,label="landward tie"))
        axs[0].set(xlim=(-7.5,11.5),ylim=(-28,1),xlabel="X (BU)",ylabel="Y (BU)",
                   title="Authored footprint by component")
        axs[0].set_aspect("equal")
        axs[1].set(xlabel="Cross-shore ring scale",ylabel="Z (BU)",title="Authored bedding breaks")
        for ax in axs:
            ax.legend()
            ax.grid(alpha=.2)
        fig.suptitle("V3 | Target plan and bedding controls (provisional)",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        fig,axs=plt.subplots(2,3,figsize=(15,9),layout="constrained")
        for ax,slice_ in zip(axs.flat,data["measured_sections"]):
            for key,color in [("previous","#8e99a3"),("v3","#245f93")]:
                ax.add_collection(LineCollection(slice_["YZ_segments"][key],colors=color,lw=1,label=key))
            ax.set(xlim=(-29,4),ylim=(-1.5,10),xlabel="Y (BU)",ylabel="Z (BU)",
                   title=f'X = {slice_["X_BU"]:.2f} BU')
            ax.axhline(0,ls=":",c="#3c98b7")
            ax.set_aspect("equal")
            ax.grid(alpha=.2)
        axs.flat[0].legend()
        fig.suptitle("V3 | Actual mesh sections against V2",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)


if __name__=="__main__":
    main()
