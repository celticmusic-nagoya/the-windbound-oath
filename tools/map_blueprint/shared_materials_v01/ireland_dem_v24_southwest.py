"""Anonymous public Copernicus GLO-30 COG intake, reference-only. No game placement."""
import sys,json,hashlib,urllib.request,urllib.parse,math
from pathlib import Path
from osgeo import gdal,ogr,osr
import numpy as np
gdal.UseExceptions()
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
host="copernicus-dem-30m.s3.amazonaws.com"
base="https://"+host+"/"
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def fetch(key,limit):
    p=out/Path(key).name;assert not p.exists()
    with urllib.request.urlopen(base+key,timeout=60) as r:
        u=urllib.parse.urlsplit(r.url)
        assert u.scheme=="https" and u.hostname==host and r.status==200
        n=int(r.headers.get("Content-Length","0"));assert 0<n<=limit,(key,n)
        with p.open("xb") as f:
            k=0
            while True:
                b=r.read(1048576)
                if not b:break
                k+=len(b);assert k<=limit
                f.write(b)
        assert k==n
        return p,dict(url=r.url,bytes=k,sha256=sha(p),etag=r.headers.get("ETag"),last_modified=r.headers.get("Last-Modified"))
license_url="https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/copernicus_contributing_mission_data_access_v2_cop_dem_licenses.pdf"
(out/"SOURCE_NOTICE.txt").write_text("Copernicus DEM GLO-30 Public, 2021 release, AWS open data; "+license_url+"\n© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.\nproduced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.\nThe organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.\nReference-only; no endorsement, no fictional world scale or game adoption.\n")
lst,meta=fetch("tileList.txt",4*1024*1024)
keys=set(lst.read_text().split())
results=[]
# Bounding boxes selected as representative Irish terrain studies, not a proposed mapping to TWO coordinates.
for label,lat,bounds in [("southwest_woodland",51,(-9.65,51.90,-9.40,51.99))]:
    tile=f"Copernicus_DSM_COG_10_N{lat}_00_W010_00_DEM"
    assert tile in keys or any(tile==Path(k).stem or tile in k for k in keys),(tile,"not listed")
    p,m=fetch(tile+"/"+tile+".tif",64*1024*1024)
    ds=gdal.Open(str(p));assert ds and ds.RasterCount==1
    assert (ds.RasterXSize,ds.RasterYSize)==(2400,3600)
    crs=ds.GetSpatialRef();assert crs and crs.IsGeographic()
    gt=ds.GetGeoTransform();assert gt[1]>0 and gt[5]<0 and gt[2]==gt[4]==0
    assert abs(gt[1]-1/2400)<1e-9 and abs(gt[5]+1/3600)<1e-9
    west,south,east,north=bounds
    assert gt[0]<=west and gt[0]+gt[1]*ds.RasterXSize>=east and gt[3]>=north and gt[3]+gt[5]*ds.RasterYSize<=south
    a=ds.ReadAsArray();nd=ds.GetRasterBand(1).GetNoDataValue()
    valid=np.isfinite(a)
    if nd is not None:valid &= a!=nd
    assert valid.any()
    # Metric reprojected crop. Height datum from provider specification, not silently transformed.
    crop=out/(label+"_utm29_30m.tif")
    w=gdal.Warp(str(crop),ds,format="GTiff",dstSRS="EPSG:32629",outputBounds=bounds,outputBoundsSRS="EPSG:4326",xRes=30,yRes=30,resampleAlg="bilinear",dstNodata=-9999,creationOptions=["COMPRESS=DEFLATE"])
    w.FlushCache();w=None
    c=gdal.Open(str(crop));z=c.ReadAsArray();good=np.isfinite(z)&(z!=-9999);assert good.any()
    assert c.GetSpatialRef().GetAuthorityCode(None)=="32629"
    hill=out/(label+"_hillshade.png")
    hs=gdal.DEMProcessing("",c,"hillshade",format="MEM",computeEdges=True,azimuth=315,altitude=40)
    gdal.Translate(str(hill),hs,format="PNG");hs=None
    # Contours in projected metres, no fictional placement.
    cn=out/(label+"_contours_20m.geojson")
    driver=ogr.GetDriverByName("GeoJSON");v=driver.CreateDataSource(str(cn));layer=v.CreateLayer("contours",srs=c.GetSpatialRef(),geom_type=ogr.wkbLineString)
    layer.CreateField(ogr.FieldDefn("id",ogr.OFTInteger));layer.CreateField(ogr.FieldDefn("elev_m",ogr.OFTReal))
    gdal.ContourGenerate(c.GetRasterBand(1),20,0,[],1,-9999,layer,0,1)
    layer.SyncToDisk();layer=None;v=None
    # GeoJSON feature count is read only after writer closure, not from live writer.
    reopened=json.loads(cn.read_text());features=reopened["features"];count=len(features)
    assert count>0 and all(f["geometry"]["type"]=="LineString" and len(f["geometry"]["coordinates"])>=2 and abs(f["properties"]["elev_m"]/20-round(f["properties"]["elev_m"]/20))<1e-9 for f in features)
    print("contours readback",count)
    gy,gx=np.gradient(z.astype(float),30,30);mask=good.copy();mask[1:-1,1:-1]&=good[:-2,1:-1]&good[2:,1:-1]&good[1:-1,:-2]&good[1:-1,2:];mask[[0,-1],:]=False;mask[:,[0,-1]]=False
    slope=np.degrees(np.arctan(np.hypot(gx[mask],gy[mask])))
    m.update(tile=tile,crs_wkt=crs.ExportToWkt(),transform=gt,shape=[ds.RasterYSize,ds.RasterXSize],valid_count=int(valid.sum()),nodata=nd,source_range_m=[float(a[valid].min()),float(a[valid].max())],vertical_reference="provider EGM2008; separate per-file vertical CRS verification not asserted",crop_bounds_lonlat=bounds,crop_crs="EPSG:32629",crop_transform=c.GetGeoTransform(),crop_shape=list(z.shape),crop_valid_count=int(good.sum()),crop_range_m=[float(z[good].min()),float(z[good].max())],slope_degrees_p50_p95=[float(x) for x in np.percentile(slope,[50,95])],contour_count=count,derived_sha256={q.name:sha(q) for q in [crop,hill,cn]})
    results.append(m);(out/"qa.json").write_text(json.dumps(dict(status="SOUTHWEST_REFERENCE_RASTER_INTAKE_PASS",tile_list=meta,tiles=results,limits=["DSM not bare earth; reprojected 30m raster, no surveyed cliff geometry; no fictional world scale or transform; no G1-D4 approval"],gdal=gdal.VersionInfo()),indent=2)+"\n")
print("TWO_IRELAND_DEM_REFERENCE_INTAKE_PASS",len(results))
