# Hit sync: the hero's damage is applied to the LOGIC at once, but HP bar / hit flash / banner number wait for the blow frame of a delivered attack motion.
# Without a motion nothing changes (delay 0). Installs fabricated frames like motion_intake.py and restores everything itself. Needs http.server 8765.
import os, subprocess, sys, tempfile, shutil
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
MAN='img/battle/motion-manifest.json'; MOT='img/battle/characters/aidan/motion'
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
orig=open(MAN,'rb').read(); had=os.path.isdir(MOT); tmp=tempfile.mkdtemp()
def battle(pg):
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
    pg.evaluate("PrologueProgress.seed(0);startAttackBattle('attackGob1',100)"); pg.wait_for_timeout(1500)
    pg.evaluate("window.__log=[]; new MutationObserver(()=>{}).observe(document.body,{childList:true})")
    w0=pg.evaluate("document.querySelector('#v2GHP').style.width")
    pg.evaluate("window.__t0=performance.now();chooseNormalAct('attack','normal_enemy_0')")
    rows=[]
    for _ in range(14):
        rows.append(pg.evaluate("[Math.round(performance.now()-__t0),PrologueCombat.enemies.normal[0].hp,document.querySelector('#v2GHP').style.width,document.querySelector('#v2GTxt').textContent]")); pg.wait_for_timeout(40)
    return w0,rows
errs=[]
try:
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
        pg.on('pageerror',lambda e:errs.append(str(e)))
        w0,rows=battle(pg)
        check(rows[0][1]<100 and rows[0][2]!=w0 or rows[1][2]!=w0,'no motion installed: HP bar and logic change at once %s'%rows[:2])
        b.close()
    idle=Image.open('img/battle/characters/aidan/aidan_attack.png').convert('RGBA')
    for i in range(6):
        f=Image.new('RGBA',idle.size,(0,0,0,0)); f.alpha_composite(idle,(i*2,0)); f.save(os.path.join(tmp,'aidan_attack_%02d.png'%(i+1)))
    r=subprocess.run([sys.executable,'tools/battle/install_motion_frames.py',tmp,'--ms','100,100,100,100,120,120','--hit','4'],capture_output=True,text=True); check(r.returncode==0,'stub motion installed (hit at ~300 ms)')
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
        pg.on('pageerror',lambda e:errs.append(str(e)))
        w0,rows=battle(pg)
        print(rows)
        check(pg.evaluate("BattleMotion.hitDelay('aidan','attack')")==300,'hitDelay = 300 ms')
        check(rows[0][1]<100,'logic HP drops immediately (%d)'%rows[0][1])
        early=[r for r in rows if r[0]<230]; late=[r for r in rows if r[0]>360]
        check(early and all(r[2]==w0 for r in early),'HP bar still full before the blow frame (%d samples)'%len(early))
        check(late and late[-1][2]!=w0 and str(rows[0][1]) in late[-1][3],'HP bar and text update after the blow frame (%s)'%(late[-1][2:] if late else None))
        b.close()
    check(not errs,'no page errors %s'%errs[:2])
finally:
    open(MAN,'wb').write(orig)
    if not had: shutil.rmtree(MOT,ignore_errors=True)
    else:
        for f in os.listdir(MOT):
            if f.startswith('aidan_attack_') : pass
print('\nFAILS',len(fails)); sys.exit(1 if fails else 0)
