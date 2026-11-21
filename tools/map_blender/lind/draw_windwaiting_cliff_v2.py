"""Generate amended sheets for edited cliff geometry and retain the original atlas."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon
import numpy as np
from PIL import Image

from draw_windwaiting_cliff_blueprint import section_lines

ROOT=Path(__file__).resolve().parents[3]
REFERENCE=ROOT/"assets/approved/game/cliff/sunset_background.png"
PLANES=[-4.35,-1.05,3.35,4.55,7.30,9.80]


def key(mesh,face):
    return tuple(sorted(tuple(round(c,6) for c in mesh["vertices"][i]) for i in face["vertices"]))


def records(mesh,indices):
    return [{
        "face_id":i,
        "xyz_BU":[mesh["vertices"][v] for v in mesh["faces"][i]["vertices"]],
        **{k:v for k,v in mesh["faces"][i].items() if k!="vertices"},
    } for i in indices]


def section_landmarks(report, stations):
    geometry=report["measurement"]["loft"]
    xyz=np.asarray(geometry["vertices"])
    landmarks=[]
    for station in stations:
        x=station[0]
        ring=xyz[np.abs(xyz[:,0]-x)<1e-5]
        if len(ring):
            top=ring[np.argmax(ring[:,2])]
            toe=ring[np.argmin(ring[:,1])]
            landmarks.append({"X_BU":x,"toe_xyz_BU":toe.tolist(),"crest_xyz_BU":top.tolist(),
                              "axis_sample_vertex_count":len(ring)})
    return landmarks


def figure_page(fig,pdf,out,name,title,note):
    fig.suptitle(title,x=.06,ha="left",fontsize=17,color="#183a5a")
    fig.text(.06,.918,note,fontsize=9,color="#395673")
    fig.subplots_adjust(top=.85,bottom=.09,left=.075,right=.94,hspace=.57,wspace=.33)
    pdf.savefig(fig)
    path=out/(name+".svg")
    fig.savefig(path)
    path.write_text("".join(line.rstrip()+"\n" for line in path.read_text().splitlines()))
    plt.close(fig)


def material_projection(ax,mask,record):
    for row in record["rows"]:
        for left,right in row["inclusive_x_spans"]:
            mask[row["y"],left:right+1]=1
    if record["first_hit_pixels"]:
        ax.contour(np.arange(mask.shape[1])+.5,np.arange(mask.shape[0])+.5,mask,
                   levels=[.5],colors=["#5cebfb"],linewidths=.85)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("baseline",type=Path)
    ap.add_argument("out",type=Path)
    args=ap.parse_args()
    out=args.out
    old=json.loads(args.baseline.read_bytes())
    new=json.loads((out/"structure.json").read_bytes())
    meshes={label:report["measurement"]["joined"] for label,report in [("previous",old),("v2",new)]}
    a,b=meshes.values()
    keys=[{key(mesh,f):i for i,f in enumerate(mesh["faces"])} for mesh in (a,b)]
    changes={}
    for label,idx in [("previous",0),("v2",1)]:
        face_ids=[keys[idx][k] for k in sorted(keys[idx].keys()-keys[1-idx].keys())]
        changes[label]={"face_count":len(face_ids),"materials":meshes[label]["materials"],
                        "faces":records(meshes[label],face_ids)}
    measured=[{"X_BU":x+.001,"segments_YZ_BU":{n:np.asarray(section_lines(mesh,0,x+.001)).tolist()
                                                       for n,mesh in meshes.items()}}
              for x in PLANES]
    col=lambda x: hashlib.file_digest(x.open("rb"),"sha256").hexdigest()
    payload={"source_structure_sha256":col(args.baseline),
             "status":"provisional playable candidate",
             "units":new["units"],
             "measurement":{"changed_faces":changes,"sections":measured,
                 "joined_topology":b["topology"],"structural_QA":new["joined_qa"],
                 "loft_landmarks":{label:section_landmarks(report,report["candidate_stations_BU"])
                                   for label,report in [("previous",old),("v2",new)]}},
             "design_targets":{"stations":new["candidate_stations_BU"],"profiles":new["candidate_section_profiles_BU"],
                               "basis":"fixed-camera sightline and authored depth; no official world dimensions"},
             "gameplay":new["gameplay"],"pbr_source":new["pbr_source"],"carrier_edit":new["carrier_edit"]}
    (out/"structure-delta.json").write_text(json.dumps(payload,separators=(",",":"))+"\n")
    with PdfPages(out/"cliff-v2-amendments.pdf") as pdf:
        fig,axs=plt.subplots(2,3,figsize=(15,9))
        for axis,row in zip(axs.flat,measured):
            for label,color in [("previous","#a1acb5"),("v2","#24587f")]:
                axis.add_collection(LineCollection(row["segments_YZ_BU"][label],colors=color,
                                                   lw=1.2,label=label))
            axis.set(xlim=(-26,2),ylim=(-1,10),title=f'X = {row["X_BU"]:.3f} BU',xlabel="Y (BU)",ylabel="Z (BU)")
            axis.set_aspect("equal")
            axis.axhline(0,ls=":",lw=.7,color="#64a7cf")
            axis.grid(alpha=.2)
        axs[0,0].legend(fontsize=8)
        figure_page(fig,pdf,out,"01-edited-sections","V2 | Edited bedrock sections",
                    "Triangle-plane intersections from evaluated meshes • previous in gray • V2 in blue • each plane is displaced +0.001 BU from design station")

        fig,axs=plt.subplots(1,2,figsize=(14,8))
        for i,(name,report) in enumerate([("Previous",old),("V2",new)]):
            ax=axs[i]
            stations=np.asarray(report["candidate_stations_BU"])
            ax.plot(stations[:,0],stations[:,1],label="Seaward toe",c="#1b567a",lw=1.75,marker=".")
            ax.plot(stations[:,0],stations[:,3],label="Shelf",c="#b98050")
            ax.plot(stations[:,0],stations[:,4],label="Crest",c="#71833d",ls="--")
            if i:
                for x,t in [(3.35,"Shoulder A"),(4.55,"Gully"),(7.30,"Shoulder B")]:
                    point=next(v for v in stations if abs(v[0]-x)<1e-4)
                    ax.annotate(t,(x,point[4]),xytext=(4,9),textcoords="offset points",fontsize=9)
            ax.set(xlim=(-8,12),ylim=(-26,0),title=f"{name} | Plan controls",xlabel="X (BU)",ylabel="Y (BU)")
            ax.set_aspect("equal")
            ax.grid(alpha=.15)
            ax.legend(fontsize=8)
        figure_page(fig,pdf,out,"02-shelf-and-gully-plan","V2 | Shelf plan and gully",
                    "Authored profile controls in provisional space • see sheet 01 for measured section lines • official depth remains unregistered")

        fig,axs=plt.subplots(1,3,figsize=(16,8))
        axs[0].imshow(Image.open(REFERENCE).resize((836,471)))
        for name,ring in new["cg_image_measurement"]["polygons"].items():
            if name!="foreground_occluder":
                axs[0].add_patch(Polygon(ring,fill=False,edgecolor="#5cebfb",lw=.85))
        axs[0].set_title("Official CG · traced rock")
        exposure=json.loads((out/"projected-exposure.json").read_text())
        w,h=exposure["image_size_px"]
        for ax,label,file in zip(axs[1:],("previous","current"),("old-sunset.png","pbr-sunset.png")):
            record=exposure["captures"][label]
            ax.imshow(Image.open(out/file),extent=(0,w,h,0))
            material_projection(ax,np.zeros((h,w)),record)
            ax.set_title(f'{label.title()} · {record["first_hit_pixels"]:,} rock pixels')
        for ax in axs:
            ax.axis("off")
        figure_page(fig,pdf,out,"03-fixed-sunset-exposure","V2 | Fixed sunset exposure",
                    "Cyan: first-hit authored rock • identical prior/V2 camera • official trace uses another projection and is not a world-space measure")


        fig,axs=plt.subplots(1,2,figsize=(14,8))
        cut=np.array(new["carrier_edit"]["wedge_floor_xyz_BU"])
        axs[0].add_patch(Polygon(cut[:,:2],facecolor="#99b9c8",edgecolor="#24536e",alpha=.65))
        for i,(x,y,z) in enumerate(cut):
            axs[0].annotate(f"P{i+1}  Z={z:.2f}",(x,y),xytext=(3,4),textcoords="offset points",fontsize=8)
        axs[0].set(xlim=(-11,-2.8),ylim=(-8.2,-2.4),xlabel="X (BU)",ylabel="Y (BU)",
                   title="Seaward wedge and cutter floor elevations")
        axs[0].set_aspect("equal")
        for label,color in [("previous","#a1acb5"),("v2","#24587f")]:
            axs[1].add_collection(LineCollection(section_lines(meshes[label],0,-7.499),
                                                 colors=color,lw=1.25,label=label))
        axs[1].set(xlim=(-9,1.5),ylim=(1.5,8),xlabel="Y (BU)",ylabel="Z (BU)",
                   title="Evaluated section at X = −7.499 BU")
        axs[1].set_aspect("equal")
        axs[1].legend(fontsize=8)
        for ax in axs:
            ax.grid(alpha=.15)
        figure_page(fig,pdf,out,"04-seaward-brow","V2 | Seaward brow and join",
                    "Wedge coordinates are authored • section lines are measured • walkable and vegetation support rays checked after the cut")


if __name__=="__main__":
    main()
