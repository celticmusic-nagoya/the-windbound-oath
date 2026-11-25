"""Bounded EPA WFS reference-only acquisition. No fictional river geometry overwrite."""
import sys,json,hashlib,urllib.parse,urllib.request,math
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
base="https://gis.epa.ie/geoserver/EPA/ows"
regions={"inagh_clare":(-9.45,52.85,-9.23,53.03),"caragh_kerry":(-9.90,51.95,-9.70,52.12)}
notice={"publisher":"Environmental Protection Agency Ireland","dataset":"River Network Routes","catalog":"https://data.gov.ie/dataset/river-network-routes","resource":"https://data.gov.ie/dataset/river-network-routes/resource/840f8205-2aea-4e81-8eb2-f962c85026cd","license":"CC BY 4.0 https://creativecommons.org/licenses/by/4.0/","changes":"Reference sample and calculated metrics; no geometry copied to fictional design."}
(out/"attribution.json").write_text(json.dumps(notice,indent=2)+"\n")
def dist(a,b):
    y1,y2=map(math.radians,(a[1],b[1]));dx=math.radians(b[0]-a[0]);dy=y2-y1
    t=math.sin(dy/2)**2+math.cos(y1)*math.cos(y2)*math.sin(dx/2)**2
    return 6371008.8*2*math.asin(math.sqrt(min(1,max(0,t))))
report={}
for name,bbox in regions.items():
    params={"service":"WFS","version":"1.0.0","request":"GetFeature","typeName":"EPA:WATER_RIVNETROUTES","maxFeatures":"200","outputFormat":"application/json","srsName":"EPSG:4326","bbox":",".join(map(str,bbox))+",EPSG:4326"}
    url=base+"?"+urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url,timeout=60) as res:
            u=urllib.parse.urlsplit(res.url);assert u.scheme=="https" and u.hostname=="gis.epa.ie" and res.status==200
            raw=res.read(16*1024*1024+1);assert 0<len(raw)<=16*1024*1024
        path=out/(name+".geojson");path.write_bytes(raw)
        d=json.loads(raw);assert d["type"]=="FeatureCollection"
        fs=d["features"];assert 0<len(fs)<=200
        crs=d.get("crs",{}).get("properties",{}).get("name")
        assert crs is None or "4326" in crs or "CRS84" in crs
        lines=[];names=set()
        for f in fs:
            g=f.get("geometry");assert g and g["type"] in ("LineString","MultiLineString")
            for k,v in f.get("properties",{}).items():
                if "name" in k.lower() and isinstance(v,str) and v.strip():names.add(v)
            for a in ([g["coordinates"]] if g["type"]=="LineString" else g["coordinates"]):
                assert len(a)>=2 and all(-11<=p[0]<=-5 and 51<=p[1]<=56 for p in a)
                length=sum(dist(p,q) for p,q in zip(a,a[1:]));chord=dist(a[0],a[-1])
                if chord>1:lines.append({"length_m":length,"chord_m":chord,"sinuosity":length/chord})
        assert lines
        report[name]={"status":"PASS_SAMPLE","url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"features":len(fs),"possibly_truncated":len(fs)==200,"crs":crs,"names":sorted(names),"component_lines":len(lines),"sinuosity_median":sorted(x["sinuosity"] for x in lines)[len(lines)//2],"metrics":lines,"limits":"Whole returned components, not clipped to bbox; source may be truncated, not catchment completeness. No flow direction inferred from line vertex order."}
    except Exception as e:
        report[name]={"status":"BLOCKED","url":url,"error":str(e)[:500]}
    (out/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
assert all(r["status"]=="PASS_SAMPLE" for r in report.values()),report
