"""Diagnostic persistence only. Original m67 selectors/assertions remain authoritative."""
import gzip,json,math,statistics,time,os
from pathlib import Path

def stats(values):
 a=sorted(values)
 return {'n':len(a),'min':min(a) if a else None,'median':statistics.median(a) if a else None,'max':max(a) if a else None,'p95':a[min(len(a)-1,int(.95*len(a)))] if a else None}

def write_json(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)

def capture_metrics(output,label,rows,moving,tr,cycles,context):
 """Persist original measurements plus explanatory variables before any assertion."""
 output=Path(output);output.mkdir(parents=True,exist_ok=True);meta=dict(context or {});first=rows[0] if rows else {};last=rows[-1] if rows else {}
 raf=[b['t']-a['t'] for a,b in zip(rows,rows[1:])];steps=[math.hypot(b['x']-a['x'],b['y']-a['y']) for a,b in zip(rows,rows[1:])];extra=[]
 for i,c in enumerate(cycles):
  a,z=tr[i],tr[i+5];part=[r for r in rows if a['t']<=r['t']<=z['t']];deltas=[(p,q) for p,q in zip(part,part[1:])];arc=sum(math.hypot(q['x']-p['x'],q['y']-p['y']) for p,q in deltas);scales=[q.get('frameScale') for p,q in deltas];scaled=sum(s/60 for s in scales) if all(s is not None for s in scales) else None
  extra.append({**c,'start_t_ms':a['t'],'end_t_ms':z['t'],'start_xy':[a['x'],a['y']],'end_xy':[z['x'],z['y']],'arc_world':arc,'effective_clock_seconds_observed':scaled,'clock_nominal_world':scaled*300 if scaled is not None else None,'max_raf_gap_ms':max((q['t']-p['t'] for p,q in deltas),default=None),'heading_change_events':[{'t':r['t'],'heading':r.get('heading')} for j,r in enumerate(part) if j==0 or r.get('heading')!=part[j-1].get('heading')],'samples':len(part)})
 med_d=statistics.median(c['distance'] for c in cycles) if cycles else None;med_t=statistics.median(c['seconds'] for c in cycles) if cycles else None
 flags={'cycle_windows_ge_4':len(cycles)>=4,'median_distance_within_12':med_d is not None and abs(med_d-90)<12,'median_seconds_within_0_08':med_t is not None and abs(med_t-.3)<.08};cadence=all(flags.values())
 result={'label':label,'condition':meta,'sample_start':first,'sample_end':last,'start_t_ms':first.get('t'),'end_t_ms':last.get('t'),'observed_elapsed_seconds':(last['t']-first['t'])/1000 if rows else None,'sample_start_xy':[first.get('x'),first.get('y')],'sample_end_xy':[last.get('x'),last.get('y')],'net_distance_world':math.hypot(last['x']-first['x'],last['y']-first['y']) if rows else None,'path_distance_world':sum(steps),'sampling_count':len(rows),'moving_count':len(moving),'transition_count':len(tr),'cycle_window_count':len(cycles),'frame_set':sorted({r['frame'] for r in tr}),'raf_ms':stats(raf),'raf_gaps_over_50ms':sum(x>50.01 for x in raf),'frame_scale':stats([r['frameScale'] for r in rows if 'frameScale' in r]),'expectation':{'cycle_world':90,'distance_abs_error_strict_lt':12,'cycle_seconds':.3,'seconds_abs_error_strict_lt':.08,'cycle_windows_ge':4},'measured':{'median_cycle_world':med_d,'median_cycle_seconds':med_t},'cadence_predicate_flags':flags,'cadence_pass':cadence,'cadence_reason':'all original conjuncts true' if cadence else ','.join(k for k,v in flags.items() if not v),'cycles':extra,'transition_rows':tr,'source_note':'Original m67 distance is endpoint chord; timestamp is observed RAF wall time. Effective clock/arc are diagnostic only, not alternative PASS criteria.'}
 result['input_elapsed_seconds']=(meta['keyEvents'][-1]['t']-meta['keyEvents'][0]['t'])/1000 if meta.get('keyEvents') else None
 result['observer_cost_ms']=stats([r['observerCostMs'] for r in rows if 'observerCostMs' in r])
 alignment={}
 for lag in [-1,0,1]:
  cases=[]
  for j in range(1,len(rows)):
   k=j+lag
   if not 0<=k<len(rows) or 'frameScale' not in rows[k]:continue
   a,z=rows[j-1],rows[j];dist=math.hypot(z['x']-a['x'],z['y']-a['y'])
   if dist>.001:cases.append({'end_t_ms':z['t'],'actual_world':dist,'expected_uncollided_world':5*rows[k]['frameScale'],'frame_scale':rows[k]['frameScale'],'raf_gap_ms':z['t']-a['t'],'error_world':abs(dist-5*rows[k]['frameScale'])})
  alignment[str(lag)]={'errors_world':stats([c['error_world'] for c in cases]),'long_gap_steps':[c for c in cases if c['raf_gap_ms']>50.01]}
 result['clock_alignment_diagnostic_by_scale_row_offset']=alignment
 # Crash-safe JSON and complete raw data are written before callers can assert.
 write_json(output/'measurement.json',result)
 tmp=output/'raw.json.gz.tmp'
 with gzip.open(tmp,'wb') as f:f.write(json.dumps({'context':meta,'rows':rows},ensure_ascii=False,allow_nan=False).encode())
 os.replace(tmp,output/'raw.json.gz')
 line={'label':label,'samples':len(rows),'transitions':len(tr),'cycles':len(cycles),'median_world':med_d,'median_seconds':med_t,'max_raf_ms':max(raf,default=None),'result':'PASS' if cadence else 'FAIL','reason':result['cadence_reason']}
 with (output/'measurement.log').open('a') as f:f.write(json.dumps(line,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
 print('MEASURE '+json.dumps(line,ensure_ascii=False),flush=True)
 return result
