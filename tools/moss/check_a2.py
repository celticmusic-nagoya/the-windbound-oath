#!/usr/bin/env python3
"""A2 structural checks: reachability and sealing. usage: check_a2.py <a2_design.json>"""
import json,sys,os
sys.path.insert(0,os.path.dirname(__file__)); import mf_lib as L
m=json.load(open(sys.argv[1],encoding='utf-8')); m['_routes']={p['id']:[tuple(q) for q in p['points']] for p in m['terrain']['paths']}
def run(label,mutate=None):
    mm=json.loads(json.dumps(m))
    if mutate: mutate(mm)
    H=L.Hash(L.compile_collision(mm)); sp=mm['spawns']['points']['from_area1']
    ok,n=L.reach(mm,H,(sp['x'],sp['y']))
    return mm,ok,n
mm,ok,n=run('base'); bad=0
def chk(name,p,want=True):
    global bad
    r=ok(p)==want; bad+=not r; print(('ok  ' if r else 'FAIL'),name,'reachable' if want else 'NOT reachable')
for k,p in m['_routes'].items(): chk('end of '+k,p[-1])
for t in m['treasurePoints']: chk(t['id'],(t['x'],t['y']))
for t in m['transitions']:
    r=t['rect']; chk(t['id'],(r['x']+r['w']/2,r['y']+max(r['h'],1)/2 if r['y']>0 else 20))
for k,s in m['spawns']['points'].items(): chk('spawn '+k,(s['x'],s['y']))
for z in m['eventZones']:
    if z['type']=='rest': r=z['shape']; chk(z['id'],(r['x']+r['w']/2,r['y']+r['h']/2))
chk('inside north cliff face',(500,3395),False); chk('inside south cliff band',(2000,5100),False)
chk('pool deep core',(1100,3790),False); chk('waterfall',(1150,3400),False)
# sealing: remove the log channel -> the waterfall ledge must be unreachable
def seal(mm):
    mm['collision']['blockers'].append({'id':'t_chan','tag':'t','shape':'rect','x':1157,'y':3675,'w':72,'h':230})
_,ok2,_=run('sealed',seal); r=not ok2((1140,3545)); bad+=not r; print(('ok  ' if r else 'FAIL'),'ledge unreachable without the log channel')
print('failures',bad); sys.exit(1 if bad else 0)
