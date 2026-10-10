#!/usr/bin/env python3
"""AREA 2 detail pass: skeleton (routes + stream, k=2.5) -> full design JSON.
All features are anchored to the skeleton's routes/stream in world coordinates (the skeleton's cluster-translated
landmarks drifted up to ~320 px off the route, so they are re-placed here).
usage: build_a2.py <skeleton.json> <a1_runtime.json> <out_design.json>   (prints validation report)"""
import json,sys,os,math,copy
sys.path.insert(0,os.path.dirname(__file__))
import mf_lib as L
K=2.5
def S(x,y): return [round(x*K,1),round(y*K,1)]
def sub(rects,cut):
    out=[]; cx,cy,cw,ch=cut
    for r in rects:
        x,y,w,h=r
        if x>=cx+cw or x+w<=cx or y>=cy+ch or y+h<=cy: out.append(r); continue
        if x<cx: out.append([x,y,cx-x,h])
        if x+w>cx+cw: out.append([cx+cw,y,x+w-(cx+cw),h])
        ty=max(y,cy); by=min(y+h,cy+ch)
        if y<cy: out.append([max(x,cx) if False else x,y,w,cy-y]) if False else None
        # vertical remainder only over the cut's x-range
        ox0=max(x,cx); ox1=min(x+w,cx+cw)
        if y<cy: out.append([ox0,y,ox1-ox0,cy-y])
        if y+h>cy+ch: out.append([ox0,cy+ch,ox1-ox0,y+h-(cy+ch)])
    return [[round(v,1) for v in r] for r in out if r[2]>=2 and r[3]>=2]
