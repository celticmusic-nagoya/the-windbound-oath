#!/usr/bin/env python3
"""Counterfactual evasion comparison on explicit physical-hit traces; never edits game data."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[2]
PLANS = {'conservative': {'p': .10, 'turns': 2, 'mp': 6, 'targets': ['aidan']},
         'standard': {'p': .15, 'turns': 3, 'mp': 10, 'targets': ['aidan', 'fiona']},
         'strong': {'p': .20, 'turns': 3, 'mp': 12, 'targets': ['aidan', 'fiona']}}


def js_round(x):
    return math.floor(x+.5)


def traces(rounds):
    # Fixed exposure: player output is assumed 64/round to choose HP phases ONLY.
    # Enemy targeting alternates in this comparison; no player HP/KO/AI feedback is simulated.
    boss = []; calls = [False, False]; queued = False; adds = []; actions = []
    forest = []
    for r in range(1, rounds+1):
        hp = max(1, 1250-64*r)
        phase = 1 if hp > 820 else 2 if hp > 400 else 3
        target = 'fiona' if r % 2 else 'aidan'
        call = next((i for i, threshold in enumerate((820, 500)) if not calls[i] and hp <= threshold), -1)
        if queued:
            base = 48 if phase == 3 else 42
            boss += [{'round': r, 'target': 'aidan', 'damage': base, 'kind': 'smash'},
                     {'round': r, 'target': 'fiona', 'damage': base-6, 'kind': 'smash'}]
            actions.append({'round': r, 'phase': phase, 'kind': 'smash'}); queued = False
        elif call >= 0:
            calls[call] = True; adds.append({'born':r, 'actions':0})
            actions.append({'round':r, 'phase':phase, 'kind':'summon'})
        elif r % 3 == 0 or (phase == 3 and r % 2 == 0):
            queued = True; actions.append({'round':r, 'phase':phase, 'kind':'queue'})
        else:
            boss.append({'round':r, 'target':target, 'damage':(21 if phase==1 else 27 if phase==2 else 32)+len(adds)*3, 'kind':'attack'})
            actions.append({'round':r, 'phase':phase, 'kind':'attack'})
        for add in adds:
            if add['born'] >= r: continue
            skill = ('supply','burst','frenzy','attack')[add['actions']%4]; add['actions'] += 1
            if skill == 'attack': boss.append({'round':r,'target':target,'damage':8,'kind':'add_attack'})
            elif skill == 'frenzy': boss += [{'round':r,'target':target,'damage':5,'kind':'add_frenzy'} for _ in range(2)]
        # forestGob3: two goblins (6 each), one tainted: burst / frenzy / attack.
        forest += [{'round':r,'target':target,'damage':6,'kind':'goblin'} for _ in range(2)]
        if (r-1)%3 == 1: forest += [{'round':r,'target':target,'damage':5,'kind':'frenzy'} for _ in range(2)]
        elif (r-1)%3 == 2: forest.append({'round':r,'target':target,'damage':8,'kind':'tainted_attack'})
    return {'raider_moss_boss': {'mp_pool':36, 'hits':boss, 'actions':actions},
            'forestGob3_nonboss_reference': {'mp_pool':30, 'hits':forest, 'actions':[]}}


def schedule(plan, rounds, budget):
    casts = []; remaining = budget
    for r in range(1, rounds+1, plan['turns']):
        if remaining < plan['mp']: break
        casts.append(r); remaining -= plan['mp']
    return casts, remaining


def compare(scenario, plan, rounds, trials, seed, guarded=False, lou_def=False):
    casts, mp_left = schedule(plan, rounds, scenario['mp_pool'])
    covered = {r for c in casts for r in range(c, min(rounds+1, c+plan['turns']))}
    rows = []
    for hit in scenario['hits']:
        damage = max(1, js_round(hit['damage']/(1.15 if lou_def else 1)))
        if guarded: damage = math.ceil(damage/2)
        probability = plan['p'] if hit['round'] in covered and hit['target'] in plan['targets'] else 0
        rows.append((damage, probability))
    baseline = sum(d for d, _ in rows)
    analytic = sum(d*(1-p) for d,p in rows)
    eligible = sum(p>0 for _,p in rows)
    expected_evades = sum(p for _,p in rows)
    variance = sum(d*d*p*(1-p) for d,p in rows)
    rng = random.Random(seed); totals=[]; evades=0
    for _ in range(trials):
        total=0
        for damage, probability in rows:
            if probability > 0 and rng.random() < probability: evades += 1
            else: total += damage
        totals.append(total)
    used = scenario['mp_pool']-mp_left
    se = math.sqrt(variance/trials)
    average = statistics.fmean(totals)
    return {'baseline_damage':baseline,'hit_opportunities':len(rows),'eligible_hits':eligible,
            'casts':casts,'mp_spent':used,'mp_left':mp_left,'protected_enemy_phases':len(covered),
            'analytic_damage':round(analytic,4),'analytic_hit_rate':round(1-expected_evades/len(rows),6),
            'damage_saved':round(baseline-analytic,4),'saved_per_mp':round((baseline-analytic)/used,4) if used else 0,
            'sample_mean_damage':round(average,4),'sample_hit_rate':round(1-evades/(trials*len(rows)),6),
            'mean_damage_standard_error':round(se,6),'within_five_standard_errors':abs(average-analytic)<=max(1e-9,5*se),
            'sample_p10_damage':sorted(totals)[int(trials*.10)],'sample_p90_damage':sorted(totals)[int(trials*.90)]}


def verify():
    p=PLANS['standard'];casts,remaining=schedule(p,7,30)
    assert casts==[1,4,7] and remaining==0
    one={'mp_pool':10,'hits':[{'round':1,'target':'aidan','damage':42},{'round':3,'target':'fiona','damage':36},{'round':4,'target':'aidan','damage':42}]}
    result=compare(one,p,4,20000,13)
    assert result['eligible_hits']==2 and result['mp_spent']==10
    assert abs(result['analytic_damage']-(42*.85+36*.85+42))<1e-8
    assert result['within_five_standard_errors']
    zero={**p,'p':0};assert compare(one,zero,4,10,13)['sample_mean_damage']==120
    assert schedule(p,5,9)==([],9)
    # One action per hit, independent two-target smash: exact full-avoid probability p^2, not p.
    assert abs(p['p']**2-.0225)<1e-10
    print('PASS schedule/MP/expiry/no-effect/independent-hit analytic checks')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials',type=int,default=20000)
    parser.add_argument('--rounds',type=int,default=18)
    parser.add_argument('--seed',type=int,default=20261013)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test: verify();return
    if args.trials<100 or not 1<=args.rounds<=100:parser.error('trials>=100 and rounds 1..100 required')
    source=(ROOT/'js/prologue-combat.js').read_text()
    for fragment in ['const base=phase===3?48:42','rbBoss<=[820,500][i]','(phase===1?21:phase===2?27:32)+rbAdds*3']:
        if fragment not in source:raise RuntimeError('Source formula changed; review model: '+fragment)
    result={'source_main':'53180f3','trials':args.trials,'rounds':args.rounds,'seed':args.seed,'plans':PLANS,
            'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['js/prologue-combat.js','js/battle-status.js','js/data/support-magic-data.js','index.html']},
            'model':'fixed damage opportunity trace; not an HP/KO/win-rate battle replay; cast day included; targets alternate; no action/MP/heal/AI feedback', 'scenarios':{}}
    for name,scenario in traces(args.rounds).items():
        result['scenarios'][name]={'mp_pool':scenario['mp_pool'],'trace':scenario,'comparisons':{}}
        for context,guard,lou in [('base',False,False),('guarded',True,False),('lou_def_guarded',True,True)]:
            result['scenarios'][name]['comparisons'][context]={key:compare(scenario,plan,args.rounds,args.trials,args.seed,guard,lou) for key,plan in PLANS.items()}
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('scenario/context/plan | hit rate | expected damage | saved/MP | MP spent | casts | MC mean')
        for name,scenario in result['scenarios'].items():
            for ctx,plans in scenario['comparisons'].items():
                for key,r in plans.items():print(f"{name}/{ctx}/{key} | {r['analytic_hit_rate']:.3%} | {r['analytic_damage']} | {r['saved_per_mp']} | {r['mp_spent']} | {r['casts']} | {r['sample_mean_damage']}")
    if not all(r['within_five_standard_errors'] for s in result['scenarios'].values() for c in s['comparisons'].values() for r in c.values()):raise SystemExit('Simulation differs from analytic expectation >5SE')

if __name__=='__main__':main()
