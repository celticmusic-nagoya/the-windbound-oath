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



def mana_schedule(rounds, initial_mp, enabled=True, recovery=0, condition='hit',
                  valid_rounds=None, hit_rounds=None, maximum=None, heal_rounds=()):
    """One Fiona action per phase; expired dance > requested heal > bolt.

    All-alive fixed horizon, not a battle replay. Invalid selected targets execute
    no attack, but the hypothetical execute-condition credits an attempted bolt:
    that contract is a sensitivity fixture, NOT a claim about current engine.
    """
    if condition not in ('hit', 'execute'): raise ValueError(condition)
    maximum = initial_mp if maximum is None else maximum
    if not 0 <= initial_mp <= maximum: raise ValueError('invalid MP bounds')
    mp = initial_mp; until = 0; ledger = []; casts = []; covered = []
    for phase in range(1, rounds+1):
        before = mp; gain = 0
        if enabled and phase > until and mp >= 10:
            action = 'dance'; mp -= 10; until = phase+2; casts.append(phase)
        elif phase in heal_rounds and mp >= 8:
            action = 'heal'; mp -= 8
        else:
            action = 'bolt'
            valid = valid_rounds is None or phase in valid_rounds
            hit = valid and (hit_rounds is None or phase in hit_rounds)
            if recovery and (condition == 'execute' or hit):
                gain = min(recovery, maximum-mp); mp += gain
        active = enabled and phase <= until
        if active: covered.append(phase)
        ledger.append({'phase':phase, 'action':action, 'mp_before':before,
                       'mp_after':mp, 'recovery':gain, 'dance_active':active})
    return {'casts':casts, 'support_actions':len(casts),
            'heal_actions':sum(x['action']=='heal' for x in ledger),
            'bolt_actions':sum(x['action']=='bolt' for x in ledger),
            'period_end_mp':mp, 'recovered_mp':sum(x['recovery'] for x in ledger),
            'covered_phases':covered, 'ledger':ledger}


def mana_verify():
    assert mana_schedule(7,30)['casts']==[1,4,7]
    r=mana_schedule(18,36,recovery=3)
    assert r['casts']==[1,4,7,10,13,16] and r['period_end_mp']==12
    assert all(0<=x['mp_after']<=36 for x in r['ledger'])
    assert 36-10*r['support_actions']-8*r['heal_actions']+r['recovered_mp']==r['period_end_mp']
    assert r['support_actions']+r['heal_actions']+r['bolt_actions']==18
    assert mana_schedule(18,36,recovery=3,condition='execute')==r
    assert mana_schedule(4,2,enabled=False,recovery=4)['period_end_mp']==2
    assert mana_schedule(4,9,recovery=3,maximum=12)['casts']==[2]
    assert mana_schedule(3,0,recovery=3,maximum=10,hit_rounds=set())['period_end_mp']==0
    assert mana_schedule(3,0,recovery=3,condition='execute',maximum=10,hit_rounds=set())['period_end_mp']==9
    assert mana_schedule(3,0,recovery=3,maximum=10,valid_rounds=set())['period_end_mp']==0
    heal=mana_schedule(3,16,enabled=False,heal_rounds=(1,2,3))
    assert heal['heal_actions']==2 and heal['bolt_actions']==1
    print('PASS mana budget/cap/expiry/one-action/condition/heal fixture checks')


def mana_results(rounds):
    source=(ROOT/'js/prologue-combat.js').read_text()
    if 'if(!e||e.hp<=0)' not in source or 'BattleCritical.resolve(a,n)' not in source:
        raise RuntimeError('Review normal-attack execution contract')
    output={'source_main':'e694817', 'rounds':rounds,
            'dance':{'evasion_points':15,'duration_enemy_phases':3,'mp':10,
                     'targets':'all alive allies','stacking':'refresh only'},
            'bolt_hit_probability_valid_living_target':1.0,
            'source_hashes':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                             for f in ('js/prologue-combat.js','js/battle-critical.js')},
            'policy':'all allies alive; dance when expired and affordable, else bolt; no heals; one Fiona action per phase; fixed trace unaffected by outgoing damage',
            'unavailable':{'battle_end_mp':'only fixed-horizon MP available',
                           'kill_turn':'no outgoing damage/HP feedback',
                           'win_rate':'no ally HP/KO/heal/target feedback'},
            'scenarios':{}}
    for name, trace in traces(rounds).items():
        budget=trace['mp_pool']; conditions={}
        configs=[('no_dance',False,0,'hit'),('dance_no_recovery',True,0,'hit')]
        configs += [(f'dance_{condition}_{gain}',True,gain,condition)
                    for gain in (2,3,4) for condition in ('hit','execute')]
        for key,enabled,gain,condition in configs:
            r=mana_schedule(rounds,budget,enabled,gain,condition)
            covered=set(r['covered_phases']); baseline=sum(x['damage'] for x in trace['hits'])
            saved=sum(x['damage']*.15 for x in trace['hits'] if x['round'] in covered)
            r.update({'fixed_trace_baseline_damage':baseline,
                      'fixed_trace_expected_damage':round(baseline-saved,4),
                      'fixed_trace_expected_saved':round(saved,4),
                      'kill_turn':None,'win_rate':None,'battle_end_mp':None})
            conditions[key]=r
        output['scenarios'][name]={'initial_mp_and_cap':budget,'conditions':conditions}
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials',type=int,default=20000)
    parser.add_argument('--rounds',type=int,default=18)
    parser.add_argument('--seed',type=int,default=20261013)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--mana-json',action='store_true',help='fixed-policy mana ledger; no game changes')
    args=parser.parse_args()
    if args.self_test: verify();mana_verify();return
    if args.trials<100 or not 1<=args.rounds<=100:parser.error('trials>=100 and rounds 1..100 required')
    if args.mana_json:
        print(json.dumps(mana_results(args.rounds),ensure_ascii=False,indent=2));return
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
