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
PAUSE_CLASSES=('battlePresentationBusy','dialogueOpen','actionCinematic')   # body classes under which BattleIdleMotion.paused() is true (js/battle-idle-motion.js)
def reset_points(tr,ctx):
    """Every animation-clock reset in the real draw log: consecutive draws whose (now/1000 - t) offset changed. Returns [{i,now_prev,now,t_prev,t}]."""
    d=[x for x in tr if x['ctx']==ctx and not x['still']];out=[]
    for i in range(1,len(d)):
        if abs((d[i]['now']/1000-d[i]['t'])-(d[i-1]['now']/1000-d[i-1]['t']))>1e-6:out.append({'i':i,'now_prev':d[i-1]['now'],'now':d[i]['now'],'t_prev':d[i-1]['t'],'t':d[i]['t']})
    return out
def pause_intervals(events,t_end=float('inf')):
    """events: [[performance.now ms, label]] where label is either a body className snapshot or 'hidden=true|false'. Returns [(start,end)] of the intervals during which the idle renderer is paused
    (a pause class on <body>, or the page hidden). An interval that never ends inside the log has end=inf (the renderer is still paused, so it cannot own a later reset)."""
    cls=False;hid=False;iv=[];cur=None
    for ms,lab in sorted(events,key=lambda e:e[0]):
        if lab.startswith('hidden='):hid=lab=='hidden=true'
        else:cls=any(c in lab.split() for c in PAUSE_CLASSES)
        p=cls or hid
        if p and cur is None:cur=ms
        if not p and cur is not None:iv.append((cur,ms));cur=None
    if cur is not None:iv.append((cur,float('inf')))
    return iv
def reset_owner(r,iv,tol=50.0):
    """A reset is owned only by a pause that (a) overlaps the silent gap between the draw before and the draw after the reset and (b) has ENDED by the time of that draw
    (the renderer resets on resume). A stale pause from earlier, or one still open, owns nothing."""
    for s,e in iv:
        if s<=r['now']+tol and e>=r['now_prev']-tol and e<=r['now']+tol:return (s,e)
    return None
STALL_MS=500.0
def draw_holes(tr,ctx,events=None,stall_ms=STALL_MS,tol=600.0):
    """Holes (> stall_ms on the wall clock) between consecutive real draws, split into (unowned, owned). A hole is OWNED when the renderer was legitimately paused for it (a pause class on <body> or the page hidden,
    pause_intervals()) for all of it but a resume/pause latency of `tol` ms in total; an owned hole is an interrupted observation (NOT_RUN_PAUSED), an unowned one is a STALL (host/page stopped without a reason the game gave)."""
    d=[x for x in tr if x['ctx']==ctx and not x['still']];iv=pause_intervals(events or []);un=[];ow=[]
    for i in range(len(d)-1):
        a,b=d[i]['now'],d[i+1]['now'];g=b-a
        if g<=stall_ms:continue
        cov=sum(max(0.0,min(b,e)-max(a,s_)) for s_,e in iv if e<=b+100.0)   # the pause must have ENDED by the time drawing resumed; drawing again while a pause is still open explains nothing
        h={'at_now_ms':round(a),'gap_ms':round(g,1),'paused_ms':round(cov)}
        (ow if cov>=g-tol else un).append(h)
    return un,ow
def classify_soak(tr,ctx,events):
    """Verdict for a soak that is meant to run WITHOUT any intended pause: PASS only with zero resets. Resets that a genuine pause->resume owns make the observation NOT_RUN_PAUSED
    (a paused run is never an unconditional PASS - re-observe the segment); any unowned reset is FAIL."""
    rs=reset_points(tr,ctx);un_h,ow_h=draw_holes(tr,ctx,events)
    if not rs:return {'verdict':'FAIL' if un_h else ('NOT_RUN_PAUSED' if ow_h else 'PASS'),'resets':0,'unowned':[],'owned':[],'stalls':un_h,'paused_holes':ow_h}
    iv=pause_intervals(events);owned=[];unowned=[]
    for r in rs:(owned if reset_owner(r,iv) else unowned).append(r)
    return {'verdict':'FAIL' if (unowned or un_h) else 'NOT_RUN_PAUSED','resets':len(rs),'unowned':unowned,'owned':owned,'stalls':un_h,'paused_holes':ow_h}
