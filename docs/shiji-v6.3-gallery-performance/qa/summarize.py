"""Aggregate completed isolated runs; preserve round-level values and provenance."""
import hashlib,json,statistics
from pathlib import Path

repo=Path(__file__).resolve().parents[3]
dist=repo/'desktop-app/dist'
evidence=Path(__file__).resolve().parent.parent/'evidence'
result={'method':'3 fresh browser contexts per scene; medians of round measurements, not pooled FPS; raw files remain in ignored dist','runs':[],'artifacts':[]}
def median(values):
 return round(statistics.median(values),2) if values else None
for phase in ['before','after']:
 for size in [1000,5000,20000,50000]:
  for mode in ['studio','calm']:
   file=dist/f'v63-{phase}-{size}-{mode}.json'
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
evidence.mkdir(exist_ok=True);(evidence/'scale-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
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
(evidence/'scale-table.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines));print('Completed scene sets:',len(result['runs']),'/ 16')
startup=['| Library / mode | First list double-rAF ms before → after | First successful QA control upper bound ms before → after | JS heap MiB at largest measured stage before → after |','|---|---|---|---|']
for size in [1000,5000,20000,50000]:
 for mode in ['studio','calm']:
  pair=[next((r for r in result['runs'] if r['phase']==p and r['size']==size and r['mode']==mode),None) for p in ['before','after']]
  if not all(pair):continue
  heaps=[next(s for s in reversed(r['stages']) if not s.get('unavailable'))['heapMiB'] for r in pair]
  startup.append('| %s / %s | %s | %s | %s |'%(size,mode,' → '.join(str(r['firstPostRafMs']) for r in pair),' → '.join(str(r['firstSuccessfulQAControlUpperMs']) for r in pair),' → '.join(str(median(h)) for h in heaps)))
text='''# V6.3 performance acceptance

## Method and provenance

Frozen before source:579d447; after performance source:245639d (interaction-only review fixes are tested separately, not retroactively substituted into this matrix). Actual Store libraries contain1K/5K/20K/50K total resources,941/4705/18823/47058 active rows. Three new browser contexts per dataset/mode, identical fixture copies,1280×900, DSF1, Chrome155.0.8059.80 headless. No build/native test was run concurrently with accepted timing samples. The separately labelled earlier diagnostic trace also identifies Chrome.80 and is excluded from these untraced medians. A contaminated baseline1KCalm round was explicitly excluded and replaced; its raw file remains in ignored dist.

These are main-thread rAF interval samples from real mouse-wheel automation, not compositor FPS. Each before/after pair uses the same driver and probe. All counts are actual loaded/mounted rows; target2000 reaches2040 by60-row pagination.1K cannot supply1020/2000 unique active rows, so the headline table uses600 and raw evidence records unavailability. Traced and untraced measurements are separate. Lower rendering cost does not prove universal60FPS.

## Repeated comparison

Values below are medians of three round values. Scroll P95 is the median of each round's P95, not a pooled percentile. Round maxima, all60/300/600/1020/2040 stages, both clear-search operations, React search, detail return deltas and heap are retained in evidence/scale-summary.json. Raw file sizes and SHA256 provenance are included there; large artifacts remain in ignored dist.

'''+ '\n'.join(lines)+'''

Mixed search is `动效 React`, entered after the accumulated browsing scene. Input→double-rAF includes input dispatch, debounce, scheduling, HTTP, parsing, application/reconciliation/layout and the probe's two rAF callbacks. It is not merely SQLite query latency. Server-Timing, request start/header/JSON completion, synchronous render, card HTML and reconciliation costs are preserved separately in each raw result. Search/filter semantics and backend SQL are unchanged; this task removes proven presentation/teardown overhead.

## Initial presentation and memory

'''+ '\n'.join(startup)+'''

First list double-rAF is a list-presentation proxy, not TTI. The successful QA-control timestamp is an observed upper bound after the driver waits for the brand intro to finish, not a measurement of the first possible interaction. Fresh browser contexts are used; OS filesystem caches are not evicted, so these are not disk-cold startup claims. JS heap is sampled without forced GC and cannot be equated with resident memory, physical footprint or a leak proof.

## Attribution and remaining cost

The initial instrumented55.66s diagnostic records inclusive Layerize33.84s and DrawProperties21.47s versus Layout0.75s, style0.93s and image decode4.1ms. Those categories overlap. The frozen page retains all loaded complex3D cover DOM; every append regenerates all accumulated markup and highlighting repeats DOM scans. The windowed page keeps viewport/overscan plus interaction pins, bounds markup caching to240, skips unchanged residency and reuses unchanged Spatial Deck presentation. Geometry/loaded summaries remain proportional to data loaded through existing pagination. List/project-board are deliberately not newly virtualized.

Chrome did not expose layer-count events in this headless setup; no fabricated layer count is reported. CDP/physical-process sampling for newer QA runs is retained where available, but the initial baseline has no equivalent physical-footprint series, so there is no valid browser CPU/physical-memory percentage comparison. Shared GPU allocation is not wholly attributable to one app.

## Native and real input

The user-driven foreground native5K sample and coordinate-click recording are separate from headless timings: evidence/native-user-interaction.json, native-real-input.json and native-user-process.json. The mixed session had13418 rAF intervals,44scroll events and hidden=false; P50/P95/max17/18/283ms. The later physical coordinate detail phase still recorded246ms maximum, P50/P9517/18ms, zero proxies after close and identical scrollbar return. This native first-detail risk remains unresolved.

The30.119s mixed-session sampler used actual Host6246/WebContent6262/backend6254 identities. WebContent peak physical footprint493.67MiB and peak RSS54.91MiB are different accounting measures. Its0.28% one-core CPU delta occurred in this mixed/post-interaction interval and is not a quiet Studio/scroll performance certification. A fixed-mode native comparison, where obtained, is recorded separately; background or interrupted runs must not be accepted as foreground results.

Manual touchpad inertia, sleep/wake, full-screen, VoiceOver virtual cursor and multi-scale native cold-start distributions remain explicit acceptance items. Retain the V5.2 Instruments investigation and do not mark native latency fixed on the strength of browser improvement.
'''
report=evidence.parent/'PERFORMANCE.md'
marker='\n## Final candidate confirmation and matched tracing\n'
existing=report.read_text() if report.exists() else ''
# Preserve explicitly curated final-candidate/native acceptance notes.
notes=marker+existing.split(marker,1)[1] if marker in existing else ''
report.write_text(text+notes)
