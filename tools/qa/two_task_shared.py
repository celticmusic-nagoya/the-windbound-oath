"""Shared GitHub Contents CAS queue candidate. State branch must be non-main.
No automatic recovery of running tasks: require verified termination externally.
"""
import base64
import json
import re
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def transition(state, key, operation, owner):
    if not re.fullmatch('[0-9a-f]{64}', key) or not owner or not isinstance(owner, str):
        raise ValueError('invalid task or owner')
    if state.get('schema') != 'two.shared-queue.v1' or type(state.get('revision')) is not int or not isinstance(state.get('tasks'), dict):
        raise ValueError('invalid queue state')
    state = json.loads(json.dumps(state))
    tasks = state['tasks']
    task = tasks.get(key)
    if operation == 'enqueue' and task is None:
        tasks[key] = {'state':'READY', 'owner':None}
    elif operation == 'claim' and task and task['state'] == 'READY':
        first = next(k for k,v in tasks.items() if v['state'] == 'READY')
        if first != key:
            return None
        task.update(state='RUNNING', owner=owner)
    elif operation in ('done','block') and task and task['state']=='RUNNING' and task['owner']==owner:
        task['state'] = 'DONE' if operation=='done' else 'BLOCKED'
    else:
        return None
    state['revision'] += 1
    return state

class GitHubStore:
    def __init__(self, repository, branch, token):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or branch != 'feature/nightly-automation-setup-01' or not token:
            raise ValueError('unsupported repository, branch or credentials')
        self.url = 'https://api.github.com/repos/'+repository+'/contents/tools/qa/shared-task-state.json'
        self.branch, self.token = branch, token
    def request(self, method, url, payload=None):
        req = Request(url, data=None if payload is None else json.dumps(payload).encode(), method=method, headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
        with urlopen(req, timeout=20) as res:
            return json.load(res)
    def apply(self, key, operation, owner):
        from urllib.parse import quote
        current = self.request('GET', self.url+'?ref='+quote(self.branch,safe=''))
        state = json.loads(base64.b64decode(current['content']))
        new = transition(state,key,operation,owner)
        if new is None:
            return 'NO_CHANGE'
        try:
            self.request('PUT', self.url, {'branch':self.branch,'sha':current['sha'],'message':'Update production queue revision '+str(new['revision']),'content':base64.b64encode(json.dumps(new,separators=(',',':')).encode()).decode()})
        except HTTPError as exc:
            if exc.code in (409,422):
                return 'CONFLICT_REVIEW'
            raise
        return 'COMMITTED'

class Tests(unittest.TestCase):
    def test_order_and_ownership(self):
        s = {'schema':'two.shared-queue.v1','revision':0,'tasks':{}}
        a,b='a'*64,'b'*64
        s=transition(s,a,'enqueue','one')
        s=transition(s,b,'enqueue','two')
        self.assertIsNone(transition(s,b,'claim','two'))
        s=transition(s,a,'claim','one')
        self.assertIsNone(transition(s,a,'claim','two'))
        self.assertIsNone(transition(s,a,'done','two'))
        s=transition(s,a,'done','one')
        self.assertEqual(s['revision'],4)
        self.assertIsNone(transition(s,a,'enqueue','one'))
    def test_conflict(self):
        from unittest.mock import Mock
        store=GitHubStore('owner/repo','feature/nightly-automation-setup-01','test')
        state={'schema':'two.shared-queue.v1','revision':0,'tasks':{}}
        store.request=Mock(side_effect=[{'sha':'old','content':base64.b64encode(json.dumps(state).encode())},HTTPError('https://api.github.com',409,'conflict',{},None)])
        self.assertEqual(store.apply('a'*64,'enqueue','one'),'CONFLICT_REVIEW')
        self.assertEqual(store.request.call_count,2)
        self.assertEqual(store.request.call_args.args[2]['sha'],'old')
    def test_main_denied(self):
        with self.assertRaises(ValueError):
            GitHubStore('owner/repo','main','test')

if __name__=='__main__':
    unittest.main()
