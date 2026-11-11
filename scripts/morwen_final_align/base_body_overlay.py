"""Draw the BASE_BODY_SPEC joint chains (neutral construction lines) over the 4 views and as a skeleton-only cross view."""
import json
from PIL import Image, ImageDraw
F = "assets/candidates/morwen/real-canon-final-04/fix03/"
s = json.load(open(F + "BASE_BODY_SPEC.json")); T = s["target_base_body_from_front"]["rows"]
EDGES = [("neck_base","shoulder_R"),("neck_base","shoulder_L"),("shoulder_R","elbow_R"),("elbow_R","wrist_R"),("shoulder_L","elbow_L"),("elbow_L","wrist_L"),
         ("neck_base","waist"),("waist","hip_R"),("waist","hip_L"),("hip_R","knee_R"),("knee_R","ankle_R"),("ankle_R","contact_R"),("hip_L","knee_L"),("knee_L","ankle_L"),("ankle_L","contact_L"),
         ("chin","neck_base"),("neck_base","shoulder_near"),("shoulder_near","elbow_near"),("elbow_near","wrist_near"),("waist","hip_near"),("hip_near","knee_near"),("knee_near","ankle_near"),
         ("ankle_near","contact_heel"),("ankle_near","contact_forefoot"),("crown_skull","chin")]
CC = {"high": (0,170,0), "medium": (255,150,0), "low": (230,0,0)}
def draw(dr, lm, ox=0, sc=1.0, w=3):
    P = {k: (v["xy"][0]*sc+ox, v["xy"][1]*sc) for k, v in lm.items() if k != "collar_contour"}
    for a, b in EDGES:
        if a in P and b in P: dr.line([P[a], P[b]], fill=(0,90,255), width=w)
    for k, (x, y) in P.items():
        r = 6*sc+2; dr.ellipse([x-r, y-r, x+r, y+r], outline=CC[lm[k]["confidence"]], width=2)
th = 0.4
sheet = Image.new("RGB", (int(4*1200*th), int(1600*th)+40), (255,255,255)); d = ImageDraw.Draw(sheet)
for i, v in enumerate(("front","right","back","left")):
    im = Image.open(s["sources"][v]["path"]); bg = Image.new("RGBA", im.size, (255,255,255,255)); bg.alpha_composite(im)
    fade = Image.blend(bg.convert("RGB"), Image.new("RGB", im.size, (255,255,255)), 0.45); dr = ImageDraw.Draw(fade)
    for k, y in T.items(): dr.line([(0,y),(1200,y)], fill=(200,200,200))
    draw(dr, s["landmarks"][v], w=4)
    sheet.paste(fade.resize((int(1200*th), int(1600*th)), Image.LANCZOS), (int(i*1200*th), 20)); d.text((int(i*1200*th)+6, 4), v.upper(), fill=(0,0,0))
d.text((6, int(1600*th)+24), "R2. blue = joint chain; circles green/orange/red = high/medium/low confidence; grey rows = front target (neck 395, shoulder 430, elbow 605, wrist 795, hip 770, knee 1100, ankle 1470, sole 1540)", fill=(0,0,0))
sheet.save(F + "BASE_BODY_OVERLAY_4DIR.png", optimize=True)
cv = Image.new("RGB", (1200, 420), (255,255,255)); d = ImageDraw.Draw(cv)
for k, y in T.items():
    d.line([(0, y*0.25), (1200, y*0.25)], fill=(220,220,220)); d.text((2, y*0.25-10), f"{k} {y}", fill=(150,150,150))
for i, v in enumerate(("front","right","back","left")):
    draw(d, s["landmarks"][v], ox=i*300, sc=0.25, w=2); d.text((i*300+120, 404), v, fill=(0,0,0))
cv.save(F + "BASE_BODY_CROSS_VIEW.png", optimize=True)
