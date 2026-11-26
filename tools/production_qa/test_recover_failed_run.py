import copy, json, subprocess, tempfile, pathlib, unittest
from recover_failed_run import recover, Hold, ROUTES, REPO, RID, BOT, OWNER, ref_for

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.run=123; self.req=456; self.rev='a'*40; self.token='b'*40; self.ref=ref_for('MORWEN')
        self.route=ROUTES[424712879]; r=self.route; base='repos/'+REPO
        self.runpath=f'{base}/actions/runs/{self.run}'
        self.jobpath=self.runpath+'/attempts/1/jobs?per_page=100'
        self.refpath=base+'/git/matching-refs/'+self.ref[5:]
        self.tagpath=base+'/git/tags/'+self.token
        self.data={self.runpath:dict(id=self.run,workflow_id=424712879,run_attempt=1,status='completed',conclusion='failure',head_branch='main',event='workflow_dispatch',path=r['path'],repository={'id':RID},head_repository={'id':RID},actor={'id':BOT},head_sha=self.rev,display_title=f'Morwen VRoid / vrm_export request:{self.req}'),
            f'{base}/contents/{r["path"]}?ref={self.rev}':{'sha':r['blob']},
            f'{base}/issues/comments/{self.req}':dict(id=self.req,user={'id':OWNER},author_association='OWNER',created_at='x',updated_at='x',issue_url=f'https://api.github.com/{base}/issues/427',body='/two-morwen-launch vrm_export main='+self.rev),
            self.jobpath:dict(total_count=4,jobs=[dict(name=r['job'],status='completed',conclusion='failure',run_id=self.run,steps=[dict(name=n,status='completed',conclusion='skipped') for n in r['skipped_steps']])]+[dict(name=n,status='completed',conclusion='skipped',run_id=self.run) for n in r['skipped_jobs']]),
            self.refpath:[dict(ref=self.ref,object=dict(type='tag',sha=self.token))],
            self.tagpath:dict(sha=self.token,object=dict(type='commit',sha=self.rev),message=json.dumps(dict(schema=r['schema'],asset='MORWEN',revision=self.rev,request=str(self.req),run=str(self.run),attempt='1',reservation='c'*40,nonce='d'*32)))}
        self.refs={self.ref:self.token,ref_for('OTHER'):'e'*40}; self.calls=[]
    def api(self,path): return copy.deepcopy(self.data[path])
    def delete(self,asset,token):
        self.calls.append((asset,token)); ref=ref_for(asset)
        if self.refs.get(ref)!=token: raise RuntimeError('CAS mismatch')
        del self.refs[ref]
    def invoke(self, apply=True): return recover(self.api,self.refs.get,self.delete,self.run,apply)
    def test_release_only_matching(self):
        self.assertEqual(self.invoke()['status'],'RELEASED'); self.assertEqual(self.refs,{ref_for('OTHER'):'e'*40})
    def test_dry_run(self): self.assertEqual(self.invoke(False)['status'],'DRY_RUN_ELIGIBLE'); self.assertFalse(self.calls)
    def test_absent(self): self.data[self.refpath]=[]; self.assertEqual(self.invoke()['status'],'NO_LEASE_API'); self.assertFalse(self.calls)
    def test_active(self): self.data[self.runpath]['status']='in_progress'; self.assertRaises(Hold,self.invoke); self.assertFalse(self.calls)
    def test_rerun(self): self.data[self.runpath]['run_attempt']=2; self.assertRaises(Hold,self.invoke)
    def test_fork(self): self.data[self.runpath]['head_repository']['id']=99; self.assertRaises(Hold,self.invoke)
    def test_unknown_worker(self): self.data[f'repos/{REPO}/contents/{self.route["path"]}?ref={self.rev}']['sha']='0'*40; self.assertRaises(Hold,self.invoke)
    def test_restore_ran(self): self.data[self.jobpath]['jobs'][0]['steps'][0]['conclusion']='success'; self.assertRaises(Hold,self.invoke)
    def test_later_job(self): self.data[self.jobpath]['jobs'][2]['conclusion']='success'; self.assertRaises(Hold,self.invoke)
    def test_missing_step(self): self.data[self.jobpath]['jobs'][0]['steps'].pop(); self.assertRaises(Hold,self.invoke)
    def test_missing_job(self): self.data[self.jobpath]['jobs'].pop(); self.assertRaises(Hold,self.invoke)
    def test_stale_run(self): body=json.loads(self.data[self.tagpath]['message']); body['run']='999'; self.data[self.tagpath]['message']=json.dumps(body); self.assertRaises(Hold,self.invoke)
    def test_changed_token(self): self.refs[self.ref]='f'*40; self.assertRaises(Hold,self.invoke); self.assertFalse(self.calls)
    def test_race_after_preflight(self):
        def race(a,t): self.refs[self.ref]='f'*40; self.delete(a,t)
        self.assertRaises(RuntimeError,recover,self.api,self.refs.get,race,self.run,True); self.assertEqual(self.refs[self.ref],'f'*40)
    def test_readback_failure(self): self.assertRaises(Hold,recover,self.api,self.refs.get,lambda a,t:None,self.run,True)
    def test_success_not_release(self): self.data[self.runpath]['conclusion']='success'; self.assertRaises(Hold,self.invoke)
    def test_cancellation(self): self.data[self.runpath]['conclusion']='cancelled'; self.data[self.jobpath]['jobs'][0]['conclusion']='cancelled'; self.assertEqual(self.invoke()['status'],'RELEASED')

if __name__=='__main__': unittest.main(verbosity=2)
