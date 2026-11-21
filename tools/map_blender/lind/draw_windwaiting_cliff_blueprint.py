"""Render vector engineering sheets from the measured Blender scene data."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Circle, Polygon
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/"assets/candidates/lind/windwaiting-cliff-playable"
ROCK, GRASS, ROAD, WATER = "#8195aa", "#77976c", "#ae6e34", "#56a7ca"


def vertices_and_triangles(mesh):
    points=np.asarray(mesh["vertices"],dtype=float)
    return points,np.asarray([t["vertices"] for t in mesh["triangles"]],dtype=int)


def decorate(ax,title,x,y):
    ax.set(title=title,xlabel=x,ylabel=y)
    ax.set_aspect("equal")
    ax.grid(alpha=.15)


def orthographic(ax, mesh, axes, depth, title, mirror=False):
    points,ids=vertices_and_triangles(mesh)
    tris=points[ids]
    faces=[mesh["faces"][t["face"]] for t in mesh["triangles"]]
    colors=np.asarray([GRASS if "turf" in (mesh["materials"][f["material_id"]]["name"] or "").lower()
                       else ROCK for f in faces])
    # Painter's order uses the omitted world axis; mirrored views retain
    # true axis labels with descending ticks.
    order=np.argsort(tris[:,:,depth[0]].mean(axis=1)*depth[1])
    ax.add_collection(PolyCollection(tris[order][:,:,axes],facecolors=colors[order],
                                     edgecolors="none",rasterized=True))
    # Keep silhouette and material-transition work as editable vectors.
    projected_edges={}
    for triangle, face in zip(ids,faces):
        key=(face["normal"][depth[0]]>=0,face["material_id"])
        for a,b in zip(triangle,np.roll(triangle,-1)):
            projected_edges.setdefault(tuple(sorted((a,b))),set()).add(key)
    drawing=[edge for edge,records in projected_edges.items() if len(records)>1]
    if drawing:
        ax.add_collection(LineCollection(points[np.asarray(drawing)][:,:,axes],
                                         colors="#32485c",linewidths=.25,alpha=.45))
    ax.autoscale()
    if mirror:
        ax.invert_xaxis()
    decorate(ax,title,"XYZ"[axes[0]]+" (BU)","XYZ"[axes[1]]+" (BU)")


def section_lines(mesh, axis, position):
    points,ids=vertices_and_triangles(mesh)
    tris=points[ids]
    values=tris[:,:,axis]-position
    crossing=(values.min(axis=1)<0)&(values.max(axis=1)>=0)
    ij=[i for i in range(3) if i!=axis]
    result=[]
    for tri, delta in zip(tris[crossing],values[crossing]):
        hits=[]
        for i,j in ((0,1),(1,2),(2,0)):
            if (delta[i]<0)!=(delta[j]<0):
                hit=tri[i]+(tri[j]-tri[i])*(delta[i]/(delta[i]-delta[j]))
                hits.append(hit[ij])
        if len(hits)==2:
            result.append(hits)
    return result


def section(ax,data,axis,position):
    for key,color in [("carrier","#b2b6b9"),("joined","#246494")]:
        lines=section_lines(data[key],axis,position)
        ax.add_collection(LineCollection(lines,linewidths=.7,colors=color,label=key))
    ax.axhline(0,c=WATER,lw=.6,ls=":")
    ax.set_xlim((-12,8) if axis==0 else (-13,12))
    ax.set_ylim(-1.75,10)
    decorate(ax,f"{'XYZ'[axis]} = {position:+.3f} BU","Y (BU)" if axis==0 else "X (BU)","Z (BU)")


def material_edges(mesh):
    assignments={}
    for face in mesh["faces"]:
        ring=face["vertices"]
        for a,b in zip(ring,ring[1:]+ring[:1]):
            assignments.setdefault(tuple(sorted((a,b))),set()).add(face["material_id"])
    return [edge for edge,materials in assignments.items() if len(materials)>1]


def steep_break_edges(mesh):
    """Find measured face-angle breaks, rather than labeling UV seams as cracks."""
    adjacency={}
    for face in mesh["faces"]:
        ring=face["vertices"]
        for a,b in zip(ring,ring[1:]+ring[:1]):
            adjacency.setdefault(tuple(sorted((a,b))),[]).append(face["normal"])
    return [edge for edge,normals in adjacency.items()
            if len(normals)==2 and np.dot(*normals)<np.cos(np.deg2rad(40))]


def topology(ax,mesh,view,labels=False):
    points=np.asarray(mesh["vertices"])
    xy=points[:,view]
    edge_ids=np.asarray(mesh["edges"])
    ax.add_collection(LineCollection(xy[edge_ids],colors="#385769",linewidths=.36,alpha=.65))
    boundaries=material_edges(mesh)
    if boundaries:
        ax.add_collection(LineCollection(xy[np.asarray(boundaries)],colors="#6e953f",linewidths=1.9))
    if labels:
        for idx in range(0,len(xy),24):
            ax.text(*xy[idx],str(idx),fontsize=6,color="#12345a")
    ax.autoscale()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("folder",type=Path)
    out=parser.parse_args().folder.resolve()
    structure=json.loads((out/"structure.json").read_text())
    data=structure["measurement"]
    loft=data["loft"]
    planes=[(0,s[0]+.001) for s in structure["candidate_stations_BU"]]
    planes += [(1,y) for y in (-9.2,-8.0,-6.5,-4.8,-3.2,-1.6)]
    measured={
        "units":"provisional Blender units",
        "sections":[{"axis":"XYZ"[axis],"position":value,
                     "coordinates":"YZ" if axis==0 else "XZ",
                     "segments":{key:np.asarray(section_lines(data[key],axis,value)).tolist()
                                 for key in ("carrier","joined")}}
                    for axis,value in planes],
        "loft_face_angle_break_edges_over_40_degrees":steep_break_edges(loft),
        "material_boundary_edges":{"encoding":"vertex ID pairs indexing structure.json per mesh",
                                   **{key:material_edges(data[key]) for key in ("loft","joined")}},
    }
    (out/"measured-sections.json").write_text(json.dumps(measured,separators=(",",":"))+"\n")
    with PdfPages(out/"cliff-blueprint.pdf") as pdf:
        def save(fig, number, title, subtitle):
            fig.suptitle(f"Windwaiting Cliff | {number}  {title}",x=.03,ha="left",fontsize=18,color="#173650")
            fig.text(.03,.922,subtitle,fontsize=9,color="#37526b")
            fig.subplots_adjust(left=.07,right=.96,top=.87,bottom=.09,hspace=.52,wspace=.29)
            pdf.savefig(fig)
            svg=out/f"{number}-{title.lower().replace(' ','-')}.svg"
            fig.savefig(svg)
            svg.write_text("".join(line.rstrip()+"\n" for line in svg.read_text().splitlines()))
            plt.close(fig)

        fig,axs=plt.subplots(2,3,figsize=(15,9))
        for ax,spec in zip(axs.flat,[((0,2),(1,-1),"Front · sea (-Y)"),
                                    ((0,2),(1,1),"Rear · inland (+Y)",True),
                                    ((1,2),(0,-1),"Left · west (-X)",True),
                                    ((1,2),(0,1),"Right · east (+X)"),
                                    ((0,1),(2,1),"Plan · top (+Z)")]):
            orthographic(ax,data["joined"],*spec)
        axs.flat[-1].axis("off")
        axs.flat[-1].text(0,.72,"Orthographic projection of the evaluated Blender mesh.\nSlate blue: rock-bearing carrier and authored rock.\nGreen: explicit turf material slots.\nMeadow coverage on carrier is shader-driven.",size=11,va="top")
        save(fig,"01","Orthographic views","Measured geometry • provisional coordinates • sea towards negative Y")

        fig,axs=plt.subplots(2,3,figsize=(15,9))
        for ax,station in zip(axs.flat,structure["candidate_stations_BU"]):
            section(ax,data,0,station[0]+.001)
        axs.flat[0].legend(loc="upper left",fontsize=8)
        save(fig,"02","Transverse sections","Six X sections from exact triangle-plane intersections • 0.001 BU offset avoids vertex ambiguity")

        fig,axs=plt.subplots(2,3,figsize=(15,9))
        for ax,y in zip(axs.flat,(-9.2,-8.0,-6.5,-4.8,-3.2,-1.6)):
            section(ax,data,1,y)
        axs.flat[0].legend(loc="upper left",fontsize=8)
        save(fig,"03","Longitudinal sections","Six additional Y sections • gray is original carrier, blue is the joined candidate")

        fig,axs=plt.subplots(2,2,figsize=(15,9))
        for ax,view,title in [(axs[0,0],(0,1),"Plan · turf / bedrock material edges"),
                              (axs[0,1],(0,2),"Sea elevation · shelves, gullies and overhang profile"),
                              (axs[1,0],(1,2),"West profile · polygon boundaries")]:
            topology(ax,loft,view,labels=ax is axs[0,0])
            decorate(ax,title,"XYZ"[view[0]]+" (BU)","XYZ"[view[1]]+" (BU)")
        breaks=np.asarray(steep_break_edges(loft))
        if len(breaks):
            points=np.asarray(loft["vertices"])
            axs[0,1].add_collection(LineCollection(points[breaks][:,:,[0,2]],colors="#ad5835",
                                                    linewidths=1.1,alpha=.85))
        ax=axs[1,1]
        points=np.asarray(loft["vertices"])
        normals=np.asarray([f["normal"] for f in loft["faces"]])
        centres=np.asarray([points[f["vertices"]].mean(axis=0) for f in loft["faces"]])
        sl=np.arange(0,len(centres),14)
        ax.quiver(centres[sl,0],centres[sl,2],normals[sl,0],normals[sl,2],
                  [loft["faces"][i]["slope_degrees"] for i in sl],cmap="plasma",angles="xy")
        decorate(ax,"Face normals · slope coloring","X (BU)","Z (BU)")
        for index,label in [(1,"Bedrock scarp"),(3,"Shoulder A"),(4,"Gully"),(5,"Shoulder B")]:
            station=structure["candidate_stations_BU"][index]
            axs[0,1].annotate(label,(station[0],station[5]),xytext=(2,10),
                              textcoords="offset points",fontsize=7,rotation=12)
        save(fig,"04","Rock topology","New loft • green: material boundaries • rust: face breaks above 40° • labels: measured vertex IDs")

        fig=plt.figure(figsize=(15,9))
        layout=fig.add_gridspec(3,2,width_ratios=[1.4,1])
        uv_ax=fig.add_subplot(layout[:,0])
        uv=[f["uv"] for f in loft["faces"]]
        color=[GRASS if f["material_id"] else ROCK for f in loft["faces"]]
        uv_ax.add_collection(PolyCollection(uv,facecolors=color,alpha=.20,
                                             edgecolors="#344a5c",linewidths=.35))
        uv_ax.autoscale()
        decorate(uv_ax,"Authored repeated UVs","U","V")
        photo=BASE/"photo-pbr/rock_boulder_dry"
        for i,(channel,title) in enumerate([("basecolor","Base color · sRGB"),
                                             ("normal","Normal · linear, OpenGL"),
                                             ("roughness","Roughness · linear")]):
            ax=fig.add_subplot(layout[i,1])
            path=photo/structure["pbr_source"]["textures"][channel]["path"]
            if path.exists():
                ax.imshow(Image.open(path))
            ax.axis("off")
            ax.set_title(title)
        save(fig,"05","Photo PBR and UV","Poly Haven Rock Boulder Dry (CC0) • packed base color, normal and roughness • texture repeats every 1.30 BU")

        fig,axs=plt.subplots(1,2,figsize=(15,8))
        for ax,(mode,rows),name in zip(axs,structure["visibility"].items(),("old-sunset.png","native-sunset.png")):
            img=Image.open(out/name)
            ax.imshow(img,extent=(0,1,0,1),aspect="auto")
            for label,col in [(False,"#62f2d0"),(True,"#ff9959")]:
                points=[r["uv"] for r in rows if bool(r["occluded_by"])==label]
                if points:
                    ax.scatter(*zip(*points),s=7,alpha=.55,color=col,
                               label=f"{'Occluded' if label else 'Visible'} ({len(points)})")
            ax.set(xlim=(0,1),ylim=(0,1),title=mode.title()+" · sunset camera")
            ax.legend(loc="lower left",fontsize=8)
        save(fig,"06","Visibility and occlusion","Outward rock triangle ray samples at four barycentric locations • counts are not image area")

        fig,axs=plt.subplots(1,2,figsize=(15,8))
        nav=json.loads((BASE/"navigation.json").read_text())
        grid=np.asarray([float("nan") if z is None else z for z in nav["levels"]]).reshape(nav["height"],nav["width"])
        x=np.arange(nav["width"])*nav["stride"]+nav["origin"][0]
        y=-(np.arange(nav["height"])*nav["stride"]+nav["origin"][1])
        axs[0].pcolormesh(x,y,grid,shading="nearest",cmap="YlGn",rasterized=True)
        road,ids=vertices_and_triangles(data["road"])
        axs[0].add_collection(PolyCollection(road[ids][:,:,:2],facecolors=ROAD,edgecolors="none"))
        axs[0].plot(nav["spawn"][0],-nav["spawn"][2],"ko",label="Spawn")
        for index,(obstacle_x,obstacle_z,radius) in enumerate(nav["obstacles"]):
            axs[0].add_patch(Circle((obstacle_x,-obstacle_z),radius,fill=False,
                                    edgecolor="#a62e53",lw=.7,label="Collision radius" if index==0 else None))
        axs[0].legend()
        decorate(axs[0],"Navigation grid and road","X (BU)","Y (BU)")
        orthographic(axs[1],data["carrier"],(0,1),(2,1),"C8-B surface · chassis geometry")
        topology(axs[1],loft,(0,1))
        axs[1].set_title("Reference carrier and candidate overlay")
        save(fig,"07","Road and collision","Runtime continues to raycast the existing baseline cliff/road colliders • candidate overlay is visual")

        fig,axs=plt.subplots(1,3,figsize=(16,8))
        cg=Image.open(ROOT/"assets/approved/game/cliff/sunset_background.png").resize((836,471))
        axs[0].imshow(cg)
        for name,poly in structure["cg_image_measurement"]["polygons"].items():
            if name!="foreground_occluder":
                axs[0].add_patch(Polygon(poly,fill=False,edgecolor="#55e5ff",lw=1.3))
            else:
                axs[0].plot(*zip(*poly),color="#ffc571",ls=":")
        axs[0].set_title("Official image · traced exposure and silhouette")
        projection=json.loads((out/"projected-exposure.json").read_text())
        source_width,source_height=projection["image_size_px"]
        for ax,mode,name,title in zip(axs[1:],("previous","current"),
                                     ("old-sunset.png","native-sunset.png"),
                                     ("Previous fixed sunset","Rebuilt fixed sunset")):
            ax.imshow(Image.open(out/name),extent=(0,source_width,source_height,0))
            record=projection["captures"][mode]
            mask=np.zeros((source_height,source_width))
            for row in record["rows"]:
                for a,b in row["inclusive_x_spans"]:
                    mask[row["y"],a:b+1]=1
            if record["first_hit_pixels"]:
                ax.contour(np.linspace(.5,source_width-.5,source_width),
                           np.linspace(.5,source_height-.5,source_height),
                           mask,levels=[.5],colors=["#55e5ff"],linewidths=.85)
            ax.set_title(f'{title} · {record["first_hit_pixels"]:,} rock pixels')
        for ax in axs:
            ax.axis("off")
        save(fig,"08","Official CG comparison","Traces and first-hit masks use different unregistered cameras • output widths indicate composition scale, not a spatial registration")


if __name__=="__main__":
    main()
