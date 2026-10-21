"""Fiona idle v3 QA helpers: the APPROVED spec (hard-coded here, independent of assets.js) and a conformance analysis of real draw traces."""
import math
SEQ=[(1,30),(2,30),(3,35),(4,70),(3,35),(2,30),(1,30)]   # approved blink: state, ms
BLINK_MS=sum(d for _,d in SEQ)                               # 260
CYCLE=4.0
def spec_state(ms):
    if ms<0:return 0
    for s,d in SEQ:
        if ms<d:return s
        ms-=d
    return 0
def spec_drawn(state):return '' if state==0 else 'L:%d,R:%d'%(state,state)
def spec_wave(t):
    ph=(t%CYCLE)/CYCLE;return ph,(1-math.cos(ph*2*math.pi))/2
def analyze(tr,ctx):
    """tr: list of draw records from BattleIdleMotion.traceStop(). Returns (failures, metrics). Every real draw is compared with the spec at its OWN clock value."""
    d=[x for x in tr if x['ctx']==ctx and not x['still']];fails=[];m={'draws':len(d)}
    bad_state=[x for x in d if x['state']!=(spec_state((x['t']-x['start'])*1000) if x['start']>-1e8 else 0)]
    if bad_state:fails.append('draw state != spec at its own clock (%d draws, e.g. %s)'%(len(bad_state),{k:bad_state[0][k] for k in ('t','start','state')}))
    bad_lr=[x for x in d if x['drawn']!=spec_drawn(x['state'])]
    if bad_lr:fails.append('overlays actually drawn != L+R of the same state (%d draws, e.g. %r for state %d)'%(len(bad_lr),bad_lr[0]['drawn'],bad_lr[0]['state']))
    bad_br=[x for x in d if abs(x['ph']-spec_wave(x['t'])[0])>1e-9 or abs(x['wave']-spec_wave(x['t'])[1])>1e-9]
    if bad_br:fails.append('breath phase/wave != 4 s cos cycle (%d draws)'%len(bad_br))
    # animation clock must track wall clock (no drift): now/1000 - t constant between resets
    off=[x['now']/1000-x['t'] for x in d];jumps=sum(1 for i in range(1,len(off)) if abs(off[i]-off[i-1])>1e-6);m['clock_resets']=jumps
    gaps=[(d[i+1]['now']-d[i]['now']) for i in range(len(d)-1)];m['max_draw_gap_ms']=round(max(gaps),1) if gaps else None;m['gaps_over_100ms']=sum(1 for g in gaps if g>100)
    # blinks: group by start
    groups={}
    for x in d:
        if x['start']>-1e8 and x['state']>0:groups.setdefault(round(x['start'],6),[]).append(x)
    full=0;partial=[]
    for st,xs in groups.items():
        seen=[]
        for x in xs:
            if not seen or seen[-1]!=x['state']:seen.append(x['state'])
        if seen==[1,2,3,4,3,2,1]:full+=1
        else:partial.append(seen)
    m['blinks']=len(groups);m['blinks_fully_sampled']=full;m['blinks_with_unsampled_states']=len(partial)
    # a state may be missing from the real draw log only if the page did not draw for longer than that state lasts (host stall); otherwise the renderer skipped it
    DUR={1:30,2:30,3:35,4:70};ts=[x['t'] for x in d];unjustified=0
    for st,xs in groups.items():
        seen=[]
        for x in xs:
            if not seen or seen[-1]!=x['state']:seen.append(x['state'])
        if seen==[1,2,3,4,3,2,1]:continue
        miss=[q for q in (1,2,3,4) if q not in seen] or [1]
        need=min(DUR[q] for q in miss)
        win=[t for t in ts if st-0.1<=t<=st+0.36]
        mg=max([(win[i+1]-win[i])*1000 for i in range(len(win)-1)] or [0])
        if mg<=need:unjustified+=1;m.setdefault('unjustified_detail',[]).append({'start':st,'seen':seen,'max_gap_ms':round(mg,1),'need_ms':need,'draws':[(round((t-st)*1000,1)) for t in win]})
    m['blinks_unsampled_without_a_stall']=unjustified
    if unjustified:fails.append('%d blink(s) lack states although the page drew continuously (renderer skipped states)'%unjustified)
    # a blink whose sampled order is not a legal sub-sequence of the spec is a FAIL (not just missing states)
    for seen in partial:
        ok=all(s in (1,2,3,4) for s in seen)
        k=0
        for s in seen:
            while k<len(SEQ) and SEQ[k][0]!=s:k+=1
            if k==len(SEQ):ok=False;break
            k+=1
        if not ok:fails.append('illegal blink order %r'%seen);break
    starts=sorted(groups);g=[starts[i+1]-starts[i] for i in range(len(starts)-1)];m['blink_gaps_s']=[round(v,3) for v in g][:12]
    slack=(m['max_draw_gap_ms'] or 0)/1000
    if any(v<3.0-1e-9 or v>6.0+slack+1e-9 for v in g):fails.append('blink gap outside 3-6 s (+draw latency)')
    return fails,m
def probe_cases():
    """(blink_start, t_seconds, expected_state) around every approved boundary, with a controlled clock (0.01 ms around boundaries for float safety)."""
    out=[];edges=[0];
    for _,dd in SEQ:edges.append(edges[-1]+dd)
    for e in edges:
        for dt in (-0.01,0.01):
            ms=e+dt
            if ms>=0:out.append((ms,spec_state(ms)))
    for k in range(0,300):out.append((k*1.0+0.5,spec_state(k*1.0+0.5)))
    out.append((-5.0,0))
    return out
