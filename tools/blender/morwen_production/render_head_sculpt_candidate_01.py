"""Non-destructive first sculpt candidate. NOT an approved Morwen head.
Uses complete VRoid Face+Body and bounded, smooth, local-space edits.
Source VRM remains unchanged. Candidate only; art gate stays BLOCKED.
"""
import hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector
from render_head_diagnostics import Scene, clay_mat, VIEWS, OUT, SRC

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def smoothstep(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3-2*t)

def deform(obj):
    """Gentle jaw taper and lower cheek refinement; no eye plate distortion."""
    mesh=obj.data
    edits=0
    for v in mesh.vertices:
        x,y,z=v.co
        # Only lower facial skin, leave upper eye/forehead and neck unchanged.
        zmask=smoothstep(1.345,1.375,z)*(1-smoothstep(1.405,1.435,z))
        # central mouth is preserved; outer cheeks/jaw narrowed subtly
        side=smoothstep(.025,.075,abs(x))
        weight=zmask*side
        if weight>0:
            v.co.x=x*(1-0.045*weight)
            edits+=1
    mesh.update()
    return edits

def main():
    before=digest(SRC)
    scene=Scene()
    face=next(o for o in scene.meshes if o.name=="Face")
    body=next(o for o in scene.meshes if o.name=="Body")
    changes={"Face":deform(face),"Body":deform(body)}
    # Render only neutral clay with the same fixed orthographic camera as HEAD_STRUCTURE-01.
    scene.run_uniform("sculpt_candidate_01_clay",clay_mat(), "clay")
    assert before==digest(SRC),"Pinned source changed"
    result={
      "task":"MORWEN-HEAD-SCULPT-01",
      "status":"EXPERIMENTAL_UNAPPROVED",
      "source_sha256":before,
      "source_modified":False,
      "method":"local bounded jaw/cheek taper; 4.5 percent maximum x compression, smoothstep weights",
      "changed_vertices":changes,
      "camera_ortho_scale_m":0.4,
      "views":list(VIEWS),
      "G1":"SOURCE_PROTECTED",
      "G2":"NOT_RUN_INDEPENDENT_ART_REVIEW",
      "G3":"RENDER_OUTPUT_PENDING_VALIDATION",
      "G4":"NOT_RUN",
      "limitations":["Not landmark-calibrated","No canonical likeness assertion","Hair/hat/glasses not built","Do not adopt as final"]
    }
    dst=OUT/"SCULPT_CANDIDATE_01.json"
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
