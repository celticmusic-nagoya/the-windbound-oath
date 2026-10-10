# M6 walk-frame intake dry run: fabricates 4 frames for the 7 waiting NPCs (+ extra farmer_male / emma frames), installs them
# through tools/lind/install_walk_frames.py, checks the runtime picks them up (frame cycling, canvas, no console errors),
# then restores every touched file with git. Needs http.server 8765. Never leaves synthetic art behind.
import os, subprocess, sys, tempfile, shutil
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
WAIT=['young_man','young_woman','elder_man','elder_woman','merchant','innkeeper','caretaker']
EXTRA=['farmer_male']
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def idle(n): return 'img/field/lind/npc/villagers/%s_idle.png'%n
tmp=tempfile.mkdtemp(prefix='walk_')
try:
    for n in WAIT+EXTRA:
        im=Image.open(idle(n)).convert('RGBA')
        for i,dx in enumerate([-2,0,2,0],1):
            c=Image.new('RGBA',im.size,(0,0,0,0)); c.paste(im,(dx,0)); c.save('%s/%s_walk_%02d.png'%(tmp,n,i))
    # --- rejection cases first
    Image.new('RGB',(10,10)).save(tmp+'/boy_walk_01.png'); Image.new('RGB',(10,10)).save(tmp+'/boy_walk_03.png')
    r=subprocess.run([sys.executable,'tools/lind/install_walk_frames.py',tmp,'--npc','boy','--dry-run'],capture_output=True,text=True)
    check(r.returncode==1 and 'RGBA' in r.stdout and 'gaps' in r.stdout,'validator rejects RGB frames and numbering gaps')
    os.remove(tmp+'/boy_walk_01.png'); os.remove(tmp+'/boy_walk_03.png')
    r=subprocess.run([sys.executable,'tools/lind/install_walk_frames.py',tmp,'--write-bounds'],capture_output=True,text=True); print(r.stdout[-400:],r.stderr[-300:])
    check(r.returncode==0,'install of 7 waiting NPCs + farmer_male succeeds')
    r=subprocess.run([sys.executable,'tools/lind/check_walk_frames.py'],capture_output=True,text=True)
    check(r.returncode==0 and 'WAITING' not in r.stdout.replace('farmer_male','').split('young_man')[0] and r.stdout.count('WAITING')==0,'check_walk_frames: nothing waiting after intake')
    errs=[]
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
        pg.evaluate("devJump('training')"); pg.wait_for_timeout(300); pg.evaluate("LindFieldReview.open()"); pg.wait_for_timeout(800)
        for n in WAIT+EXTRA:
            frames=pg.evaluate("(id)=>{const a=LindFieldNPCs.actors.find(a=>a.id===id);return a?a.walkSeq:null}",n)
            check(frames==[n+'_walk_0%d'%i for i in (1,2,3,4)],'%s: runtime built the 4-frame walk sequence %s'%(n,frames))
            moves=pg.evaluate("(id)=>{const a=LindFieldNPCs.actors.find(a=>a.id===id);return Boolean(a.life||a.play)}",n)
            if not moves: print('note %s has no walking routine/play today: frames are installed and ready, nothing animates yet'%n); continue
            seen=pg.evaluate("""(id)=>new Promise(r=>{const a=LindFieldNPCs.actors.find(a=>a.id===id),s=new Set();if(!a.play){a.life=null;a.play=true;}let t0=performance.now();
                const f=()=>{a.state='WALK';for(const im of a.element.querySelectorAll('img'))if(!im.hidden)s.add(im.src.split('/').pop());
                performance.now()-t0<1500?requestAnimationFrame(f):r([...s])};requestAnimationFrame(f)})""",n)
            check(len(seen)>=3,'%s: walking cycles through %d frames %s'%(n,len(seen),seen[:4]))
        b.close()
    check(not errs,'0 console errors %s'%errs[:2])
finally:
    shutil.rmtree(tmp,ignore_errors=True)
    subprocess.run(['git','checkout','--','js/field/lind-content-bounds.js'])
    subprocess.run('git clean -fdq -- img/field/lind/npc/villagers',shell=True)
    subprocess.run(['git','checkout','--','img/field/lind/npc'])
sys.exit(1 if fails else 0)