def analyze(tr,ctx,require_no_resets=False,events=None):
    """tr: list of draw records from BattleIdleMotion.traceStop(). Returns (failures, metrics). Every real draw is compared with the spec at its OWN clock value.
    require_no_resets: for a stable soak with no intended pause, ANY animation-clock reset is a failure (it is counted either way as m['clock_resets'])."""
    d=[x for x in tr if x['ctx']==ctx and not x['still']];fails=[];m={'draws':len(d)}
    bad_state=[x for x in d if x['state']!=(spec_state((x['t']-x['start'])*1000) if x['start']>-1e8 else 0)]
    if bad_state:fails.append('draw state != spec at its own clock (%d draws, e.g. %s)'%(len(bad_state),{k:bad_state[0][k] for k in ('t','start','state')}))
    bad_lr=[x for x in d if x['drawn']!=spec_drawn(x['state'])]
    if bad_lr:fails.append('overlays actually drawn != L+R of the same state (%d draws, e.g. %r for state %d)'%(len(bad_lr),bad_lr[0]['drawn'],bad_lr[0]['state']))
    bad_br=[x for x in d if abs(x['ph']-spec_wave(x['t'])[0])>1e-9 or abs(x['wave']-spec_wave(x['t'])[1])>1e-9]
    if bad_br:fails.append('breath phase/wave != 4 s cos cycle (%d draws)'%len(bad_br))
    # animation clock must track wall clock (no drift): now/1000 - t constant between resets
    off=[x['now']/1000-x['t'] for x in d];jumps=sum(1 for i in range(1,len(off)) if abs(off[i]-off[i-1])>1e-6);m['clock_resets']=jumps
    if require_no_resets and jumps:fails.append('animation clock reset %d time(s) in a stable soak (no intended pause)'%jumps)
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
    # Two DIFFERENT events are kept apart here (Codex FIV3 FAIL, P2):
    #  (1) RENDER STALL = a long hole between consecutive real draws on the WALL clock (host/page stopped, whatever the cause). It is reported on its own (m['stalls']) and fails the soak as a stall.
    #  (2) STATE SKIP = the renderer's animation clock jumped over a blink state although draws kept coming. Every one of the 7 slots of a complete blink is checked (not only states that never appear). A slot without any draw is a SKIP only if the two draws that bracket that
    #      state's time slot (on the animation clock) are no more than the slot's duration apart on the wall clock; if they are further apart, the slot lay inside a hole (a stall), which is event (1), not a skip.
    # The previous rule looked only at draws inside [start-0.1, start+0.36] and therefore saw NO gap (0) whenever the hole swallowed the window, calling a stall a 'skipped state'.
    DUR={1:30,2:30,3:35,4:70};ts=[x['t'] for x in d]
    m['stall_threshold_ms']=STALL_MS
    un_h,ow_h=draw_holes(tr,ctx,events);m['stalls']=un_h;m['paused_holes']=ow_h
    m['max_stall_ms']=max([h['gap_ms'] for h in un_h] or [0]);m['max_paused_hole_ms']=max([h['gap_ms'] for h in ow_h] or [0])
    if un_h:fails.append('render stall: %d hole(s) of >%d ms between consecutive real draws (max %.0f ms) not explained by a pause - a host/page stop, NOT a skipped blink state'%(len(un_h),STALL_MS,m['max_stall_ms']))
    # A blink that starts before the first traced draw or ends after the last one is cut by the OBSERVATION WINDOW, not by the renderer: its missing states were never in the log.
    t_lo,t_hi=(min(ts),max(ts)) if ts else (0,0);m['blinks_truncated_by_window']=sum(1 for st in groups if st<t_lo-1e-9 or st+BLINK_MS/1000>t_hi+1e-9)
    unjustified=0;slot_in_hole=0;by_t=sorted(d,key=lambda x:x['t'])
    import bisect
    tt=[x['t'] for x in by_t]
    for st,xs in groups.items():
        if st<t_lo-1e-9 or st+BLINK_MS/1000>t_hi+1e-9:continue
        seen=[]
        for x in xs:
            if not seen or seen[-1]!=x['state']:seen.append(x['state'])
        if seen==[1,2,3,4,3,2,1]:continue
        off=0.0;skipped=[];hole=[]
        for q,dur in SEQ:
            a_,b_=st+off/1000,st+(off+dur)/1000;off+=dur
            i=bisect.bisect_left(tt,a_);j=bisect.bisect_left(tt,b_)
            if j>i:continue   # a draw lies inside this slot, so it would have shown the state (a wrong state is caught by the per-draw spec check above)
            if i==0 or j>=len(by_t):continue   # no bracketing draw on one side: window edge, not evidence of anything
            gap=by_t[j]['now']-by_t[i-1]['now']   # wall-clock distance between the draws that bracket the slot
            (skipped if gap<dur-0.5 else hole).append({'state':q,'slot_ms':dur,'bracket_wall_gap_ms':round(gap,1)})
        if skipped:unjustified+=1;m.setdefault('unjustified_detail',[]).append({'start':st,'seen':seen,'skipped':skipped})
        if hole:slot_in_hole+=1
    m['blinks_unsampled_without_a_stall']=unjustified;m['blinks_unsampled_inside_a_stall']=slot_in_hole
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

def classify_incident(layers):
    """layers: set of independent clocks that showed a hole during one stall incident. W = Worker heartbeat (not blocked by the main thread), T = main-thread setTimeout chain,
    R = requestAnimationFrame chain, D = the idle renderer's own draw log. Returns the attribution sentence used in reports (it names where the stop is, not why)."""
    L=set(layers)
    if L>={'W','T','R'}:return 'process-level freeze (worker heartbeat stopped too): host/CPU starvation or VM pause, not the page'
    if 'T' in L and 'W' not in L:return 'main thread blocked or timers throttled while the worker kept beating'
    if L=={'R'} or L=={'R','D'}:return 'rAF delivery stopped while main-thread timers and worker kept running (frame production)'
    if L=={'D'}:return 'idle renderer did not draw although rAF/timers/worker ran (paused()/eligible/exception)'
    return 'mixed: '+''.join(sorted(L))
def stall_layers(start_ep,end_ep,layer_gaps,slack=300.0):
    """layer_gaps: {'W':[(gap_start_ep,gap_end_ep)],'T':[...],'R':[...]} epoch-ms holes of the independent clocks. Returns the set of layers whose hole overlaps [start_ep,end_ep]."""
    out={'D'}
    for k,v in layer_gaps.items():
        if any(a<=end_ep+slack and b>=start_ep-slack for a,b in v):out.add(k)
    return out
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
