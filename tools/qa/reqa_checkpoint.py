"""Read-only pre-assert checkpoints for existing QA functions; no predicate rewrites."""
import ast,copy,datetime,gzip,hashlib,inspect,json,math,os,time,traceback
from pathlib import Path
SELECT={'rows','moving','tr','trans','transitions','cycles','origin','feet','before','after','up','preview','start','end','raw','record','m','inventory','stable','storage','failed','errors','view','label','width','height','w','h','direction','actor','group','index','frame','tail','bob_error','rate','elapsed','expected','want','urls','URLS','M','KEYS','LOCK','OTHER_LOCK','PR91','locked','ledger','entries','counts','repl','replacement'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def safe(value,depth=0):
 if value is None or isinstance(value,(str,int,bool)):return value
 if isinstance(value,float):return value if math.isfinite(value) else {'nonfinite':str(value)}
 if depth>14:return {'not_serialized':'depth limit'}
 if isinstance(value,(list,tuple)):return [safe(v,depth+1) for v in value]
 if isinstance(value,dict):return {str(k):safe(v,depth+1) for k,v in value.items()}
 return {'not_serialized':type(value).__name__}
def params(values):
 boolkey=next((x for x in ['ok','v'] if x in values),None);namekey=next((x for x in ['name','n','label'] if x in values),None)
 if boolkey is None or namekey is None:raise RuntimeError('Unsupported original check signature')
 return str(values[namekey]),bool(values[boolkey])
def instrument(source,filename):
 tree=ast.parse(source,filename);original=ast.dump(tree,include_attributes=False);calls={}
 for n in ast.walk(tree):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'ck','check'}:calls.setdefault(n.lineno,[]).append(ast.get_source_segment(source,n))
 modified=copy.deepcopy(tree);count=0
 for n in ast.walk(modified):
  if not isinstance(n,ast.FunctionDef) or n.name not in {'ck','check'}:continue
  names=[a.arg for a in n.args.args];bk=next((x for x in ['ok','v'] if x in names),None);nk=next((x for x in ['name','n','label'] if x in names),None)
  if not bk or not nk:raise RuntimeError('Unsupported check signature '+n.name)
  count+=1;n.body.insert(0,ast.parse('__reqa_checkpoint(locals(), globals())').body[0])
  if not any(isinstance(x,ast.Assert) for x in ast.walk(n)):
   n.body.append(ast.If(test=ast.UnaryOp(op=ast.Not(),operand=ast.Name(id=bk,ctx=ast.Load())),body=[ast.Raise(exc=ast.Call(func=ast.Name(id='AssertionError',ctx=ast.Load()),args=[ast.Name(id=nk,ctx=ast.Load())],keywords=[]),cause=None)],orelse=[]));n._reqa_end_guard=True
 if count!=1:raise RuntimeError('Expected exactly one original check function, got '+str(count))
 for n in ast.walk(modified):
  if isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Call) and isinstance(i.context_expr.func,ast.Name) and i.context_expr.func.id=='sync_playwright' for i in n.items):
   handler=ast.ExceptHandler(type=None,name=None,body=ast.parse('__reqa_unhandled(locals(), globals())\nraise').body);n.body=[ast.Try(body=n.body,handlers=[handler],orelse=[],finalbody=[])];n._reqa_exception_guard=True
 proof=copy.deepcopy(modified)
 for n in ast.walk(proof):
  if isinstance(n,ast.With) and getattr(n,'_reqa_exception_guard',False):n.body=n.body[0].body
  if isinstance(n,ast.FunctionDef) and n.name in {'ck','check'}:
   n.body.pop(0)
   if getattr(n,'_reqa_end_guard',False):n.body.pop()
 if ast.dump(proof,include_attributes=False)!=original:raise RuntimeError('Original predicate/body altered')
 return compile(ast.fix_missing_locations(modified),filename,'exec'),calls
