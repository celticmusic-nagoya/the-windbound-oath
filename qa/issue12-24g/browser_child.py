"""Transport/telemetry adapters only. Executes unchanged product tests."""
import atexit,json,os,runpy,sys,traceback,importlib.util
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from playwright.sync_api import BrowserType,Page
root=Path(sys.argv[1]);name=sys.argv[2];port=int(sys.argv[3]);extra=json.loads(sys.argv[4]);target=Path(os.environ['BROWSER_EVIDENCE']);evidence={'browsers':[],'navigations':[]}
def save():target.write_text(json.dumps(evidence,indent=2)+'\n')
atexit.register(save);launch=BrowserType.launch;goto=Page.goto

def actual_launch(self,*args,**kwargs):
 if self.name=='chromium':kwargs.setdefault('executable_path',os.environ['PW_CHROMIUM_EXECUTABLE'])
 browser=launch(self,*args,**kwargs);evidence['browsers'].append({'type':self.name,'version':browser.version});save();return browser

def actual_goto(self,url,*args,**kwargs):
 parts=urlsplit(url)
 if parts.hostname in ('localhost','127.0.0.1') and parts.port==8765:url=urlunsplit((parts.scheme,'127.0.0.1:'+str(port),parts.path,parts.query,parts.fragment))
 result=goto(self,url,*args,**kwargs);evidence['navigations'].append({'url':url,'status':result.status if result else None});save();return result
BrowserType.launch=actual_launch;Page.goto=actual_goto
os.chdir(root);sys.argv=[str(root/name)]+extra;sys.path.insert(0,str((root/name).parent));sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('product_qa_runner',root/'tools/qa/run_regressions.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.child(root,name,port,extra)
