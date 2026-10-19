"""Analyse lou_faint_t18_matrix.py outputs. usage: lou_faint_t18_analyze.py <dir-with-mx_*.json>   (writes <dir>/analysis.json)"""
import json, glob, math, os, sys, collections, statistics as st
d = sys.argv[1]
runs = {os.path.basename(f)[3:-5]: json.load(open(f)) for f in sorted(glob.glob(d + '/mx_*.json'))}
def wilson(w, n, z=1.96):
    if n == 0: return (0, 0)
    p = w / n; den = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / den, (c + h) / den)
def summ(r):
    R = r['results']; n = len(R); w = sum(x['won'] for x in R); lo, hi = wilson(w, n)
    sup = [len(x['heal']) + len(x['bless']) for x in R]
    return dict(n=n, seed=r['seed'], policy=r['policy'], mode=r['mode'], win=w, wipe=n - w, win_rate=round(w / n, 3), ci95=[round(lo, 2), round(hi, 2)],
        rounds=round(sum(x['rounds'] for x in R) / n, 2), wipe_round=round(sum(x['rounds'] for x in R if not x['won']) / max(1, n - w), 1),
        faints=round(sum(len(x['faint']) for x in R) / n, 2), absent_turn_rate=round(sum(x['faintTurns'] for x in R) / max(1, sum(len(x['turns']) for x in R)), 3),
        support=round(sum(sup) / n, 2), final=round(sum(len(x['final']) for x in R) / n, 2), errs=sum(len(x['errs']) for x in R))
out = {k: summ(v) for k, v in runs.items()}
for k, v in out.items(): print(k, v)
def key(x): return (x['won'], x['rounds'], tuple(x['heal']), tuple(x['bless']), tuple(x['final']))
for c in [k for k in runs if k.startswith('ctrl_')]:
    m = c.replace('ctrl_', 'main_')
    if m in runs:
        a = {x['i']: key(x) for x in runs[c]['results']}; b = {x['i']: key(x) for x in runs[m]['results']}
        common = sorted(set(a) & set(b)); diff = [i for i in common if a[i] != b[i]]
        print('CONTROL', c, 'vs', m, 'battles', len(common), 'differing', len(diff), diff[:5]); out['control_' + c] = dict(compared=len(common), differing=len(diff))
def phase3_round(x):
    for r, hp, fhp, boss, f in x['turns']:
        if boss <= 400: return r
    return None
cls = collections.Counter(); detail = []
for k, r in runs.items():
    if not k.startswith('faint_'): continue
    main = runs.get(k.replace('faint_', 'main_')); mm = {x['i']: x for x in main['results']} if main else {}
    for x in r['results']:
        viol = []; F = x['faint']; W = x['wake']; sup = sorted(x['heal'] + x['bless']); wins = []
        for f in F:
            w = next((w for w in W if w > f), None); wins.append((f, w))
            if w is not None and (w - f) not in (2, 3): viol.append('recovery round gap %d (faint R%d wake R%d)' % (w - f, f, w))
            end = w if w is not None else 10**6
            bad = [s for s in sup if f <= s <= end] + [s for s in x['final'] if f <= s < end]  # the pending blessing legitimately fires at the wake round end
            if bad: viol.append('support during faint %s (R%d..%s)' % (bad, f, w))
            if w is not None:
                pass
        # support cadence: between two consecutive support/blessing events (lastSupportRound rule: gap<=3 unless blocked) a gap >3 needs a faint window inside it
        ev = sorted(sup + x['final'])
        for a_, b_ in zip(ev, ev[1:]):
            if b_ - a_ > 3 and not any(f2 < b_ and (next((w2 for w2 in W if w2 > f2), 10**6)) > a_ for f2 in F):
                viol.append('support gap R%d->R%d without a faint window' % (a_, b_))
        if len(x['final']) > 1: viol.append('final blessing x%d' % len(x['final']))
        p3 = phase3_round(x); delay = (x['final'][0] - (p3 - 1)) if (x['final'] and p3 is not None) else None
        mx = mm.get(x['i']); missed = None
        if mx:
            msup = sorted(mx['heal'] + mx['bless'])
            missed = sum(1 for s in msup for f, w in wins if f <= s <= (w if w is not None else 10**6))
        cat = ('win' if x['won'] else 'wipe') + ('/no-faint' if not F else ('/IMPL-ISSUE' if viol else '/faint-consistent'))
        cls[(k, cat)] += 1
        detail.append(dict(run=k, i=x['i'], won=x['won'], faints=F, wakes=W, support=sup, final=x['final'], phase3=p3, final_delay=delay, missed_main_support=missed, violations=viol, rounds=x['rounds']))
print('\nCLASSIFICATION'); [print(k, v) for k, v in sorted(cls.items())]
iss = [t for t in detail if t['violations']]
print('battles with invariant violations:', len(iss)); [print(t) for t in iss[:10]]
dl = [t['final_delay'] for t in detail if t['final_delay'] is not None]
print('final blessing fired in', sum(1 for t in detail if t['final']), 'of', len(detail), 'battles; delay vs Phase3 entry (rounds):', dict(collections.Counter(dl)))
for lab, cond in (('wipe', lambda t: not t['won'] and t['faints']), ('win', lambda t: t['won'] and t['faints'])):
    v = [t['missed_main_support'] for t in detail if cond(t) and t['missed_main_support'] is not None]
    if v: print(lab, 'fainted battles', len(v), 'avg main-run support events falling inside the faint window', round(st.mean(v), 2))
json.dump(dict(summary=out, classification={'%s|%s' % k: v for k, v in cls.items()}, detail=detail), open(os.path.join(d, 'analysis.json'), 'w'), indent=1)
