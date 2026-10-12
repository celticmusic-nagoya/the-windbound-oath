#!/usr/bin/env python3
"""Direct public-API planner benchmark. Start a root http.server first.

PORT=8765 PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python3 tests/moss/m19_plan_bench.py
No runtime source, maps, saves or planner internals are modified. Outputs raw
JSON and a Markdown table. This measures planning, not walking/Android FPS.
"""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HEIGHT_ROUTES = [
    ('height_near', '低地・近距離', [300, 1250, 0], [500, 1250, 0]),
    ('height_bridge', '低地→橋の上', [300, 1250, 0], [1560, 600, 1]),
    ('height_plateau', '低地→高台', [300, 1250, 0], [2000, 250, 1]),
    ('height_down', '高台→低地', [2000, 250, 1], [300, 1250, 0]),
    ('height_under', '橋の下・横断', [1450, 900, 0], [1700, 900, 0]),
]
TWO_D_ROUTES = [
    ('2d_near', '2D・近距離', [7600, 5625, 0], [7580, 5425, 0]),
    ('2d_mid', '2D・中距離', [8400, 6925, 0], [7800, 5792, 0]),
    ('2d_far', '2D・遠距離', [8200, 6125, 0], [6845, 4667, 0]),
]
# Coordinates in the request are feet; public movement/planner APIs take actor
# top-left = feet - (17,42). Level is explicit, never inferred from XY.
MEASURE = """({kind,start,goal,repeats})=>{
  const a={x:start[0]-17,y:start[1]-42},b={x:goal[0]-17,y:goal[1]-42,level:goal[2]};
  const samples=[], map=MossForest.map;
  if(kind==='height'){
    const h=MossForest.height;
    if(!h||h.blockedAtLevel(a.x,a.y,start[2])||h.blockedAtLevel(b.x,b.y,goal[2]))throw new Error('Invalid height route endpoint');
    const old=h.level;
    try {
      for(let i=-1;i<repeats;i++){
        h.setLevel(start[2]);const t=performance.now();
        const r=h.plan(a,b,{grid:32,maxNodes:60000,width:map.world.width,height:map.world.height});
        const elapsed=performance.now()-t;
        if(i>=0)samples.push({iteration:i+1,wall_ms:elapsed,reported_ms:r.ms,expanded:r.expanded,
          success:Array.isArray(r.path)&&r.path.length>0&&r.path[r.path.length-1].level===goal[2]&&Math.hypot(r.path[r.path.length-1].x-b.x,r.path[r.path.length-1].y-b.y)<1e-6,path_vertices:r.path?r.path.length:0,
          final_level:r.path&&r.path.length?r.path[r.path.length-1].level:null});
      }
    } finally {h.setLevel(old);}
  }else{
    const blocked=MossForest.forest.blocked;
    if(blocked(a.x,a.y)||blocked(b.x,b.y))throw new Error('Invalid 2D route endpoint');
    try {
      for(let i=-1;i<repeats;i++){
        const t=performance.now(),target=FieldNavigation.destination(b.x,b.y,blocked);
        const moved=target?FieldNavigation.follow(a.x,a.y,target,blocked):null;
        const elapsed=performance.now()-t,st=FieldNavigation.status;
        if(i>=0)samples.push({iteration:i+1,wall_ms:elapsed,reported_ms:st.milliseconds,expanded:st.expanded,
          success:!!target&&!!moved&&!moved.unreachable&&['moving','arrived'].includes(st.outcome),
          planner_calls:st.plans,outcome:st.outcome});
      }
    }finally {FieldNavigation.cancel();}
  }
  return samples;
}"""


