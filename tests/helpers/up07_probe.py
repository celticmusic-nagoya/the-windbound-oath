"""Load explicit, validated QA functions without executing m67's top-level browser run."""
import ast,json,math,re,statistics
from pathlib import Path
from up07_metrics import capture_metrics
NAMES={'settle','go','stop','decoded','transitions','field_check'}
def load_probe(root,output,check):
 source=(Path(root)/'tests/moss/m67_up_production.py').read_text();tree=ast.parse(source);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in NAMES];assert {n.name for n in functions}==NAMES and len(functions)==len(NAMES)
 constants={}
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name) and target.id in {'OBS','STABLE'}:constants[target.id]=ast.literal_eval(node.value)
 assert set(constants)=={'OBS','STABLE'} and all(isinstance(v,str) and len(v)>30 for v in constants.values())
 manifest=json.loads((Path(root)/'img/field/characters/aidan/up5/adopted-walk.json').read_text());ns={'math':math,'re':re,'statistics':statistics,'URLS':[f['path'] for f in manifest['files']],'O':Path(output),'ck':check,'capture_metrics':capture_metrics,**constants}
 exec(compile(ast.Module(body=functions,type_ignores=[]),str(Path(root)/'tests/moss/m67_up_production.py'), 'exec'),ns)
 return ns

def criterion_contract(source):
 tree=ast.parse(source);fs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};f=fs['field_check'];cks=[n for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='ck'];assert len(cks)==3
 assigns={t.id:ast.dump(n.value,include_attributes=False) for n in f.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name) and t.id in {'moving','tr','cycles'}}
 assert set(assigns)=={'moving','tr','cycles'}
 return {'predicates':[ast.dump(c.args[1],include_attributes=False) for c in cks],'measurements':assigns,'decoded':ast.dump(fs['decoded'],include_attributes=False),'transitions':ast.dump(fs['transitions'],include_attributes=False)}
