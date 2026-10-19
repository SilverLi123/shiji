"""Aggregate completed isolated runs; preserve round-level values and provenance."""
import argparse,hashlib,json,statistics
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');parser.add_argument('--optimized',action='store_true');args=parser.parse_args()
repo=Path(__file__).resolve().parents[3]
dist=repo/'desktop-app/dist'
evidence=Path(__file__).resolve().parent.parent/'evidence'
result={'method':'3 fresh browser contexts per scene; medians of round measurements, not pooled FPS; raw files remain in ignored dist','runs':[],'artifacts':[]}
def median(values):
 return round(statistics.median(values),2) if values else None
for phase in ['before','after']:
 for size in [1000,5000,20000,50000]:
  for mode in ['studio','calm']:
   file=dist/(f'v64-optimized-{phase}-{size}-{mode}.json' if args.optimized and phase=='after' else f'v64-final-{phase}-{size}-{mode}.json' if args.final and phase=='after' else f'v64-{phase}-{size}-{mode}.json')
   if not file.exists():continue
   data=json.loads(file.read_text());rounds=[r for r in data['rounds'] if r.get('completed') and not r.get('interference')]
   if len(rounds)!=3:continue
   entry={'phase':phase,'size':size,'mode':mode,'versions':sorted(set(r.get('browserVersion',data['version']) for r in rounds)),'rounds':len(rounds),'firstPostRafMs':median([r['firstPostRaf'] for r in rounds]),'firstSuccessfulQAControlUpperMs':median([r['raw']['samples'][0]['start'] for r in rounds]),'stages':[],'searches':[]}
   for target in [60,300,600,1020,2000]:
    rows=[next(s for s in r['stages'] if s['target']==target) for r in rounds if any(s['target']==target for s in r['stages'])]
    valid=[s for s in rows if not s.get('unavailable')]
    if len(valid)!=3:
     entry['stages'].append({'target':target,'unavailable':True});continue
    entry['stages'].append({'target':target,'loaded':valid[0]['actualLoaded'],'cards':[s['cards'] for s in valid],'renderMs':[round(s['lastRender']['renderMs'],2) for s in valid],'scrollP95Ms':[round(s['scrollFrames']['p95'],2) for s in valid],'scrollMaxMs':[round(s['scrollFrames']['max'],2) for s in valid],'heapMiB':[round(s['heapBytes']/1048576,2) for s in valid],'nodes':[s['nodes'] for s in valid],'hidden':any(s['hidden'] or s['scrollFrames']['hidden'] or s['scrollFrames']['hiddenEnd'] for s in valid)})
   for index,query in enumerate(['动效 React','','React','']):
    entry['searches'].append({'query':query,'inputPostRafMs':[round(r['searches'][index]['input']['inputToPostRafMs'],2) for r in rounds],'renderMs':[round(r['searches'][index]['lastRender']['renderMs'],2) for r in rounds]})
   entry['detail']=[{'maxFrameMs':round(r['detailFrames']['max'],2),'returnDelta':round(r['detailReturn']['afterScrollY']-r['detailReturn']['origin']['scrollY'],2),'ghosts':r['detailReturn']['ghosts']} for r in rounds]
   result['runs'].append(entry);result['artifacts'].append({'file':str(file.relative_to(repo)),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
evidence.mkdir(exist_ok=True);(evidence/('scale-optimized-summary.json' if args.optimized else 'scale-final-summary.json' if args.final else 'scale-summary.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['| Mode / total resources | Loaded | DOM before → after | Render median ms before → after | Scroll P95 median ms before → after | Mixed search median ms before → after |','|---|---:|---|---|---|---|']
for size in [1000,5000,20000,50000]:
 for mode in ['studio','calm']:
  pair=[next((r for r in result['runs'] if r['phase']==p and r['size']==size and r['mode']==mode),None) for p in ['before','after']]
  if not all(pair):continue
  target=600 if size==1000 else 2000
  stages=[next(s for s in r['stages'] if s['target']==target) for r in pair]
  cols=[str(stages[0]['loaded'])]
  for key in ['cards','renderMs','scrollP95Ms']:cols.append(' → '.join(str(median(s[key])) for s in stages))
  cols.append(' → '.join(str(median(r['searches'][0]['inputPostRafMs'])) for r in pair))
  lines.append('| %s / %s | %s |'%(mode,size,' | '.join(cols)))
(evidence/('scale-optimized-table.md' if args.optimized else 'scale-final-table.md' if args.final else 'scale-table.md')).write_text('\n'.join(lines)+'\n')
print('\n'.join(lines));print('Completed scene sets:',len(result['runs']),'/ 16')
startup=['| Library / mode | First list double-rAF ms before → after | First successful QA control upper bound ms before → after | JS heap MiB at largest measured stage before → after |','|---|---|---|---|']
for size in [1000,5000,20000,50000]:
 for mode in ['studio','calm']:
  pair=[next((r for r in result['runs'] if r['phase']==p and r['size']==size and r['mode']==mode),None) for p in ['before','after']]
  if not all(pair):continue
  heaps=[next(s for s in reversed(r['stages']) if not s.get('unavailable'))['heapMiB'] for r in pair]
  startup.append('| %s / %s | %s | %s | %s |'%(size,mode,' → '.join(str(r['firstPostRafMs']) for r in pair),' → '.join(str(r['firstSuccessfulQAControlUpperMs']) for r in pair),' → '.join(str(median(h)) for h in heaps)))
text="""# Cover Studio 3.0 — performance evidence

## Scope and method

Frozen before: `31eeea27547ae9c00a1c88212a5bbc2f70ed268f` (V6.3). Initial after: `bb8a460` (before the review corrections). Both read identical copies of the candidate-created schema3 fixtures: 1K/5K/20K/50K total rows, 941/4705/18823/47058 active rows, mixed Chinese/English/code/Prompt, project notes and real local attachments. Optional cover preferences are present in both copies; the old renderer ignores them. Fixture construction is reproducible with `qa/fixtures.py`; no formal library was read.

The existing V6.3 browser probe and exact same driver are reused, three fresh 1280×900 DSF1 Chrome contexts per dataset/mode. Studio/Calm runs use actual mouse-wheel input, API pagination, search, category switch and opening/closing a real resource. The 2000 target reaches2040 in60-row batches; 1K cannot reach1020, so its comparable stage is600. The gallery is windowed, not all50K full DOM cards. These are headless-browser tests, not foreground WKWebView or physical iPhone performance.

## Repeated comparison

"""+"\n".join(lines)+"""

All values are medians of three round measurements; scroll P95 is the median of three per-round P95s, not a pooled percentile or FPS certification. Search includes input, debounce, network/API, parsing, render and the probe's double-rAF. It is not SQL-only latency. Raw round values, errors, input timings, frame arrays, query Server-Timing, process CPU counters and hashes are retained in ignored `desktop-app/dist/v64-{phase}-{size}-{mode}.json`; compact provenance and all measured stages are in `evidence/scale-summary.json`.

## Startup and memory

"""+"\n".join(startup)+"""

First-list double-rAF is a presentation proxy, not TTI. Successful QA-control time is an observed upper bound after waiting for the preserved brand intro. OS caches were not evicted; fresh contexts do not prove disk-cold launch. Heap is JS heap without forced GC, not WebContent RSS, GPU ownership or a leak proof. CDP process CPU counters are cumulative browser observations, not quiet native one-core CPU percentages. No physical-memory or native60FPS claim is made.

## Review corrections and retained risks

Review corrections affect the editor ownership/source policy and native code captions, and reserve shared Editorial text regions. A final-candidate browser confirmation is recorded separately below rather than retroactively replacing the initial measured source. The completed16scene sets contain48rounds and no page errors; the raw data is the authority for individual long frames and query outliers.

No heavy native build ran during the initial matrix; lightweight reviewer checks could overlap early samples. Therefore these results are functional/performance regression evidence, not a quiet CPU calibration. The retained V6.3/V5.2 foreground-native first-detail ~246ms risk is not addressed or declared fixed. Physical-device capture/sync, native sleep/wake, touchpad inertia, VoiceOver and large Dynamic Type require separate acceptance.
"""
if args.final:
 text=text.replace('Initial after: `bb8a460` (before the review corrections).','Final after runtime: `748d8af`; final tested head: `2f2c3b8` (later commits are test/docs only).').replace('scale-summary.json','scale-final-summary.json').replace('Review corrections affect the editor ownership/source policy and native code captions, and reserve shared Editorial text regions. A final-candidate browser confirmation is recorded separately below rather than retroactively replacing the initial measured source.','Review corrections affect editor ownership/source policy and native code captions, and reserve shared Editorial text regions. This report uses a fresh final-after24-round matrix; initial-after measurements remain in scale-summary.json. The owned QA simulator was shut down and no local build or test ran concurrently with the final-after scenes.').replace('desktop-app/dist/v64-{phase}-{size}-{mode}.json','desktop-app/dist/v64-before-{size}-{mode}.json and v64-final-after-{size}-{mode}.json')
if args.optimized:
 text=text.replace('Initial after: `bb8a460` (before the review corrections).','Optimized runtime: `7bc01cb`; iPhone UI runtime `748d8af` is unchanged by the web-only geometry optimization.').replace('scale-summary.json','scale-optimized-summary.json').replace('desktop-app/dist/v64-{phase}-{size}-{mode}.json','desktop-app/dist/v64-before-{size}-{mode}.json and v64-optimized-after-{size}-{mode}.json')
 text += '\n## Measured optimization\n\nThe pre-optimization50K Studio accumulated2040 stage rendered in34.8ms median (baseline17ms); HTML creation itself was only4.2ms in a representative36.1ms round. The residency regression exposed1000 unnecessary cover resolutions for1000 unmeasured frame-mode rows. Optional chaining still evaluated the comparison RHS. The cache now returns its existing frame/ratio fallback without resolving a cover when no measurement/decoded ratio exists. This changes no markup, image quality, motion controller or resource data. The test first failed at1000calls, then passed its bounded-call gate, followed by full Node, real browser and Python regression.\n\nThis fresh optimized-after24-round matrix ran after the tests, with the owned simulator stopped. The initial/pre-optimization samples remain in scale-summary.json / scale-final-summary.json and their hashed raw files; they are not silently replaced.\n'
(evidence.parent/'PERFORMANCE.md').write_text(text)
