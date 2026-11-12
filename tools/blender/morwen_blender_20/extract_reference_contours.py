"""Extract alpha silhouettes from locked reference PNGs without changing source images.

This produces a garment-inclusive silhouette, NOT an inferred nude anatomy contour.
Only outer alpha edges are used. Transparent holes and costume appendages remain visible.
"""
import hashlib, json, struct, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REF=ROOT/"assets/references/morwen/reference_20261112"
OUT=ROOT/"assets/candidates/morwen-blender-20"
EXPECTED={
"front":"b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed",
"profile_facing_left":"69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa",
"profile_facing_right":"9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737",
"back":"b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"}

def rgba_png_alpha(data):
    assert data[:8]==bytes([137,80,78,71,13,10,26,10])
    pos=8; chunks=[];width=height=depth=color=interlace=None
    while pos<len(data):
        length=struct.unpack(">I",data[pos:pos+4])[0]
        typ=data[pos+4:pos+8];payload=data[pos+8:pos+8+length]
        assert zlib.crc32(typ+payload)&0xffffffff==struct.unpack(">I",data[pos+8+length:pos+12+length])[0]
        pos+=12+length
        if typ==b"IHDR":
            width,height,depth,color,comp,fil,interlace=struct.unpack(">IIBBBBB",payload)
        elif typ==b"IDAT":chunks.append(payload)
        elif typ==b"IEND":break
    assert (width,height,depth,color,interlace)==(384,1024,8,6,0),"Expected RGBA8 noninterlaced 384x1024"
    raw=zlib.decompress(b"".join(chunks)); stride=width*4
    rows=[];prior=bytearray(stride);i=0
    for y in range(height):
        mode=raw[i];i+=1;scan=bytearray(raw[i:i+stride]);i+=stride
        for x in range(stride):
            a=scan[x-4] if x>=4 else 0
            b=prior[x];c=prior[x-4] if x>=4 else 0
            if mode==1: scan[x]=(scan[x]+a)&255
            elif mode==2:scan[x]=(scan[x]+b)&255
            elif mode==3:scan[x]=(scan[x]+((a+b)//2))&255
            elif mode==4:
                p=a+b-c;da=abs(p-a);db=abs(p-b);dc=abs(p-c)
                pred=a if da<=db and da<=dc else b if db<=dc else c
                scan[x]=(scan[x]+pred)&255
            elif mode!=0:raise ValueError("Unsupported PNG filter")
        rows.append(scan[3::4]);prior=scan
    assert i==len(raw)
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"task":"MORWEN-BLENDER-20","threshold":128,
      "source":"canonical RGBA alpha; includes clothing/hair/accessories",
      "anatomical_target":False,"art_approval":"NOT_RUN","views":{}}
    for name,sha in EXPECTED.items():
        p=REF/("REFERENCE_"+name+".png")
        data=p.read_bytes()
        assert hashlib.sha256(data).hexdigest()==sha,"canonical SHA mismatch: "+name
        alpha=rgba_png_alpha(data)
        scan=[]
        for y,row in enumerate(alpha):
            occupied=[x for x,a in enumerate(row) if a>=128]
            if occupied:
                scan.append({"y":y,"left":occupied[0],"right":occupied[-1],"width":occupied[-1]-occupied[0]+1})
        assert len(scan)>200,"unexpectedly empty silhouette"
        report["views"][name]={"sha256":sha,"rows":scan,
           "bbox":[min(x["left"] for x in scan),scan[0]["y"],max(x["right"] for x in scan),scan[-1]["y"]]}
    (OUT/"canonical_alpha_contours.json").write_text(json.dumps(report,separators=(",",":"))+"\n")
    print("MORWEN_20_CANONICAL_ALPHA_CONTOURS_PASS")
if __name__=="__main__":main()
