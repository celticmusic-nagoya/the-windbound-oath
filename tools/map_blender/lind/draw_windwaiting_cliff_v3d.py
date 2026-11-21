"""Publish measured V3-D plan, elevations and sections without duplicating the full atlas."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection, PolyCollection
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
CG=ROOT/"assets/approved/game/cliff/sunset_background.png"


def axes_for(ax, title, labels):
    ax.set(title=title,xlabel=labels[0]+" (BU)",ylabel=labels[1]+" (BU)")
    ax.set_aspect("equal")
    ax.grid(alpha=.17)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    out=p.parse_args().output
    data=json.loads((out/"qa.json").read_text())
    target=np.asarray(data["authored_profile_vertices_BU"])
    mesh=data["authoring_mesh"]
    points=np.asarray(mesh["vertices"])
    faces=np.asarray([t["vertices"] for t in mesh["triangles"]])
    bands=[mesh["faces"][t["face"]]["material_id"] for t in mesh["triangles"]]
    colors=np.array(["#899caf","#799573","#5e8199","#a6a6aa"])
    with PdfPages(out/"target-plan-and-sections.pdf") as pdf:
        fig,axs=plt.subplots(1,2,figsize=(15,8),layout="constrained")
        for ax,index,title in [(axs[0],(0,1),"Plan | authored landward heel, crest and toe"),
                               (axs[1],(0,2),"Sea elevation | authored grades and shelf bands")]:
            for j,c,label in [(0,"#326394","Toe"),(4,"#716abc","Lower shelf"),
                              (7,"#80543d","Middle shelf"),(9,"#2f7c4a","Turf lip"),(-2,"#899caf","Buried heel")]:
                ax.plot(target[:,j,index[0]],target[:,j,index[1]],color=c,lw=1.3,marker=".",label=label)
            if index[1]==2:
                for x,label in ((2.78,"Shoulder 1"),(5.17,"Incision"),(7.86,"Shoulder 2")):
                    i=min(range(len(target)),key=lambda i:abs(target[i,9,0]-x))
                    ax.annotate(label,target[i,9,[0,2]],xytext=(0,16),textcoords="offset points",
                                rotation=13,fontsize=9)
            axes_for(ax,title,("X","Y" if index[1]==1 else "Z"))
            ax.legend(fontsize=8)
        fig.suptitle("V3-D | Continuous headland target controls (provisional)",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        fig,axs=plt.subplots(2,3,figsize=(16,9),layout="constrained")
        for ax,section in zip(axs.flat,data["measured_sections"]):
            for name,col in [("previous","#a5adb7"),("v3d","#285b84")]:
                ax.add_collection(LineCollection(section["YZ_segments"][name],colors=col,lw=.8,label=name))
            ax.set(xlim=(-30,5),ylim=(-1.8,10))
            ax.axhline(0,color="#50a9cc",ls=":",lw=.7)
            axes_for(ax,f'X={section["X_BU"]:.2f} | actual section',("Y","Z"))
        axs.flat[0].legend(fontsize=8)
        fig.suptitle("V3-D | V3-C and candidate triangle-plane intersections",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        fig,axs=plt.subplots(1,3,figsize=(16,8),layout="constrained")
        axs[0].imshow(Image.open(CG))
        axs[0].set_title("Official CG | visual target")
        axs[1].imshow(Image.open(out/"clay-sunset.png"))
        axs[1].set_title("Candidate | fixed sunset")
        axs[2].imshow(Image.open(out/"visible-ids.png"))
        axs[2].set_title("Candidate | first-hit geometry")
        for ax in axs: ax.axis("off")
        fig.suptitle("V3-D | Composition and visibility",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        fig,axs=plt.subplots(1,2,figsize=(14,8),layout="constrained")
        for ax,index,label in [(axs[0],(0,1),"Plan / measured authoring mesh"),
                               (axs[1],(0,2),"Elevation / measured authoring mesh")]:
            ax.add_collection(PolyCollection(points[faces][:,:,index],facecolors=colors[bands],
                                             edgecolors="#384c62",lw=.18,alpha=.43))
            ax.autoscale()
            axes_for(ax,label,("X","Y" if index[1]==1 else "Z"))
        fig.suptitle("V3-D | Actual vertex and face layout",fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)


if __name__=="__main__":
    main()
