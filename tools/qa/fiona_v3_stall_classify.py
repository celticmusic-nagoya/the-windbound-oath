"""Classify every STALL of a Fiona idle v3 soak evidence set (the Codex FIX2 QA package, or a new FIONA_EVIDENCE json) on the page's own epoch axis. READ-ONLY on the evidence.
usage: python3 -I fiona_v3_stall_classify.py <evidence_dir_with_soak-N.json> [--lt <soak-N-full-extra.json> ...] [--out DIR]
Per stall: gap, how much of it each independent clock (W worker / T main timer / R rAF) was silent for (union coverage), the longest single hole, the long tasks that overlap it, and the host
counters when the evidence has them. Classes name WHAT is observed, never WHY (see fiona_v3_trace.classify_incident):
  A  single main-thread task spans the stall   - one long task covers >= 90 % of it (main thread occupied or descheduled inside ONE task)
  B  main/frame delay without one long task    - T and R silent >= 70 % but no single long task (the event loop was not scheduled / many shorter tasks); not 'JS ran for seconds'
  C  frame delivery only                       - R silent >= 80 %, T < 50 %
  D  draw log only                             - nothing else silent (would point at the idle renderer itself)  [none expected]
Each row also carries W: 'none' / 'partial' (<50 %) / 'most' (>=50 %); a worker that beat now and then is NOT 'alive', a slowed worker is NOT 'frozen'."""
import json,sys,os,csv,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fiona_v3_trace as S
def classify(g,cov,lt_n,lt_max,lt_known):
    T,R=cov['T']['frac'],cov['R']['frac']
    if lt_known and lt_max>=0.9*g:return 'A'
    if T>=0.7 and R>=0.7:return 'B' if lt_known else 'B?'   # '?' = long-task list incomplete for this time: A cannot be excluded
    if R>=0.8 and T<0.5:return 'C'
    if R<0.5 and T<0.5:return 'D'
    return 'M'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('dir');ap.add_argument('--lt',nargs='*',default=[]);ap.add_argument('--out',default=None);a=ap.parse_args()
    rows=[];D=Path(a.dir)
    for n in (1,2):
        f=D/('soak-%d.json'%n)
        if not f.exists():continue
        s=json.load(open(f));h=s['holes'];to=h['to'];lt=s['long_tasks']
        for e in a.lt:
            if ('soak-%d'%n) in e:lt=json.load(open(e))['lt']
        lt_cap=(len(lt)==200)   # the original evidence json cut the list at 200
        for st in s['metrics']['stalls']:
            a0=st['at_now_ms'];g=st['gap_ms'];e0=to+a0
            cov=S.stall_coverage(e0,e0+g,{k:h[k] for k in 'WTR'})
            ov=[x for x in lt if x[0]<a0+g and x[0]+x[1]>a0];known=not(lt_cap and a0>lt[-1][0])
            c=classify(g,cov,len(ov),max([x[1] for x in ov] or [0]),known)
            wf=cov['W']['frac'];w='none' if wf==0 else ('partial' if wf<0.5 else 'most')
            rows.append({'soak':n,'page_ms':a0,'gap_ms':g,'class':c,'W_cov_pct':round(100*wf),'T_cov_pct':round(100*cov['T']['frac']),'R_cov_pct':round(100*cov['R']['frac']),'W_state':w,'W_max_hole_ms':cov['W']['max_hole_ms'],
              'longtasks_overlapping':len(ov),'longtask_max_ms':max([x[1] for x in ov] or [0]),'longtask_list_complete':known,'pause_evidence':st.get('pause_evidence','none (events=[] in the evidence)')})
    out=Path(a.out) if a.out else None
    if out:
        out.mkdir(parents=True,exist_ok=True)
        with open(out/'stall_classification.csv','w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    from collections import Counter
    print('stalls',len(rows),'by soak',dict(Counter(r['soak'] for r in rows)),'by class',dict(Counter(r['class'] for r in rows)),'W_state',dict(Counter(r['W_state'] for r in rows)))
    print('R>=80%%: %d  T>=70%%: %d  of %d'%(sum(r['R_cov_pct']>=80 for r in rows),sum(r['T_cov_pct']>=70 for r in rows),len(rows)))
    for r in rows:print('%d %7d %7.1f %-3s W%3d T%3d R%3d %-7s Wmax%6.0f LT %d/%4dms %s'%(r['soak'],r['page_ms'],r['gap_ms'],r['class'],r['W_cov_pct'],r['T_cov_pct'],r['R_cov_pct'],r['W_state'],r['W_max_hole_ms'],r['longtasks_overlapping'],r['longtask_max_ms'],'' if r['longtask_list_complete'] else 'LT-list-incomplete'))
main()