def build(sk,a1):
    m=copy.deepcopy(sk); m.pop('_skeletonOnly',None); W,H=m['world']['width'],m['world']['height']
    P={p['id']:p['points'] for p in m['terrain']['paths']}
    mainr=P['path_main']
    # ---- cliffs (collision bands + visual segments) ------------------------------------------------
    NY0,NH=3300,190                 # north wall: face visible; lip y=3300
    SY0,SH=4980,260                 # south wall: lip/face band
    N_STEPS=(1885,2065)             # root steps gap (route x=1975)
    S_RAMP=(7340,7690)              # root ramp gap (route crosses 7424..7570)
    FALL=(1070,1230)                # waterfall cut: blocked (falling water), not a gap
    north=[[0,NY0,N_STEPS[0],NH],[N_STEPS[1],NY0,W-N_STEPS[1],NH]]
    south=[[0,SY0,S_RAMP[0],SH],[S_RAMP[1],SY0,W-S_RAMP[1],SH]]
    m['terrain']['cliffs']=[
      {'id':'cliff_north','type':'face_visible','segments':north,'faceHeight':NH,'wobble':36,'seed':201,
       'gaps':[{'x0':N_STEPS[0],'x1':N_STEPS[1],'fill':'path_root_steps_E'},{'x0':FALL[0],'x1':FALL[1],'fill':'water_waterfall_01','blocked':True}]},
      {'id':'cliff_south','type':'lip_only','segments':south,'band':[SY0,SY0+SH],'wobble':30,'seed':202,
       'gaps':[{'x0':S_RAMP[0],'x1':S_RAMP[1],'fill':'path_root_ramp_W'}]}]
    # ---- water: stream (skeleton), pool + waterfall -----------------------------------------------------
    POOL=(1150,3790)
    pool_poly=[[round(POOL[0]+170*math.cos(t*math.pi/6),1),round(POOL[1]+110*math.sin(t*math.pi/6),1)] for t in range(12)]
    core_poly=[[round(POOL[0]+125*math.cos(t*math.pi/6),1),round(POOL[1]+70*math.sin(t*math.pi/6),1)] for t in range(12)]
    m['terrain']['waters']=[w for w in m['terrain']['waters'] if w['id']=='stream_a2']
    m['terrain']['waters'][0].update(depth='shallow',surface='shallow_water',flow={'dx':1,'dy':0.1,'speed':0.5})
    m['terrain']['waters']+= [{'id':'pool_a2','kind':'pool','depth':'shallow','surface':'shallow_water','polygon':pool_poly,'core':{'depth':'deep','polygon':core_poly}},
                              {'id':'fall_a2','kind':'fall','depth':'deep','polygon':[[FALL[0],NY0],[FALL[1],NY0],[FALL[1],NY0+NH],[FALL[0],NY0+NH]]}]
    # deep stream head: pool -> x=1700 along stream_a2's first leg (width 110)
    (x0,y0),(x1,y1)=m['terrain']['waters'][0]['points'][:2]
    sl=(y1-y0)/(x1-x0); X1=1700; Y1=y0+sl*(X1-x0); hw=55
    head_quad=[[x0,y0-hw],[X1,Y1-hw],[X1,Y1+hw],[x0,y0+hw]]; head_top=round(Y1-hw)
    # log channel through the pool's deep core, centred on the alcove route
    ax=[p for p in P['path_opt_alcove']]; chan_x=1193
    # the whole pool is deep (no wading round the rim); the log channel is the only way across.
    deep=L.ellipse_rects(POOL[0],POOL[1],170,110,step=12,shrink=1.0)
    channel=[chan_x-36,POOL[1]-115,72,230]
    deep=sub(deep,channel)
    m['collision']['carves']=[{'id':'carve_bridge','shape':'rect','x':3727,'y':3962,'w':96,'h':200,'note':'bridge deck: walkable over the stream'},
                              {'id':'carve_log','shape':'rect','x':channel[0],'y':channel[1],'w':channel[2],'h':channel[3],'note':'fallen log across the pool'}]
    m['collision']['blockers']=[
      {'id':'cb_cliff_north','tag':'cliff','shape':'rects','rects':north},
      {'id':'cb_cliff_south','tag':'cliff','shape':'rects','rects':south},
      {'id':'cb_waterfall','tag':'water_deep','shape':'rects','rects':[[FALL[0],NY0,FALL[1]-FALL[0],NH]]},
      {'id':'cb_pool_deep','tag':'water_deep','shape':'rects','rects':deep},
      # seals the waterfall ledge pocket: stream head is deep, rocks close the north bank east of the pocket, a root wall closes the west.
      {'id':'cb_stream_head_deep','tag':'water_deep','shape':'rects','rects':sub(L.poly_rects(head_quad),channel)},
      {'id':'cb_pocket_rocks_e','tag':'rock','shape':'rects','rects':[[1560,NY0+NH,80,head_top-(NY0+NH)+8]]},
      {'id':'cb_pocket_roots_w','tag':'rock','shape':'rects','rects':[[940,NY0+NH,70,3770-(NY0+NH)]]}]
    m['collision']['softZones']=[{'id':'sz_stream','ref':'stream_a2','speedMul':0.85,'footstep':'shallow_water','fx':'fx_water_splash'},
                                 {'id':'sz_pool_rim','ref':'pool_a2','speedMul':0.8,'footstep':'shallow_water','fx':'fx_water_splash'},
                                 {'id':'sz_root_steps','shape':'rect','x':N_STEPS[0],'y':NY0,'w':N_STEPS[1]-N_STEPS[0],'h':NH,'speedMul':0.85,'footstep':'root'},
                                 {'id':'sz_root_ramp','shape':'rect','x':S_RAMP[0],'y':SY0,'w':S_RAMP[1]-S_RAMP[0],'h':SH,'speedMul':0.85,'footstep':'root'}]
    # ---- patches -------------------------------------------------------------------------------------
    def blob(cx,cy,rx,ry,n=12,seed=0):
        return [[round(cx+rx*(1+.12*math.sin(i*2.3+seed))*math.cos(2*math.pi*i/n),1),round(cy+ry*(1+.12*math.cos(i*1.7+seed))*math.sin(2*math.pi*i/n),1)] for i in range(n)]
    fernend=P['path_opt_fern'][-1]; marker=S(1190,600)
    m['terrain']['base']={'tiles':['gnd_moss_01','gnd_moss_02','gnd_moss_03'],'surface':'moss','seed':2201}
    m['terrain']['baseColor']='#5a8a4a'
    m['terrain']['patches']=[
      {'id':'patch_valley_floor','texture':'gnd_moss_wet','tint':'#8fc2a0','surface':'moss','feather':60,'polygon':[[0,NY0+NH],[W,NY0+NH],[W,SY0],[0,SY0]]},
      {'id':'patch_fern_hollow','texture':'gnd_moss_dark','tint':'#2f5a46','surface':'moss','feather':50,'polygon':blob(fernend[0]-120,fernend[1],420,200,seed=1)},
      {'id':'patch_marker_clearing','texture':'gnd_grass_sunny','tint':'#e6e3b0','surface':'grass','feather':50,'polygon':blob(marker[0],marker[1]-20,320,220,seed=2)},
      {'id':'patch_north_plateau','texture':'gnd_grass_sunny','tint':'#dfe9b8','surface':'grass','feather':80,'polygon':[[0,60],[W,60],[W,NY0],[0,NY0]]}]
    m['terrain']['openAreas']=[{'id':'open_bridge','shape':'rect','x':3600,'y':3920,'w':350,'h':300},{'id':'open_marker','shape':'rect','x':marker[0]-260,'y':marker[1]-200,'w':520,'h':400},
                               {'id':'open_arch','shape':'rect','x':6000,'y':4380,'w':400,'h':260},{'id':'open_ledge','shape':'rect','x':4850,'y':5650,'w':380,'h':280}]
    # ---- props / landmarks (world coords) ----------------------------------------------------------
    br=(3775,4062); arch=(6200,4475); steps=(1975,3430); rim=(7600,5450); led=P['path_opt_overlook'][-1]
    props=[]; add=lambda i,a,x,y,**k: props.append(dict(id=i,asset=a,x=round(x,1),y=round(y,1),**k))
    add('lm_a2_rim_reveal','rock_moss_L_01',rim[0]-190,rim[1]+10,tags=['landmark','reveal']); add('p_rim_rock_e','rock_moss_M_01',rim[0]+200,rim[1]-20)
    add('p_rim_fence_a','prop_fence_broken_01',rim[0]-330,rim[1]-30); add('p_rim_fence_b','prop_fence_broken_01',rim[0]+330,rim[1]-40,flip=True)
    add('lm_a2_root_arch','prop_root_arch_01',arch[0],arch[1],tags=['landmark','foreground'],layerHint='FOREGROUND')
    add('lm_a2_bridge','prop_bridge_wood_01',br[0],br[1],tags=['landmark','warm'],noCollision=True,layerHint='GROUND_DETAIL')
    for i,(dx,dy) in enumerate([(-70,-96),(70,-96),(-70,96),(70,96)]): add(f'p_bridge_post_{i}','prop_bridge_post_01',br[0]+dx,br[1]+dy)
    add('lm_a2_waterfall','fx_waterfall_01',(FALL[0]+FALL[1])/2,NY0+NH,noCollision=True,tags=['landmark','water'])
    add('lm_a2_root_steps','prop_root_steps_01',steps[0],steps[1],noCollision=True,tags=['landmark'],layerHint='GROUND_DETAIL')
    add('lm_a2_old_marker','anc_stone_marker_old_01',marker[0]+70,marker[1]-60,tags=['landmark','story','taint'],interactZone='ev_a2_old_marker')
    add('p_marker_stone_b','anc_standing_L_01',marker[0]-130,marker[1]-30,scale=.8)
    add('lm_a2_overlook_ledge','rock_moss_L_02',led[0]-30,led[1]-140,flip=True,tags=['landmark','optional'])
    add('p_overlook_fence','prop_fence_broken_01',led[0]-120,led[1]+60)
    add('p_log_fallen','tree_log_fallen_H_01',chan_x,POOL[1],noCollision=True,tags=['landmark','optional'],layerHint='GROUND_DETAIL')
    add('p_ramp_rock_w','rock_moss_L_01',S_RAMP[0]-40,SY0+SH/2); add('p_ramp_rock_e','rock_moss_L_02',S_RAMP[1]+40,SY0+SH/2,flip=True)
    add('p_stairs_rock_w','rock_moss_M_01',N_STEPS[0]-30,NY0+NH/2); add('p_stairs_rock_e','rock_moss_M_02',N_STEPS[1]+30,NY0+NH/2,flip=True)
    for i,q in enumerate([(5500,3520),(5700,3800),(6050,3470),(6300,3720)]): add(f'p_fern_root_{i}','tree_mossy_M_01',q[0],q[1],tags=['canopy'])
    # nudge any prop whose collision touches a route (min clearance = route half width + footprint + 14)
    routes={k:[tuple(p) for p in v] for k,v in P.items()}
    def clear_of_routes(p):
        pr=L.preset(p['asset'])
        if not pr or p.get('noCollision'): return
        ext=max(max(abs(r[0]),abs(r[0]+r[2])) for r in pr)
        for _ in range(8):
            best=(1e9,None,None)
            for name,pl in routes.items():
                wid=next(q['width'] for q in m['terrain']['paths'] if q['id']==name)
                for i in range(len(pl)-1):
                    d,q=L.seg_proj((p['x'],p['y']),pl[i],pl[i+1])
                    need=wid/2+ext+22
                    if d<need and need-d>best[0]*-1 and d<best[0]: best=(d,q,need)
            if best[1] is None: return
            d,q,need=best; nx,ny=p['x']-q[0],p['y']-q[1]; n=math.hypot(nx,ny) or 1
            p['x']=round(q[0]+nx/n*(need+4),1); p['y']=round(q[1]+ny/n*(need+4),1)
    for p in props: clear_of_routes(p)
    m['props']=props
    # ---- effects / camera / taint / treasure / zones --------------------------------------------------
    m['effects']=[{'id':'fx_a2_fall','asset':'fx_waterfall_spray_01','x':(FALL[0]+FALL[1])/2,'y':NY0+NH,'layer':'FOREGROUND','blend':'add','alpha':.5},
                  {'id':'fx_a2_bridge_light','asset':'fx_light_shaft_01','x':br[0]-40,'y':br[1]-150,'layer':'FOREGROUND','blend':'add','alpha':.3},
                  {'id':'fx_a2_pool_mist','asset':'fx_mist_01','x':POOL[0],'y':POOL[1],'layer':'FOREGROUND','blend':'screen','alpha':.25},
                  {'id':'fx_a2_arch_shade','asset':'fx_shadow_soft_01','x':arch[0],'y':arch[1]-10,'layer':'GROUND_DETAIL','blend':'multiply','alpha':.35}]
    cf=lambda i,x,y,z=1.0,r=300,**k: dict(id=i,x=round(x,1),y=round(y,1),radius=r,zoom=z,priority=2,mode='bias',maxBiasPx=90,**k)
    m['cameraFocus']=[cf('cf_a2_rim_reveal',rim[0],rim[1],0.9,380,tags=['reveal_valley']),cf('cf_a2_root_arch',arch[0],arch[1]),cf('cf_a2_bridge',br[0],br[1]),
                      cf('cf_a2_waterfall',1150,NY0+NH+60,1.0,320),cf('cf_a2_marker',marker[0],marker[1]),cf('cf_a2_overlook',led[0],led[1],0.85,340),cf('cf_a2_alcove',1140,3540,1.0,260)]
    m['taint']={'baseLevel':1,'maxCoverageRatio':0.005,'palette':{'crack':'#120A1F','glow':'#8A4DFF'},
                'spots':[{'id':'ts_a2_marker','x':marker[0]+70,'y':marker[1]-30,'r':70,'kind':'hairline_crack'},{'id':'ts_a2_pool','x':POOL[0],'y':POOL[1]+20,'r':90,'kind':'water_shimmer'},
                         {'id':'ts_a2_ferns','x':fernend[0]-100,'y':fernend[1]-30,'r':110,'kind':'wilt'}]}
    m['treasurePoints']=[{'id':'tr_a2_overlook','x':led[0]-40,'y':led[1]-20,'tier':'common','route':'path_opt_overlook','hint':'fx_treasure_glint','contents':None},
                         {'id':'tr_a2_alcove','x':1140,'y':3545,'tier':'uncommon','route':'path_opt_alcove','hint':'fx_treasure_glint','contents':None},
                         {'id':'tr_a2_fern','x':fernend[0]-20,'y':fernend[1]-20,'tier':'common','route':'path_opt_fern','hint':'fx_treasure_glint','contents':None},
                         {'id':'tr_a2_marker_side','x':marker[0]+260,'y':marker[1]-120,'tier':'common','route':None,'hint':'fx_treasure_glint','contents':None}]
    def zone(i,cx,cy,w,h,**k): return dict(id=i,shape={'shape':'rect','x':round(cx-w/2,1),'y':round(cy-h/2,1),'w':w,'h':h},enabled=False,note='encounters not wired yet',**k)
    sb=S(2090,1660); pl=S(390,1600); fh=(fernend[0]-120,fernend[1]); rc=S(1365,375); nm=S(315,600); sw=S(2090,1925)
    m['encounterZones']=[zone('enc_a2_south_wall',sw[0],sw[1]+330,1300,150,rate='low',style='ambush',enemies=[{'id':'forest_bat','weight':100}],groupSize=[2,3],tags=['ecology:cliff_shade']),
      zone('enc_a2_stream_banks',sb[0],sb[1]+150,1500,200,rate='low',style='step',enemies=[{'id':'moss_slime','weight':100}],groupSize=[1,2]),
      zone('enc_a2_pool_shore',POOL[0]+260,POOL[1]+280,500,300,rate='low',style='step',enemies=[{'id':'moss_slime','weight':100}],groupSize=[1,2]),
      zone('enc_a2_fern_hollow',fh[0],fh[1],500,260,rate='mid',style='symbol',enemies=[{'id':'thornling','weight':100}],groupSize=[1,2]),
      zone('enc_a2_rim_camp',rc[0]+300,rc[1]+400,550,350,rate='low',style='symbol',enemies=[{'id':'goblin','weight':100}],groupSize=[2,3]),
      zone('enc_a2_north_meadow',nm[0]+700,nm[1]+300,450,600,rate='rare',style='symbol',enemies=[{'id':'wild_boar','weight':100}],groupSize=[1,1]),
      {'id':'enc_a2_taint_pool','shape':{'shape':'circle','cx':POOL[0],'cy':POOL[1],'r':120},'enabled':False,'rate':'rare','style':'step','enemies':[{'id':'tainted_moss_slime','weight':100}],'groupSize':[1,1],'maxPerVisit':1}]
    m['eventZones']=[{'id':'ev_a2_arrival','type':'locationCard','shape':{'shape':'rect','x':S(1,1)[0]+8340-200,'y':6560,'w':440,'h':260},'once':True},
                     {'id':'ev_a2_rest_ramp','type':'rest','shape':{'shape':'rect','x':7000,'y':4800,'w':240,'h':160},'noEncounter':True},
                     {'id':'ev_a2_rest_bridge','type':'rest','shape':{'shape':'rect','x':br[0]-270,'y':br[1]-90,'w':260,'h':140},'noEncounter':True},
                     {'id':'ev_a2_rest_marker','type':'rest','shape':{'shape':'rect','x':marker[0]-250,'y':marker[1]-175,'w':500,'h':350},'noEncounter':True},
                     {'id':'ev_a2_old_marker','type':'interact','shape':{'shape':'circle','cx':marker[0]+70,'cy':marker[1]-30,'r':90},'hook':'a2_marker_crack_glint'},
                     {'id':'ev_a2_ambience_marker','type':'ambienceShift','shape':{'shape':'rect','x':marker[0]-300,'y':marker[1]-250,'w':600,'h':500},'hook':'a2_marker_birds_thin'}]
    m['particles']=[{'id':'pt_spray_fall','type':'water_spray','region':{'shape':'rect','x':FALL[0]-40,'y':NY0+NH-60,'w':240,'h':200},'ratePerSec':6,'layer':'FOREGROUND'},
                    {'id':'pt_motes_bridge','type':'light_motes','region':{'shape':'rect','x':br[0]-250,'y':br[1]-300,'w':500,'h':420},'count':16,'layer':'FOREGROUND'},
                    {'id':'pt_leaf_fall','type':'leaf_fall','region':{'shape':'rect','x':0,'y':60,'w':W,'h':NY0},'ratePerSec':0.5,'layer':'FOREGROUND'}]
    # ---- scatter ---------------------------------------------------------------------------------------
    RECT=lambda y0,y1:{'shape':'rect','x':0,'y':y0,'w':W,'h':y1-y0}
    AV=['path_core','water','blockers']; AVT=['path_core:+56','open:*','water','blockers']
    sc=lambda i,pool,count,region,md,avoid,seed,**k: dict(id=i,pool=pool,count=count,region=region,minDist=md,avoid=avoid,seed=seed,**k)
    m['scatter']=[
      sc('sc_grass_plateau',['veg_grass_tuft_01','veg_grass_tuft_02','veg_grass_tuft_03','veg_grass_tuft_04'],3000,RECT(60,NY0),44,AV,31),
      sc('sc_grass_south',['veg_grass_tuft_01','veg_grass_tuft_02','veg_grass_tuft_03'],1800,RECT(SY0+SH,H-60),44,AV,32),
      sc('sc_moss_floor',['veg_moss_clump_01','veg_moss_clump_02','veg_moss_clump_03'],1100,{'shape':'patch','ref':'patch_valley_floor'},40,AV,33),
      sc('sc_ferns_valley',['veg_fern_S_01','veg_fern_S_02','veg_fern_M_01','veg_fern_M_02'],650,{'shape':'patch','ref':'patch_valley_floor'},46,AV,34),
      sc('sc_ferns_hollow',['veg_fern_M_01','veg_fern_M_02','veg_fern_L_01'],260,{'shape':'patch','ref':'patch_fern_hollow'},34,['water','blockers'],35),
      sc('sc_flowers_marker',['veg_flower_white_01','veg_flower_white_02','veg_flower_yellow_01'],90,{'shape':'patch','ref':'patch_marker_clearing'},36,AV,36),
      sc('sc_trees_north',['tree_mossy_L_01','tree_mossy_L_02','tree_oak_L_01','tree_oak_M_01','tree_oak_M_02'],300,RECT(100,NY0-40),160,AVT,37),
      sc('sc_trees_south',['tree_mossy_L_01','tree_oak_L_02','tree_oak_M_01','tree_birch_M_01'],260,RECT(SY0+SH+40,H-100),160,AVT,38),
      sc('sc_trees_valley',['tree_mossy_M_01','tree_mossy_M_02'],110,{'shape':'patch','ref':'patch_valley_floor'},200,AVT,39),
      sc('sc_shrubs',['veg_shrub_S_01','veg_shrub_S_02','veg_shrub_M_01'],420,RECT(60,H-60),100,['path_core:+24','water','blockers','open:*'],40,weights=[3,3,2]),
      sc('sc_rocks',['rock_moss_S_01','rock_moss_S_02','rock_moss_M_01','rock_moss_M_02'],260,RECT(60,H-60),130,['path_core:+24','water','blockers','open:*'],41),
      sc('sc_mushrooms',['veg_mushroom_red_01','veg_mushroom_brown_01'],160,RECT(60,H-60),100,AV,42),
      sc('sc_reeds_stream',['veg_reeds_01','veg_reeds_02'],240,{'shape':'along','ref':'stream_a2','offset':[50,120]},60,['path_core','blockers'],43),
      sc('sc_leaf_litter',['gnd_leaflitter_01','gnd_leaflitter_02'],420,RECT(60,H-60),80,['water'],44)]
    # ---- presentation blocks ---------------------------------------------------------------------------
    for k in('layers',): m[k]=a1[k]
    m['displayName']={'ja':'苔むした渓谷','en':'Mossy Ravine'}
    m['locationCard']={'regionJa':'モスの森','regionEn':'Moss Forest','areaJa':'苔むした渓谷','areaEn':'Mossy Ravine','triggerZone':'ev_a2_arrival'}
    amb=copy.deepcopy(a1['ambience']); amb['grade']={'id':'a2_damp','tint':'#BFE0C8','tintStrength':0.16,'brightness':0.96,'saturation':1.04}
    amb['shadow']={'dir':[0.5,0.85],'alpha':0.38}; amb['water']={'streamLoop':{'id':'sfx_stream_mid','refs':['stream_a2'],'maxDistance':900},'fallLoop':{'id':'sfx_waterfall','at':[1150,NY0+NH],'maxDistance':1400}}
    m['ambience']=amb
    m['audio']={'bgm':{'id':'bgm_moss_forest_a2','fadeInSec':1.5},'layers':[{'id':'amb_stream_mid','volume':0.5},{'id':'amb_wind_soft','volume':0.3},{'id':'amb_birds_day','volume':0.35}],
                'hooks':[{'zone':'ev_a2_ambience_marker','action':'fadeLayer','layer':'amb_birds_day','to':0.05,'sec':3}]}
    m['spawns']={'default':'from_area1','points':{'from_area1':{'x':sk['spawns']['points']['from_area1']['x'],'y':sk['spawns']['points']['from_area1']['y'],'facing':'up'},
                                                  'from_area3':{'x':sk['spawns']['points']['from_area3']['x'],'y':sk['spawns']['points']['from_area3']['y'],'facing':'down'}}}
    m['transitions']=[{'id':'tr_to_area1','rect':sk['transitions'][0]['rect'],'toMap':'moss_forest_01_sunlit_path','toSpawn':'from_area2','fade':{'out':.35,'in':.35},'enabled':True},
                      {'id':'tr_to_area3','rect':sk['transitions'][1]['rect'],'toMap':'moss_forest_03_ancient_grove','toSpawn':'from_area2','fade':{'out':.35,'in':.35},'enabled':True}]
    m['culling']={'chunk':256,'margin':1,'maxLiveNodes':800,'viewportWorst':[1920,1080],'scatterRender':'chunkLayer'}
    m['debug']={'mainRouteLengthPx':round(L.poly_len(mainr)),'mainRouteSecAt300':round(L.poly_len(mainr)/300,1),'speedPxPerSec':300}
    m['_routes']={k:[tuple(p) for p in v] for k,v in P.items()}
    return m
if __name__=='__main__':
    sk=json.load(open(sys.argv[1],encoding='utf-8')); a1=json.load(open(sys.argv[2],encoding='utf-8'))
    m=build(sk,a1)
    ok,rep,n=L.validate(m,'A2')
    print('A2 clear=',ok,'rects',n,'props',len(m['props']))
    for r in rep: print(' ',r)
    m.pop('_routes'); json.dump(m,open(sys.argv[3],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
