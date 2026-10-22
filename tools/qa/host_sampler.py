"""Host-side sampler for stall investigations (diagnostic only; touches no game file). A background thread records, every `interval` seconds on the wall clock (epoch ms, the same axis as the page's
performance.timeOrigin+performance.now()): its own wake-up delay (dt - interval), loadavg, /proc/stat cpu steal+iowait deltas, PSI (cpu/io/memory 'some' avg10 and the cumulative total, if the kernel has them),
cgroup v2 cpu.stat (nr_throttled, throttled_usec), cpu.max, memory.events/memory.current, and the context-switch counters of every chrom* process. Every source is optional: a missing file is recorded as None and never stops the thread
(the first Codex run lost its host samples because /proc/pressure/cpu did not exist). What decides a stall's cause is a counter that moves INSIDE the stall window: throttled_usec (quota), PSI total (contention), steal (VM),
involuntary context switches of the renderer (preemption) versus voluntary ones (the thread waiting by itself)."""
import os,time,threading
def _read(p):
    try:
        with open(p) as f:return f.read()
    except Exception:return None
def _kv(s):
    out={}
    for l in (s or '').splitlines():
        p=l.split()
        if len(p)>=2:
            try:out[p[0]]=int(p[1])
            except ValueError:pass
    return out
def _psi(name):
    s=_read('/proc/pressure/'+name)
    if not s:return None
    r={}
    for l in s.splitlines():
        p=l.split();d=dict(x.split('=') for x in p[1:])
        r[p[0]]={'avg10':float(d.get('avg10',0)),'total_us':int(d.get('total',0))}
    return r
def _cgroup():
    base='/sys/fs/cgroup/'
    cs=_kv(_read(base+'cpu.stat'));me=_kv(_read(base+'memory.events'))
    cur=_read(base+'memory.current');cm=_read(base+'cpu.max')
    return {'nr_throttled':cs.get('nr_throttled'),'throttled_usec':cs.get('throttled_usec'),'nr_periods':cs.get('nr_periods'),'cpu_max':cm.strip() if cm else None,
            'mem_current':int(cur) if cur and cur.strip().isdigit() else None,'mem_high':me.get('high'),'mem_oom':me.get('oom')}
def _procs():
    vol=invol=n=0
    try:
        for d in os.listdir('/proc'):
            if not d.isdigit():continue
            c=_read('/proc/%s/comm'%d)
            if not c or not c.startswith('chrom'):continue
            s=_read('/proc/%s/status'%d)
            if not s:continue
            k=_kv(s.replace(':',' '));vol+=k.get('voluntary_ctxt_switches',0);invol+=k.get('nonvoluntary_ctxt_switches',0);n+=1
    except Exception:pass
    return {'procs':n,'vol_ctxt':vol,'invol_ctxt':invol}
def _stat():
    s=_read('/proc/stat')
    if not s:return None
    v=list(map(int,s.splitlines()[0].split()[1:]));return {'total':sum(v),'iowait':v[4] if len(v)>4 else 0,'steal':v[7] if len(v)>7 else 0}
class HostSampler:
    def __init__(self,interval=0.25):
        self.interval=interval;self.rows=[];self._stop=threading.Event();self._th=threading.Thread(target=self._run,daemon=True)
    def start(self):self._th.start();return self
    def _run(self):
        last=time.time()
        while not self._stop.is_set():
            if self._stop.wait(self.interval):break
            now=time.time()
            try:
                row={'ep_ms':round(now*1000,1),'wake_delay_ms':round((now-last-self.interval)*1000,1),'load':os.getloadavg(),'stat':_stat(),
                     'psi':{n:_psi(n) for n in ('cpu','io','memory')},'cg':_cgroup(),**_procs()}
            except Exception as e:row={'ep_ms':round(now*1000,1),'err':repr(e)}
            self.rows.append(row);last=now
    def stop(self):
        self._stop.set();self._th.join(timeout=5);return self.rows
def window_summary(rows,start_ep,end_ep,pad_ms=1000.0):
    """What the host counters did while a stall lasted: deltas between the last sample before and the first after the window, plus the worst sampler wake-up delay inside it."""
    inw=[r for r in rows if start_ep-pad_ms<=r['ep_ms']<=end_ep+pad_ms and 'err' not in r]
    if len(inw)<2:return {'samples':len(inw),'note':'no host samples cover this window (UNKNOWN)'}
    a,b=inw[0],inw[-1];d=lambda k,s:(None if (a.get(s) or {}).get(k) is None or (b.get(s) or {}).get(k) is None else b[s][k]-a[s][k])
    out={'samples':len(inw),'max_sampler_wake_delay_ms':max(r['wake_delay_ms'] for r in inw),'d_vol_ctxt':b['vol_ctxt']-a['vol_ctxt'],'d_invol_ctxt':b['invol_ctxt']-a['invol_ctxt'],
         'd_nr_throttled':d('nr_throttled','cg'),'d_throttled_usec':d('throttled_usec','cg'),'d_steal_ticks':d('steal','stat'),'d_iowait_ticks':d('iowait','stat'),'d_mem_high_events':d('mem_high','cg')}
    for n in ('cpu','io','memory'):
        pa=(a['psi'].get(n) or {}).get('some');pb=(b['psi'].get(n) or {}).get('some')
        out['d_psi_%s_some_us'%n]=None if not pa or not pb else pb['total_us']-pa['total_us']
    return out
