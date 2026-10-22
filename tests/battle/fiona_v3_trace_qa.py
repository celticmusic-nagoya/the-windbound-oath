"""Fiona idle v3 - trace-analysis checks on synthetic draw logs (pure Python, no browser): (1) animation-clock reset detection (Codex FIV3-RQ-01); (2) blinks cut by the observation window vs. real renderer skips.
The OLD soak predicate  `clock_resets==0 or all(<event looks like a pause> for e in events)`  accepted an unannounced reset (empty event list) and a reset
'explained' by a stale / still-open pause event. The NEW rule: a stable soak must have resets==0; a genuine pause->resume owning the reset is NOT_RUN_PAUSED (never PASS);
anything else is FAIL. Each bad case below is shown to be MISSED by the old predicate and DETECTED by the new one; the good cases must still pass."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
import fiona_v3_trace as S
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail if detail!='' else '')
    if not ok:fails.append(name)
def old_predicate(m,events):   # verbatim logic of tests/battle/fiona_idle_v3.py:95 before this fix
    return m['clock_resets']==0 or all(e[1].find('dialogueOpen')>=0 or 'hidden' in e[1] or 'Busy' in e[1] or 'actionCinematic' in e[1] for e in events)
def draw(now,t):
    ph,wave=S.spec_wave(t)
    return {'ctx':'raider','t':t,'start':-1e9,'state':0,'drawn':'','wave':wave,'ph':ph,'still':False,'now':now}
def trace(segments):
    """segments: [(first_now_ms, first_t_s, n_draws)] with 16 ms between draws; a new segment whose (now/1000 - t) offset differs is a clock reset."""
    out=[]
    for now0,t0,n in segments:
        for k in range(n):out.append(draw(now0+16*k,t0+0.016*k))
    return out
def run(tr,events):
    f,m=S.analyze(tr,'raider',require_no_resets=True);return f,m,S.classify_soak(tr,'raider',events)
# --- good: continuous 20 s, no events
tr=trace([(1000,5.0,1250)]);f,m,v=run(tr,[])
check(not f and m['clock_resets']==0 and v['verdict']=='PASS' and old_predicate(m,[]),'GOOD continuous soak: no resets, PASS',(m['clock_resets'],v['verdict']))
# --- BAD A (Codex's case): t jumps back 1.016 s -> 0 s while now keeps advancing 16 ms, waves follow t, NO events at all
trA=trace([(1000,0.0,64),(1000+16*64,0.0,500)]);evA=[]
fA,mA,vA=run(trA,evA)
check(mA['clock_resets']==1,'BAD-A unannounced reset is counted (1)',mA['clock_resets'])
check(old_predicate(mA,evA) is True,'BAD-A is MISSED by the old predicate (the defect)')
check(bool(fA) and vA['verdict']=='FAIL' and len(vA['unowned'])==1,'BAD-A is DETECTED by the new rule (analyze failure + FAIL verdict)',(fA,vA['verdict']))
# --- BAD B: reset with only an unrelated, still-open dialogueOpen event from long before it (no resume)
trB=trace([(1000,0.0,1000),(1000+16*1000,0.0,300)]);evB=[[100,'raiderBattleMode dialogueOpen']]
fB,mB,vB=run(trB,evB)
check(old_predicate(mB,evB) is True,'BAD-B (stale open dialogueOpen event) is MISSED by the old predicate (the defect)')
check(bool(fB) and vB['verdict']=='FAIL','BAD-B is DETECTED by the new rule',(fB,vB['verdict']))
# --- BAD B2: a pause that began AND ended long before the reset (stale, closed) must not own it either
evB2=[[100,'raiderBattleMode dialogueOpen'],[300,'raiderBattleMode']]
fB2,mB2,vB2=run(trB,evB2)
check(vB2['verdict']=='FAIL','BAD-B2 (pause closed long before the reset) is DETECTED',vB2['verdict'])
# --- BAD C: an event inside the gap that is NOT a pause (class change that does not pause the renderer) owns nothing
trC=trace([(1000,0.0,300),(1000+16*300+2000,0.0,300)]);evC=[[1000+16*300+500,'raiderBattleMode somethingElse']]
fC,mC,vC=run(trC,evC);check(vC['verdict']=='FAIL','BAD-C (non-pause event in the gap) is DETECTED',vC['verdict'])
# --- LEGIT pause->resume: draws stop, dialogueOpen opens then closes inside the gap, renderer resets on resume.
now_pause=1000+16*300;now_resume=now_pause+3000
trP=trace([(1000,0.0,300),(now_resume,0.0,300)]);evP=[[now_pause+5,'raiderBattleMode dialogueOpen'],[now_resume,'raiderBattleMode']]
fP,mP,vP=run(trP,evP)
check(mP['clock_resets']==1 and vP['verdict']=='NOT_RUN_PAUSED' and len(vP['owned'])==1 and not vP['unowned'],'LEGIT pause->resume: the reset is owned, verdict NOT_RUN_PAUSED (re-observe), not PASS',vP['verdict'])
check(bool(fP),'LEGIT pause->resume run still fails the stable-soak rule (resets must be 0), so it can never pass silently',fP)
# --- hidden tab pause->resume is owned too
evH=[[now_pause+5,'hidden=true'],[now_resume-1,'hidden=false']];fH,mH,vH=run(trP,evH)
check(vH['verdict']=='NOT_RUN_PAUSED','LEGIT hidden->visible: owned, NOT_RUN_PAUSED',vH['verdict'])
# --- mixed: one owned pause reset plus one unannounced reset -> FAIL
trM=trace([(1000,0.0,300),(now_resume,0.0,300),(now_resume+16*300,0.0,300)]);fM,mM,vM=run(trM,evP)
check(mM['clock_resets']==2 and vM['verdict']=='FAIL' and len(vM['owned'])==1 and len(vM['unowned'])==1,'MIXED owned+unannounced reset -> FAIL',(vM['verdict'],mM['clock_resets']))
# --- sub-threshold jitter (<1 us offset change) is not a reset
trJ=trace([(1000,0.0,300)]);
for x in trJ[150:]:x['t']+=1e-8
fJ,mJ,vJ=run(trJ,[]);check(mJ['clock_resets']==0 and vJ['verdict']=='PASS','float-noise offset change (1e-8 s) is not a reset',mJ['clock_resets'])

# ---- observation-window edges: a blink cut by the START or END of the trace must not be reported as a renderer skip; a complete blink with a missing state and continuous draws still must be
def blink_trace(t_from,t_to,start,skip=None):
    out=[];t=t_from
    while t<=t_to+1e-12:
        st=S.spec_state((t-start)*1000) if t>=start else 0
        ph,wave=S.spec_wave(t);stt=0 if st==skip else st   # skip: the renderer never draws that state (draw shows the previous one's neighbour -> state absent)
        out.append({'ctx':'raider','t':t,'start':start,'state':stt if skip is None else (st if st!=skip else 0),'drawn':S.spec_drawn(st if skip is None else (st if st!=skip else 0)),'wave':wave,'ph':ph,'still':False,'now':1000+t*1000});t+=0.016
    return out
def run2(tr):
    f,m=S.analyze(tr,'raider');return f,m
# end-truncated: window ends 183 ms into a 260 ms blink -> only states 1,2,3,4,3 drawn, draws continuous
f1,m1=run2(blink_trace(10.0,14.818,14.635))
check(m1['blinks_truncated_by_window']==1 and not [x for x in f1 if 'lack states' in x],'blink cut by the END of the trace window is not a renderer skip',(f1,m1['blinks_truncated_by_window']))
# start-truncated: window starts 100 ms into the blink
f2,m2=run2(blink_trace(10.1,16.0,10.0))
check(m2['blinks_truncated_by_window']==1 and not [x for x in f2 if 'lack states' in x],'blink cut by the START of the trace window is not a renderer skip',(f2,m2['blinks_truncated_by_window']))
# complete blink fully inside the window, continuous 16 ms draws, but state 2 is never drawn on the way up -> renderer skip, must FAIL
f3,m3=run2(blink_trace(9.0,15.0,12.0,skip=2))
check(m3['blinks_truncated_by_window']==0 and any('lack states' in x or 'state' in x for x in f3),'complete in-window blink with a never-drawn state and continuous draws is still DETECTED',f3)
# complete, correct blink in the window: clean
f4,m4=run2(blink_trace(9.0,15.0,12.0));check(not [x for x in f4 if 'lack states' in x] and m4['blinks_fully_sampled']==1,'complete correct blink: no failure, fully sampled',(f4,m4['blinks_fully_sampled']))
# ---- P2 (Codex FIV3 FAIL): a render STALL and a skipped blink STATE are different events ----------------------------------------------------------------------------------
# OLD analyzer = the one at the previously submitted SHA 320ba8c (read from git when available) so the before/after difference is shown by this very file.
import subprocess,types
def old_analyzer():
    try:
        src=subprocess.run(['git','show','320ba8ca7c480f77e69a6e48faf8238772c1567c:tools/qa/fiona_v3_trace.py'],cwd=Path(__file__).resolve().parents[2],capture_output=True,check=True).stdout.decode()
    except Exception:return None
    mod=types.ModuleType('fiona_v3_trace_old');exec(compile(src,'fiona_v3_trace_old','exec'),mod.__dict__);return mod
OLD=old_analyzer()
def gen(spans,start,skip_clock=None):
    """spans: [(t_from,t_to)] of 16 ms draws on a clock that follows the wall clock (now=1000+t*1000); the gaps between spans are STALLS (nothing drawn, wall and clock both move on).
    skip_clock=(t_at,jump): from draw time t_at the animation clock runs `jump` seconds ahead of the wall clock (draws stay 16 ms apart on the wall)."""
    out=[]
    for a,b in spans:
        t=a
        while t<=b+1e-12:
            tt=t+(skip_clock[1] if skip_clock and t>=skip_clock[0] else 0)
            st=S.spec_state((tt-start)*1000) if tt>=start else 0;ph,wave=S.spec_wave(tt)
            out.append({'ctx':'raider','t':tt,'start':start,'state':st,'drawn':S.spec_drawn(st),'wave':wave,'ph':ph,'still':False,'now':1000+t*1000});t+=0.016
    return out
def lack(f):return [x for x in f if 'lack states' in x]
def stallf(f):return [x for x in f if x.startswith('render stall')]
# S1: the blink at t=12.000 starts, one draw shows state 1, then the page stops drawing for 7.9 s (Codex's case) and resumes with a consistent clock
trS1=gen([(9.0,12.010),(19.9,25.0)],12.0)
fo,mo=OLD.analyze(trS1,'raider') if OLD else (None,None);fn,mn=S.analyze(trS1,'raider')
if OLD:check(bool(lack(fo)),'S1 OLD analyzer calls the 7.9 s stall a skipped blink state (the defect)',lack(fo))
check(not lack(fn) and len(stallf(fn))==1 and mn['stalls'] and abs(mn['max_stall_ms']-7890)<40,'S1 NEW analyzer: no state-skip claim; one separate render-stall failure of ~7.9 s',(fn,mn['stalls']))
check(mn['blinks_unsampled_inside_a_stall']==1 and mn['blinks_unsampled_without_a_stall']==0,'S1 the unsampled blink is attributed to the stall, not to the renderer',(mn['blinks_unsampled_inside_a_stall'],mn['blinks_unsampled_without_a_stall']))
# S2: a clean stall in a quiet period (no blink anywhere near) is a stall failure and nothing else
trS2=gen([(9.0,10.0),(17.9,22.0)],12.0)
fn2,mn2=S.analyze(trS2,'raider')
check(len(stallf(fn2))==1 and not lack(fn2) and mn2['clock_resets']==0,'S2 stall alone: exactly one stall failure, no skip claim, no clock reset',(fn2,mn2['clock_resets']))
# S3: a SHORT hole (150 ms, jank) in the middle of a blink is not a stall failure and not a skip (behaviour kept from before)
trS3=gen([(9.0,12.040),(12.19,15.0)],12.0);fn3,mn3=S.analyze(trS3,'raider')
check(not stallf(fn3) and not lack(fn3) and mn3['blinks_unsampled_inside_a_stall']==1,'S3 150 ms hole inside a blink: no stall failure, no skip, attributed to the hole',(fn3,mn3['blinks_unsampled_inside_a_stall']))
# S4: the animation clock jumps 0.1 s ahead in mid-blink while draws stay 16 ms apart on the wall = a REAL skipped state. The OLD analyzer measured the gap on the animation clock (looks like a 100 ms hole) and MISSED it.
trS4=gen([(9.0,15.0)],12.0,skip_clock=(12.02,0.1));fo4,mo4=OLD.analyze(trS4,'raider') if OLD else (None,None);fn4,mn4=S.analyze(trS4,'raider')
if OLD:check(not lack(fo4),'S4 OLD analyzer MISSES a clock jump over blink states with continuous wall draws (the weaker rule)',lack(fo4))
check(bool(lack(fn4)) and not stallf(fn4),'S4 NEW analyzer DETECTS it as a skipped state (and not as a stall)',fn4)
# S5: the earlier strict cases still behave identically on the new analyzer (never-drawn state with continuous draws; window-edge blinks; clean blink)
check(any('state' in x for x in S.analyze(blink_trace(9.0,15.0,12.0,skip=2),'raider')[0]),'S5 never-drawn state with continuous draws is still detected')
check(not lack(S.analyze(blink_trace(9.0,15.0,12.0),'raider')[0]) and not stallf(S.analyze(blink_trace(9.0,15.0,12.0),'raider')[0]),'S5 clean continuous blink: no failure of either kind')
# ---- a hole that the game itself explains (renderer paused: dialogue / presentation / hidden page) is an interrupted observation, not a stall; an unexplained one is a stall ------------------
trP=gen([(9.0,12.010),(19.9,25.0)],12.0)   # hole = page time 13010..20900 ms
evP=[[13000,'raiderBattleMode dialogueOpen'],[20850,'raiderBattleMode']]
fP,mP=S.analyze(trP,'raider',require_no_resets=True,events=evP);vP=S.classify_soak(trP,'raider',evP)
check(not stallf(fP) and len(mP['paused_holes'])==1 and vP['verdict']=='NOT_RUN_PAUSED','P1 7.9 s hole fully owned by a dialogue pause: no stall failure, verdict NOT_RUN_PAUSED (never PASS)',(fP,vP['verdict'],mP['paused_holes']))
fQ,mQ=S.analyze(trP,'raider',require_no_resets=True,events=[]);vQ=S.classify_soak(trP,'raider',[])
check(len(stallf(fQ))==1 and vQ['verdict']=='FAIL','P2 the same hole with no pause event is an unexplained stall: FAIL',(fQ,vQ['verdict']))
fR,mR=S.analyze(trP,'raider',events=[[15000,'raiderBattleMode dialogueOpen'],[15200,'raiderBattleMode']]);vR=S.classify_soak(trP,'raider',[[15000,'raiderBattleMode dialogueOpen'],[15200,'raiderBattleMode']])
check(len(stallf(fR))==1 and vR['verdict']=='FAIL','P3 a 200 ms pause somewhere inside a 7.9 s hole does not own the hole: stall',(fR,vR['verdict']))
evH=[[13000,'hidden=true'],[20850,'hidden=false']];vH2=S.classify_soak(trP,'raider',evH)
check(vH2['verdict']=='NOT_RUN_PAUSED','P4 hole owned by a hidden page -> NOT_RUN_PAUSED',vH2['verdict'])
evO=[[13000,'raiderBattleMode dialogueOpen']];fO,mO=S.analyze(trP,'raider',events=evO)
check(len(stallf(fO))==1,'P5 a pause that is still open when drawing resumes does not own the hole (drawing during a pause explains nothing)',(fO,))
# ---- stall attribution: which independent clock stopped together with the draw log -----------------------------------------------------------------------------------
H=(1000.0,8900.0)
check(S.classify_incident(S.stall_layers(1000,8900,{'W':[H],'T':[H],'R':[H]})).startswith('process-level freeze'),'ATTR all four clocks stopped -> process-level freeze (not the page)')
check(S.classify_incident(S.stall_layers(1000,8900,{'W':[],'T':[H],'R':[H]})).startswith('main thread blocked'),'ATTR worker alive, main timers + rAF stopped -> main thread blocked')
check(S.classify_incident(S.stall_layers(1000,8900,{'W':[],'T':[],'R':[H]})).startswith('rAF delivery stopped'),'ATTR only rAF stopped -> frame delivery')
check(S.classify_incident(S.stall_layers(1000,8900,{'W':[],'T':[],'R':[]})).startswith('idle renderer did not draw'),'ATTR nothing but the draw log stopped -> the idle renderer itself')
check(S.classify_incident(S.stall_layers(1000,8900,{'W':[],'T':[],'R':[(20000.0,21000.0)]})).startswith('idle renderer did not draw'),'ATTR a hole of another clock elsewhere in time is not blamed')
print('FAILS',fails);sys.exit(1 if fails else 0)
