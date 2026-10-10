# M6 real-asset swap dry run: drops a fake "real" tree + a fake ancient-tree PNG into img/field/moss/, edits manifest.json only,
# and checks (1) the checker flags a mis-ordered rule, (2) correctly ordered rules replace the stand-in / null placeholder in the
# running game with no code change, (3) removing them restores the stand-ins. Restores every touched file. Needs http.server 8765.
import json, os, subprocess, sys, shutil
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
MAN='img/field/moss/manifest.json'; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def chk(): return subprocess.run([sys.executable,'tools/moss/check_assets.py'],capture_output=True,text=True)
orig=open(MAN,encoding='utf-8').read(); m=json.loads(orig)
os.makedirs('img/field/moss/real_t',exist_ok=True)
Image.new('RGBA',(200,260),(200,30,30,255)).save('img/field/moss/real_t/oak_test.png')
Image.new('RGBA',(300,420),(30,30,200,255)).save('img/field/moss/real_t/ancient_test.png')
try:
    # (1) real rule AFTER the stand-in -> checker must warn
    bad=json.loads(orig); bad['node'].append({"match":"^tree_oak_L_01$","file":"real_t/oak_test.png","w":170,"h":220})
    open(MAN,'w',encoding='utf-8').write(json.dumps(bad,ensure_ascii=False,indent=1))
    r=chk(); check('SHADOWED' in r.stdout and r.returncode==0,'checker warns that a real rule listed after the stand-in is shadowed')
    # (2) real rules BEFORE -> applied
    good=json.loads(orig)
    good['node'][0:0]=[{"match":"^tree_oak_L_01$","file":"real_t/oak_test.png","w":170,"h":220},{"match":"^tree_ancient","file":"real_t/ancient_test.png","w":260,"h":380}]
    open(MAN,'w',encoding='utf-8').write(json.dumps(good,ensure_ascii=False,indent=1))
    for k,(w,h) in {'chest_closed':(60,48),'chest_open':(60,48),'fiona':(56,84)}.items():
        Image.new('RGBA',(w*2,h*2),(30,200,30,255)).save('img/field/moss/real_t/%s.png'%k)
        good.setdefault('entity',{})[k]={"file":"real_t/%s.png"%k,"w":w,"h":h}
    open(MAN,'w',encoding='utf-8').write(json.dumps(good,ensure_ascii=False,indent=1))
    r=chk(); check(r.returncode==0 and 'SHADOWED' not in r.stdout,'checker accepts the correctly ordered manifest'); print(r.stdout.strip().splitlines()[-1])
    errs=[]
    def run(tag,expect_real):
        with sync_playwright() as p:
            b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
            pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda x:x.type=='error' and errs.append(x.text))
            pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
            pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(1500)
            a1=pg.evaluate("document.querySelectorAll('#forestWorld img[src*=\"real_t/oak_test\"]').length")
            standin=pg.evaluate("document.querySelectorAll('#forestWorld img[src*=\"standin/tree\"]').length")
            check((a1>0)==expect_real,'%s: real oak sprites in A1 = %d (stand-in trees = %d)'%(tag,a1,standin))
            ent=pg.evaluate("({chest:document.querySelectorAll('.forest-treasure.art').length,fiona:document.querySelector('#forestFiona').classList.contains('art')||document.querySelector('#forestFiona').classList.contains('fiona-sprite'),fw:document.querySelector('#forestFiona').style.width})")
            check((ent['chest']>0 and ent['fiona'])==expect_real,'%s: entity art on chests/Fiona = %s'%(tag,ent))
            if expect_real:
                size=pg.evaluate("(()=>{const i=document.querySelector('#forestWorld img[src*=\"real_t/oak_test\"]');return [i.style.width||i.width,i.style.height||i.height]})()"); print('   sprite size',size)
            b.close()
    run('with real rules',True)
    # (3) revert -> stand-ins return
    open(MAN,'w',encoding='utf-8').write(orig); run('after removal',False)
    check(not errs,'0 console errors %s'%errs[:2])
finally:
    open(MAN,'w',encoding='utf-8').write(orig); shutil.rmtree('img/field/moss/real_t',ignore_errors=True)
    check(open(MAN,encoding='utf-8').read()==orig and not os.path.exists('img/field/moss/real_t'),'manifest and art folder restored')
sys.exit(1 if fails else 0)
