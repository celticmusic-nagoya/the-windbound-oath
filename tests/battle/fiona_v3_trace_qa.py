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
print('FAILS',fails);sys.exit(1 if fails else 0)
