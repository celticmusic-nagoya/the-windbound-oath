#!/usr/bin/env python3
"""Extract diagnostic silhouette pixels from actual Blender RGBA renders.

No anatomical landmark inference. Uses stdlib PNG decoder for 8-bit RGBA images.
"""
import argparse,hashlib,json,pathlib,struct,zlib

def rgba_alpha(p):
    data=p.read_bytes()
    if data[:8]!=b"\x89PNG\r\n\x1a\n":raise ValueError("not PNG")
    off=8;payload=bytearray();w=h=None
    while off<len(data):
        length=struct.unpack_from(">I",data,off)[0];tag=data[off+4:off+8];chunk=data[off+8:off+8+length];off+=12+length
        if tag==b"IHDR":
            w,h,depth,color,_,_,interlace=struct.unpack(">IIBBBBB",chunk)
            if depth!=8 or color!=6 or interlace!=0:raise ValueError("requires noninterlaced 8bit RGBA")
        elif tag==b"IDAT":payload.extend(chunk)
        elif tag==b"IEND":break
    raw=zlib.decompress(payload);stride=w*4;previous=bytearray(stride);alpha=[]
    i=0
    for _ in range(h):
        filt=raw[i];i+=1;row=bytearray(raw[i:i+stride]);i+=stride
        for j in range(stride):
            left=row[j-4] if j>=4 else 0
            up=previous[j];upperleft=previous[j-4] if j>=4 else 0
            if filt==1:row[j]=(row[j]+left)&255
            elif filt==2:row[j]=(row[j]+up)&255
            elif filt==3:row[j]=(row[j]+((left+up)//2))&255
            elif filt==4:
                q=left+up-upperleft;da=abs(q-left);db=abs(q-up);dc=abs(q-upperleft)
                row[j]=(row[j]+(left if da<=db and da<=dc else up if db<=dc else upperleft))&255
            elif filt!=0:raise ValueError("invalid PNG filter")
        alpha.append([row[x*4+3] for x in range(w)])
        previous=row
    return w,h,alpha

def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();manifest=pathlib.Path(a.manifest).resolve();out=pathlib.Path(a.output).resolve()
    doc=json.loads(manifest.read_text())
    result={"status":"PASS_RENDER_CONTOUR_CANDIDATES_ONLY","source_manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "anatomical_qa":"BLOCKED","reviewer_confirmed":False,"views":[]}
    for entry in doc["views"]:
        image=manifest.parent/entry["file"]
        if hashlib.sha256(image.read_bytes()).hexdigest()!=entry["sha256"]:raise SystemExit("FAIL render hash mismatch")
        w,h,alpha=rgba_alpha(image)
        samples=[]
        for y in range(72,257,8):
            opaque=[x for x in range(w) if alpha[y][x]>=128]
            if not opaque:continue
            left,right=opaque[0],opaque[-1]
            # Offset 2px inward from the silhouette to reduce antialiasing misses.
            for label,x in (("left_inset",min(left+2,right)),("mid",round((left+right)/2)),("right_inset",max(right-2,left))):
                samples.append({"label":label,"pixel":[x,y],"alpha":alpha[y][x]})
        result["views"].append({"object":entry["object"],"view":entry["view"],"image_sha256":entry["sha256"],
                                "resolution":[w,h],"samples":samples})
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"views":len(result["views"]),"samples":sum(len(v["samples"]) for v in result["views"])}))
if __name__=="__main__":main()
