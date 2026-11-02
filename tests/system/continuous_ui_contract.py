"""Read-only 26C driver integrity and forbidden-itinerary negative controls.

Exact driver hash is independently reviewed, not an editable gameplay fixture.
This test does not launch a browser and never changes product files.
"""
import ast, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DRIVER=ROOT/'tools/qa/continuous_ui.py'
PIN='59b0f34336a86438be00cf863e87fc4a810d6b1f8fed26d078251245673f97fb'
def audit(source):
 if hashlib.sha256(source).hexdigest()!=PIN:raise ValueError('unreviewed driver source')
 tree=ast.parse(source)
 calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='evaluate']
 if len(calls)!=1 or ast.unparse(calls[0].args[0])!='READS[key]':raise ValueError('non-allowlisted evaluation')
sys.path.insert(0,str(DRIVER.parent))
spec=importlib.util.spec_from_file_location('ui_contract_driver',DRIVER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
audit(DRIVER.read_bytes())
for c in [{'op':'observe'},{'op':'walk','x':320,'y':250},{'op':'click','selector':'#msg'},{'op':'cold'},{'op':'key','key':'ArrowUp'}]:m.validate(c)
bad=[{'op':'evaluate','script':'storyStage=15'}, {'op':'teleport','x':1,'y':1}, {'op':'walk','x':1,'y':1,'script':'MossForest.goFeet(1,1)'}, {'op':'click','selector':'#devBtn'}, {'op':'click','selector':'#msg','force':True}, {'op':'key','key':'F12'}, {'op':'save','value':'fake'}, {'op':'wait','seconds':999}]
for c in bad:
 try:m.validate(c)
 except (ValueError,KeyError):pass
 else:raise AssertionError('forbidden itinerary accepted: '+str(c))
faults=['storyStage=15','MossForest.teleportFeet(1,1)','flags.drawer=true','battleItems.potion=99','aahp=999','localStorage.setItem(SAVE_KEY,"fake")','winNormalBattle()','devJump(15)']
for f in faults:
 corrupted=DRIVER.read_bytes().replace(b"localStorage.getItem(SAVE_KEY)",f.encode())
 assert corrupted!=DRIVER.read_bytes()
 try:audit(corrupted)
 except ValueError:pass
 else:raise AssertionError('state-writing observer accepted: '+f)
print(json.dumps({'driver_integrity':'PASS','fixed_observer_call':'PASS','forbidden_commands_detected':len(bad),'state_write_faults_detected':len(faults),'browser_started':False}))