def summarize(samples):
    def stats(key):
        values = [s[key] for s in samples]
        return {'median': statistics.median(values), 'maximum': max(values), 'minimum': min(values)}
    return {'wall_ms': stats('wall_ms'), 'reported_ms': stats('reported_ms'),
            'expanded': stats('expanded'), 'successful': sum(s['success'] for s in samples), 'trials': len(samples)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8765')))
    parser.add_argument('--repeats', type=int, default=10)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/qa/field-height-proto')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    errors = []; results = []
    try:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    except subprocess.CalledProcessError:
        sha = None
    with sync_playwright() as p:
        launch = {'headless': True}
        if os.environ.get('PW_CHROMIUM_EXECUTABLE'):
            launch['executable_path'] = os.environ['PW_CHROMIUM_EXECUTABLE']
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width':1366, 'height':768})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        cdp = page.context.new_cdp_session(page)
        page.goto('http://localhost:%d/index.html?dev=1' % args.port)
        page.evaluate("enterWorldMap('fort')")
        page.wait_for_function('window.MossForest&&MossForest.active&&!MossForest.busy', timeout=60000)
        metadata = {'repo_sha':sha,'measured_at_utc':datetime.now(timezone.utc).isoformat(),
                    'benchmark_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                        ['js/field/field-height.js','js/field/field-navigation.js','js/field/field-collision.js',
                         'data/maps/dev_height_proto.json','data/maps/moss_forest_02_mossy_ravine.json']},'chromium_version':browser.version,'ua':page.evaluate('navigator.userAgent'),
                    'viewport':{'width':1366,'height':768},'repeats':args.repeats,'warmup_calls_per_route':1,
                    'rates':[1,4],'height_grid':32,'height_max_nodes':60000,
                    '2d_grid':32,'2d_max_nodes':40000,'coordinates':'feet; APIs receive x-17,y-42',
                    'height_api':'MossForest.height instance of window.FieldHeight; public plan/setLevel/blockedAtLevel',
                    '2d_api':'FieldNavigation.destination + first follow (public APIs)',
                    'clock':'external performance.now around each public API call; includes recursive fallback',
                    'scope':'Chromium CPU emulation; not Android or input-to-render timing'}
        for rate in (1,4):
            cdp.send('Emulation.setCPUThrottlingRate', {'rate':rate})
            for kind,mid,routes in [('height','dev_height_proto',HEIGHT_ROUTES),('2d','moss_forest_02_mossy_ravine',TWO_D_ROUTES)]:
                page.evaluate('(map)=>MossForest.enter({map})', mid)
                page.wait_for_function('(map)=>MossForest.mapId===map&&MossForest.active&&!MossForest.busy',arg=mid,timeout=60000)
                page.evaluate('closeDialogue()')
                for rid,label,start,goal in routes:
                    samples = page.evaluate(MEASURE, {'kind':kind,'start':start,'goal':goal,'repeats':args.repeats})
                    row = {'id':rid,'route':label,'map':mid,'planner':kind,'cpu_rate':rate,'start_feet':start,'goal_feet':goal,
                           'straight_distance_px':math.hypot(goal[0]-start[0],goal[1]-start[1]),'summary':summarize(samples),'samples':samples}
                    results.append(row)
                    print('%sx %-16s median %.3fms max %.3fms expanded %.0f success %d/%d' %
                          (rate,rid,row['summary']['wall_ms']['median'],row['summary']['wall_ms']['maximum'],
                           row['summary']['expanded']['median'],row['summary']['successful'],args.repeats),flush=True)
        cdp.send('Emulation.setCPUThrottlingRate', {'rate':1})
        browser.close()
    args.out.mkdir(parents=True,exist_ok=True)
    payload = {'metadata':metadata,'results':results,'errors':errors}
    (args.out/'plan-bench.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    text = ['# 高さ/2D経路探索ベンチ', '', '基準SHA: `%s`。Chromium %s、1366×768、各%d試行＋事前warmup1回。' % (sha,metadata['chromium_version'],args.repeats),
            'CPU倍率はCDPの1×/4×。実機Androidの測定ではない。歩行や描画は測らず、公開APIの同期呼び出しのみを測定。', '',
            '| CPU | 経路 | 足元 start→goal（level） | 直線距離px | ms中央値 | ms最大 | 展開ノード中央値/最大 | 成功 |',
            '|---|---|---|---:|---:|---:|---:|---:|']
    for r in results:
        s=r['summary'];text.append('| %s× | %s | %s → %s | %.1f | %.3f | %.3f | %.0f / %.0f | %d/%d |' %
            (r['cpu_rate'],r['route'],r['start_feet'],r['goal_feet'],r['straight_distance_px'],s['wall_ms']['median'],s['wall_ms']['maximum'],
             s['expanded']['median'],s['expanded']['maximum'],s['successful'],s['trials']))
    text += ['', '## 測定条件と限界', '',
             '- 座標は足元基準。APIにはactor左上基準として(17,42)を減算する。高さの開始levelを各回setLevelし、測定後に元へ戻す。XYからlevelを推測しない。',
             '- 高さは現在のruntimeと同じgrid32/maxNodes60000。2DはA2にenterして設定されるgrid32/maxNodes40000と実マップの静的衝突を使用。既存コード/マップ/セーブ/戦闘を変更しない。',
             '- 全時間は外側のperformance.nowで計測。JSONにはAPI報告msも残す。高さplanがgrid16へ再帰fallbackするとAPI報告ms/expandedは最後の探索のみで、外側msは先行失敗も含む。展開ノード数は公開APIの報告値であり、fallbackの合計とは限らない。',
             '- 2Dはdestination＋最初のfollow。高さplan単体より移動1ステップ等の付随処理を含む。plannerの空間/衝突/距離も異なるため、表の倍率を高さ対応そのものの純粋な速度倍率と解釈しない。',
             '- 各回新しいdestinationを作り既存pathの再利用を避ける。warmup1回は集計から除外。10回は同一pageで測り、renderer/JSの状態やCPU条件順による影響は残る。',
             '- raw samples、reported_ms、成功/失敗、node数は同じフォルダのplan-bench.jsonを参照。0ms付近は時計精度の影響が大きい。', '',
             'console/pageerror: %d。全16条件の各%d回が成功したかは成功列を参照。' % (len(errors),args.repeats)]
    (args.out/'plan-bench.md').write_text('\n'.join(text)+'\n')
    return 0 if len(results)==16 and not errors and all(r['summary']['successful']==args.repeats for r in results) else 1


if __name__=='__main__':
    sys.exit(main())
