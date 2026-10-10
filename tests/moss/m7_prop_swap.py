# Cliff props (fence post / bench / standing stones): temp PNGs + manifest.json rules only -> in-game sprites swap, checker flags art/collision width mismatch.
# Restores manifest bytes and deletes temp art itself. needs http.server 8765
import json, os, subprocess, sys, shutil
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
MAN='img/field/moss/manifest.json'; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def chk(): return subprocess.run([sys.executable,'tools/moss/check_assets.py'],capture_output=True,text=True)
orig=open(MAN,encoding='utf-8').read()
os.makedirs('img/field/moss/real_t',exist_ok=True)
art={'fence_test':(22,64,(150,100,50,255)),'bench_test':(170,70,(60,60,200,255)),'stone_test':(90,220,(120,120,120,255))}
for k,(w,h,c) in art.items(): Image.new('RGBA',(w*2,h*2),c).save('img/field/moss/real_t/%s.png'%k)
def write(rules):
    m=json.loads(orig); m['node'][0:0]=rules; open(MAN,'w',encoding='utf-8').write(json.dumps(m,ensure_ascii=False,indent=1))
rules=[{"match":"^prop_post_boundary_wood","file":"real_t/fence_test.png","w":22,"h":64},
       {"match":"^prop_bench_view","file":"real_t/bench_test.png","w":170,"h":70},
       {"match":"^anc_(standing|boundary_stone)","file":"real_t/stone_test.png","w":90,"h":220}]
errs=[]
try:
    write(rules); r=chk(); print(r.stdout.strip().splitlines()[-1])
    check(r.returncode==0 and 'SHADOWED' not in r.stdout,'checker accepts the new rules')
    check('COLLISION prop_bench_view_01' in r.stdout,'checker warns: bench art 170px vs 80px blocker')
    check('COLLISION prop_post_boundary_wood' not in r.stdout,'fence post art (22) vs blocker (16) within tolerance')
    def run(tag,real):
        with sync_playwright() as p:
            b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
            pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda x:x.type=='error' and errs.append(x.text))
            pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
            pg.evaluate("PrologueProgress.seed(0);storyStage=3");pg.evaluate("document.querySelector('#hillExit').click()"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(1200)
            m=pg.evaluate("MossForest.map")
            for key,asset in (('fence','prop_post_boundary_wood_01'),('bench','prop_bench_view_01'),('stone','anc_standing_L_01')):
                p0=[q for q in m['props'] if q['asset']==asset]
                if not p0 and key=='fence': p0=[q for q in m['props'] if q['asset'].startswith('prop_post')]
                pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y+60)",[p0[0]['x'],p0[0]['y']]); pg.wait_for_timeout(700)
                n=pg.evaluate("k=>document.querySelectorAll('#forestWorld img[src*=\"real_t/%s_test\"]').length"%key,key)
                sz=pg.evaluate("k=>{const i=document.querySelector('#forestWorld img[src*=\"real_t/'+k+'_test\"]');return i?[parseFloat(i.style.width||i.width),parseFloat(i.style.height||i.height)]:null}",key)
                check((n>0)==real,'%s: %s sprite is %s (%d nodes, size %s)'%(tag,key,'the temp art' if n else 'the stand-in/placeholder',n,sz))
                if real and sz: check(sz==[art[key+'_test'][0],art[key+'_test'][1]],'%s: %s drawn at manifest w/h'%(tag,key))
            b.close()
    run('with temp art',True)
    open(MAN,'w',encoding='utf-8').write(orig); run('after removal',False)
    check(not errs,'0 console errors %s'%errs[:2])
finally:
    open(MAN,'w',encoding='utf-8').write(orig); shutil.rmtree('img/field/moss/real_t',ignore_errors=True)
    check(open(MAN,encoding='utf-8').read()==orig and not os.path.exists('img/field/moss/real_t'),'manifest and art folder restored')
sys.exit(1 if fails else 0)
