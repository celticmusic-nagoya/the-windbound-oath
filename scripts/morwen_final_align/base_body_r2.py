import json, math
F="assets/candidates/morwen/real-canon-final-04/fix03/"
s=json.load(open(F+"BASE_BODY_SPEC.json")); Lm=s["landmarks"]
def setp(v,k,xy,c=None,note=None):
    Lm[v][k]["xy"]=list(xy)
    if c: Lm[v][k]["confidence"]=c
    if note: Lm[v][k]["note"]=note
setp("front","crown_skull",(600,184),"low","range 180-188 (under the hat)")
setp("front","shoulder_R",(487,430),"medium","joint ~20-25 px below the shoulder surface (convention)")
setp("front","shoulder_L",(713,430),"medium","same convention")
for k in ("elbow_R","elbow_L"): Lm["front"][k]["confidence"]="low"; Lm["front"][k]["note"]="under the capelet"
setp("front","hip_R",(545,770),"low"); setp("front","hip_L",(655,770),"low")
setp("right","wrist_near",(600,798),"high","R1 correction: previous value was on the belt chain")
setp("right","elbow_near",(595,615),"medium"); setp("right","knee_near",(593,1100),"medium","joint centre, not shin contour")
setp("right","ankle_near",(573,1465),"medium"); setp("right","shoulder_near",(610,428),"medium","joint convention; surface ~400-405")
setp("left","knee_near",(610,1100),"medium"); setp("left","ankle_near",(630,1465),"medium"); setp("left","elbow_near",(615,625),"medium")
setp("left","wrist_near",(605,820),"high"); setp("left","shoulder_near",(600,436),"medium","left view drawn ~8 px lower than front (chin 330 vs 322)")
setp("back","neck_base",(600,410),"low","anatomical estimate; the collar/hair-end contour is at ~445")
Lm["back"]["collar_contour"]={"xy":[600,445],"confidence":"medium","note":"garment contour, not anatomy"}
setp("back","hip_L",(545,770),"low","hidden; copied from front, not verifiable"); setp("back","hip_R",(655,770),"low","hidden; copied from front, not verifiable")
for v in ("right","left"): Lm[v]["hip_near"]["note"]="hidden; estimated, not verifiable"
T=s["target_base_body_from_front"]
T["rows"].update({"crown_skull":184,"shoulder":430})
T.update({"crown_range":[180,188],"shoulder_row_tolerance":8,"shoulder_joint_convention":"joint centre ~20-25 px below the shoulder surface; front surface ~400-405",
 "shoulder_width_joint_to_joint":226,"hip_width":110,"upper_arm":round(math.dist((487,430),(410,605)),1),"forearm":round(math.dist((410,605),(398,795)),1),
 "arm_total":round(math.dist((487,430),(410,605))+math.dist((410,605),(398,795)),1),
 "head_height_estimate":"chin 322 - crown 180..188 = 134..142 px; ~9.6 heads including ~50 px boot heel (stylised, approved art)",
 "head_hair_width":{"front_bob":243,"back_bob":280,"note":"back ~15% wider (UNSURE, ribbon hides the right edge) - director decision"}})
T["back_targets"]={"shoulders":[[487,430],[713,430]],"wrists_current":[[345,795],[855,795]],"wrists_target":[[356,786],[844,786]],
 "reason":"front arm length ~381 px; target shoulder to current wrist ~392 px (unreachable). Moving cuffs+hands ~11 px inward and ~9 px up (move-only layer) gives ~379 px with a slight elbow bend.",
 "neck_base":395,"hair_tip":[370,380],"capelet_top":384,"capelet_tier1_bottom":540,"hat_crown_top":[34,35]}
s["side_shoulder_offset"]="reading error, not perspective: the shoulder surface sits at y~395-405 in front/right/left; left view additionally drawn ~8 px lower"
s["legs_consistency"]="rows (knee 1100, ankle 1465-1470, contact 1540) agree within ~5 px; side-view x positions differ 25-37 px (side stance, pose not anatomy)"
def row(view,key):
    for k,v in Lm[view].items():
        if k==key or k.startswith(key+"_"): return v["xy"][1]
keys={"neck_base":"neck_base","shoulder":"shoulder","elbow":"elbow","wrist":"wrist","waist":"waist","hip":"hip","knee":"knee","ankle":"ankle"}
s["row_delta_vs_target"]={k:{d:(row(d,k)-T["rows"][k] if row(d,k) is not None else None) for d in Lm} for k in keys}
limbs={}
for d,ks in {"front":("shoulder_R","elbow_R","wrist_R","hip_R","knee_R","ankle_R"),"back":("shoulder_L","elbow_L","wrist_L","hip_L","knee_L","ankle_L"),
   "right":("shoulder_near","elbow_near","wrist_near","hip_near","knee_near","ankle_near"),"left":("shoulder_near","elbow_near","wrist_near","hip_near","knee_near","ankle_near")}.items():
    p=[Lm[d][k]["xy"] for k in ks]
    limbs[d]={"upper_arm":round(math.dist(p[0],p[1]),1),"forearm":round(math.dist(p[1],p[2]),1),"shoulder_to_wrist":round(math.dist(p[0],p[2]),1),"thigh":round(math.dist(p[3],p[4]),1),"shank":round(math.dist(p[4],p[5]),1)}
s["limb_lengths"]=limbs; s["revision"]="R2 (independent QA R1 corrections 1-6 applied)"; s["status"]="CANDIDATE R2 - pending independent re-QA and director freeze"
json.dump(s,open(F+"BASE_BODY_SPEC.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(s["row_delta_vs_target"])); print(json.dumps(limbs))
