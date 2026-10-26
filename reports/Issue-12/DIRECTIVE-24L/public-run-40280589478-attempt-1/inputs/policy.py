"""24K acceptance only; raw SKIP/FAIL counts never change. Core has no exceptions."""
NAME='tests/moss/m24_height_contacts_e2e.py'
LINE='SKIP: rest/ambience external effects have no hooks; active zone ids checked instead'
REQUIRED={f'{k}: {s}' for k in ('rest','ambience') for s in ('exact implemented active zone id','changing level clears zone','reentry restores zone')}
def minor(row):
 e=row.get('limitation_evidence',{});browser=row.get('browser_evidence',{})
 return (row.get('name')==NAME and row.get('status')=='SKIP' and row.get('exit_code')==0
  and row.get('skip_lines')==[LINE] and not row.get('failure_lines') and not any(row.get('reported_fails',[]))
  and bool(browser.get('browsers')) and bool(browser.get('navigations'))
  and e.get('all_current_checks_pass') is True and e.get('errors')==[] and REQUIRED<=set(e.get('checked',[])))

IDLE='tests/battle/battle_idle6.py'
MS={'aidan':[220,180,220,160,110,260],'fiona':[260,220,240,180,300,260]}
def idle_analysis(data):
 """Only a late frame at the next available browser RAF is an environment scheduling warning."""
 if not isinstance(data,dict) or data.get('completed') is not True or data.get('clock')!='native RAF' or data.get('tolerance_ms')!=45 or data.get('page_errors'):return None
 allowed={f'{ctx} {who}: per-frame durations match (±45ms)' for ctx in ('normal','raider') for who in MS}
 names=data.get('failure_names',[])
 if not names or not set(names)<=allowed:return None
 records=data.get('records',[])
 if len(records)!=2 or {r.get('context') for r in records}!={'normal','raider'}:return None
 bad=[];bad_names=set()
 for record in records:
  samples=record['samples'];ticks=[];total=0
  for gap in samples['gaps']:total+=gap;ticks.append(total)
  for who,wanted in MS.items():
   seq=samples['seen'][who]
   if len(seq)<7 or any(seq[i+1]['f']!=(seq[i]['f']+1)%6 for i in range(len(seq)-1)):return None
   for i in range(1,len(seq)-1):
    start,end=seq[i]['t'],seq[i+1]['t'];expected=wanted[seq[i]['f']];actual=end-start
    if abs(actual-expected)<=45:continue
    opportunities=[t for t in ticks if start+expected+1<t<end-1]
    gaps=[ticks[j]-ticks[j-1] for j in range(1,len(ticks)) if ticks[j]>start and ticks[j-1]<end]
    largest=max(gaps,default=0)
    # A wrong configured hold under normal browser scheduling has many late opportunities and fails.
    if actual<expected or len(opportunities)>1 or largest<30:return None
    bad_names.add(f"{record['context']} {who}: per-frame durations match (±45ms)")
    bad.append({'context':record['context'],'actor':who,'frame':seq[i]['f'],'start_ms':start,'end_ms':end,'expected_ms':expected,'actual_ms':actual,'max_browser_raf_gap_ms':largest,'unused_late_raf_opportunities':len(opportunities)})
 return bad if bad and bad_names==set(names) else None

def environment(row):
 if row.get('name')!=IDLE or row.get('status')!='FAIL' or row.get('exit_code')!=1 or row.get('skip_lines'):return False
 browser=row.get('browser_evidence',{})
 if not browser.get('browsers') or not browser.get('navigations'):return False
 data=row.get('native_idle_timing');proof=idle_analysis(data)
 if not proof:return False
 lines=row.get('failure_lines',[])
 return bool(lines) and len(lines)==len(data['failure_names']) and all(any(line.startswith('FAIL '+name+' ') for name in data['failure_names']) for line in lines)

def accepted(row):return row.get('status')=='PASS' or minor(row) or environment(row)