class Recorder:
 def __init__(self,out,calls,test):
  self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True);self.calls=calls;self.test=test;self.index=0;self.started=time.monotonic();self.previous_utc=now();self.failures=[]
 def unhandled(self,args,namespace):
  self({'name':'unhandled original exception: '+traceback.format_exc(),'ok':False},namespace,inspect.currentframe().f_back)
 def __call__(self,args,namespace,frame=None):
  self.index+=1;name,passed=params(args);caller=frame or inspect.currentframe().f_back.f_back;values={**caller.f_globals,**caller.f_locals};context={}
  for key in SELECT:
   if key not in values:continue
   value=values[key]
   if key=='rows' and isinstance(value,list) and value and isinstance(value[0],dict) and not any('t' in x or 'x' in x for x in value[:3]):context['rows_history_count']=len(value);continue
   context[key]=safe(value)
  blob=json.dumps(context,ensure_ascii=False,allow_nan=False).encode();sha=hashlib.sha256(blob).hexdigest();p=self.out/'contexts'/f'{sha}.json.gz';p.parent.mkdir(exist_ok=True)
  if not p.exists():
   with gzip.open(p,'wb') as f:f.write(blob)
  trace=next(((key,value) for key in ['rows','moving','up','preview','transitions','trans','tr'] if isinstance((value:=values.get(key)),list) and len(value)>1 and all(isinstance(x,dict) and isinstance(x.get('t'),(float,int)) for x in value)),None)
  movement={'start_coordinates':None,'end_coordinates':None,'distance_world':None,'sample_count':None,'raf_intervals_ms':None,'reason':'Not a sampled movement interval; static/UI/unit predicate. Retained context is not relabelled as current movement.'}
  if trace:
   key,a=trace;movement.update(source_variable=key,provenance='retained caller trace; NOT guaranteed to describe this current predicate; movement fields N/A unless confirmed by primary per-route metrics',sample_count=len(a),start_t_ms=a[0]['t'],end_t_ms=a[-1]['t'],elapsed_seconds=(a[-1]['t']-a[0]['t'])/1000,raf_intervals_ms=[z['t']-b['t'] for b,z in zip(a,a[1:])],reason=None)
   if all('x' in x and 'y' in x for x in [a[0],a[-1]]):movement.update(start_coordinates=[a[0]['x'],a[0]['y']],end_coordinates=[a[-1]['x'],a[-1]['y']],distance_world=math.hypot(a[-1]['x']-a[0]['x'],a[-1]['y']-a[0]['y']))
  live={'capture':'not requested on passing assertion; no extra browser work inside timed checks'}
  if not passed:
   page=next((values.get(k) for k in ['p','pg'] if callable(getattr(values.get(k),'evaluate',None))),None)
   if page is None:live={'capture':'N/A','reason':'No live browser in this check'}
   else:
    try:
     if page.is_closed():live={'capture':'N/A','reason':'page already closed'}
     else:
      expressions={k:v for k in ['STABLE','PROTECTED','SAVE'] if isinstance((v:=namespace.get(k)),str) and v.startswith('JSON.stringify(')}
      expr='()=>({t:performance.now(),timeOrigin:performance.timeOrigin,feet:window.MossForest?.feet||null,map:window.MossForest?.mapId||null,active:!!window.MossForest?.active,observer:window.__up07?{start:__up07.start,end:__up07.end,rows:__up07.rows,keyEvents:__up07.keyEvents,longTasks:__up07.longTasks}:null,input:window.InputManager?.state?.(),save:typeof SAVE_KEY===\"string\"?localStorage.getItem(SAVE_KEY):null,comparisons:{'+','.join(json.dumps(k)+':('+v+')' for k,v in expressions.items())+'}})';live={'capture':'read-only failure snapshot','values':page.evaluate(expr)}
      raw_live=json.dumps(safe(live['values']),ensure_ascii=False,allow_nan=False).encode();live_file=self.out/f'failure-browser-{self.index:04}.json.gz'
      with gzip.open(live_file,'wb') as f:f.write(raw_live)
      live={'capture':'read-only failure snapshot','file':live_file.name,'sha256':hashlib.sha256(raw_live).hexdigest(),'feet':live['values'].get('feet'),'map':live['values'].get('map')}
    except Exception as e:live={'capture':'ERROR','error':str(e)}
  ended=now();entry={'index':self.index,'test':self.test,'name':name,'start_utc':self.previous_utc,'end_utc':ended,'elapsed_from_test_start_seconds':time.monotonic()-self.started,'expected_original_call':self.calls.get(caller.f_lineno,['see source line '+str(caller.f_lineno)]),'callsite_note':'All original call candidates on this source line; computed result/name are exact, expression association may be ambiguous for multiple calls.','source_line':caller.f_lineno,'computed_result':passed,'verdict':'PASS' if passed else 'FAIL','reason':'Original computed predicate true' if passed else 'Original computed predicate false; stop without changing it','context_file':str(p.relative_to(self.out)),'context_sha256':sha,'movement_or_explicit_NA':movement,'failure_snapshot':live}
  entry=safe(entry)
  with (self.out/'checkpoints.jsonl').open('a') as f:f.write(json.dumps(entry,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
  self.previous_utc=ended
  if not passed:
   self.failures.append(entry)
   if len(self.failures)==1:atomic(self.out/'failure.json',entry)
   else:atomic(self.out/f'failure-{self.index:04}.json',entry)
