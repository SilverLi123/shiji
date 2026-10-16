# V6.2 measured performance

Measured 2026-10-16 on macOS 26.6.2 arm64, Python3.9.6 / SQLite3.51.0. No formal library/credentials. These are deterministic **real Store** fixtures, not production user records or Demo data. Total resources include every17th record in trash: active counts941 /4705 /18823 /47058, attachments50 /250 /1000 /2500. Chinese/English, code/Prompt, projects, notes, tags and files remain in the search corpus.

## Same-data backend comparison (milliseconds)

`qa/baseline.py` executes frozen V6.1 commit9433afc and seeds temporary canonical Store data. `qa/measure.py` copies those SQLite/files fixtures before measuring V6.2. Full-state medians use five samples; query cells show P50/P95 over nine repeated calls after the separately retained first-filter sample. With nine samples P95 is the maximum, not a robust production percentile estimate. Raw individual rounds, response bytes, first-filter costs and environment are in [before.json](evidence/before.json) / [after.json](evidence/after.json).

| Total | V6.1 full state P50 | V6.2 same full state P50 | First60 P50/P95 | 中文“动效” P50/P95 | English React P50/P95 | Mixed+tag+project P50/P95 | Deep page P50/P95 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 14.28 | 12.31 | 3.90/5.38 | 3.57/4.33 | 4.13/19.79 | 4.64/6.44 | 3.25/4.23 |
| 5000 | 129.15 | 53.43 | 3.70/4.24 | 6.82/7.78 | 7.07/8.27 | 9.06/12.66 | 4.74/6.36 |
| 20000 | 1409.87 | 337.00 | 4.70/7.13 | 22.93/26.80 | 30.56/34.98 | 24.22/46.04 | 12.41/13.94 |
| 50000 | 8220.00 | 1127.94 | 4.16/4.92 | 41.27/48.14 | 56.37/62.04 | 61.31/206.37 | 25.08/33.10 |

The same full-state operation at50K falls from8220ms to1128ms after attachment batch reads. More importantly, the normal UI no longer requests it: first-page response is73,732bytes versus64,433,123bytes for the old complete active library, plus the old4MB trash response. This is an architectural transfer comparison, **not** a claim that the same SQL query became thousands of times faster. Full export remains available and still scales with all data.

At50K: category P50/P95 12.46/15.42ms; project13.46/16.74ms; clear search5.08/6.05ms. Broad Chinese first-filter call178.17ms precedes warmed41.27/48.14ms. Mixed/code queries retained outliers206.37/283.60ms; no outlier trimming. A separate actual HTTP broad mixed query (36,078matches, no narrow project filter) recorded first488.76ms, median55.41ms over nine calls; [raw](evidence/http-broad-mixed-50000.json).

## Initial indexing and startup cost

| Total | Source documents+metadata+first page | Additional synchronous FTS build | Exact fallback 中文 | Indexed DB MiB |
|---:|---:|---:|---:|---:|
| 1000 | 101.72 | 194.23 | 3.21 | 6.9 |
| 5000 | 361.53 | 828.52 | 8.58 | 34.4 |
| 20000 | 1876.56 | 4033.69 | 39.00 | 134.4 |
| 50000 | 6501.18 | 10377.39 | 183.95 | 336.0 |

These are application API measurements, not App time-to-interactive. First-use measurement suppresses only FTS scheduling to isolate source-document preparation; full source search is available during accelerator building. Then the explicit synchronous accelerator build is timed independently. Actual application worker builds in32-row chunks with yields, so these columns must not be added and called actual background completion time. Search index adds substantial disk overhead. Reopening an already indexed library avoids rebuilding every document.

Experiments found two material bottlenecks: a virtual-table join could repeat MATCH work per resource; a rowid candidate subquery and FTS-driven NOT INDEXED access avoid this plan. Closing each batch connection caused repeated final-connection WAL checkpoints; one connection across bounded transactions reduced build cost markedly. `mmap_size` is advisory; correctness does not require it. Optional FTS fallback is tested, not assumed available from a version number.

## Actual V5 page and native observations

The in-app browser ran the real page and business HTTP API. QA-only script records render milestones/resource timing and buffers data; it is not loaded by production index.html. Single observed first-interactive milestones (not repeated cold-start distributions):

| Dataset | Initial index absent: browser first rendered usable cards |
|---:|---:|
| 1K | 718.5ms |
| 5K | 1406.4ms |
| 20K | 3601.4ms |
| 50K | 7710.4ms |

Same-data old V6.1 page observed9612.2ms. V6.2 reopening the indexed50K service observed688.2ms. These were not a quiet randomized A/B study; do not infer a guaranteed startup improvement percentage. Warm broad mixed input→render still observed1050.8ms (120ms debounce, HTTP plus rendering and browser scheduling); initial broad search909ms. Backend medians are **not** end-to-end search latency. This remains an optimization target. Evidence files `browser-*.json` preserve all observations.

A real50K UI initialization exposed legacy desktop polling before capability discovery. Regression delays capability3300ms; repair gates polling until initialization succeeds. Fresh cold page now contains no `/api/resources` or `/api/trash` request.

30-second real browser rAF intervals, visible throughout,60 loaded posters:

| Mode | Samples | P50 | P95 | Max | Actual scroll events |
|---|---:|---:|---:|---:|---:|
| Studio / 3D |1800|16.7ms|17.3ms|17.7ms|88|
| Calm / Flat |1796|16.7ms|17.4ms|50.2ms|8|

Scroll paths differ. These are **frame callback intervals**, not compositor/GPU frame delivery or a60FPS certification. At5K,17 actual page loads accumulated1020DOM cards; a30second sample recorded P50/P95 16.8/34.3ms, max933.1ms and three scroll events. Full tests/builds overlapped this stress sample; it is a warning, not isolated attribution. Last page render230ms. No DOM virtualization claim: cumulative cards and repeated full loaded-list work remain a bottleneck requiring focused windowing/layout profiling. V5 art and motion have not been reduced to hide this.

768×1024 and390×844 viewport overrides retained search/filter controls without horizontal document overflow, then overrides were reset. Screenshots cover empty actual library, empty search, long Chinese title/code and summary→full detail.

Native1000 QA app uses separate bundle/data/port. Actual native search reached721matches with60cards and rendered retained V5 Hero. QA diagnostics report hidden=true/focus=false despite AX interaction; first-interactive1277ms and search304ms are **background-only**, not foreground acceptance. Native timing stream also reports backgroundPaused=true and running/cssRunning/transitionRunning=0.30.1s process sampling uses attributed native host93227 and WebContent93237 via the existing Mach sampler: host0.0027% of one core, peak footprint40.19MB; WebContent0.0030%, footprint217.06MB. RSS is also recorded but does not include compressed footprint. GPU allocations are not assigned to these processes; no total-app-memory claim. [Raw](evidence/native-background.jsonl), [summary](evidence/native-background-summary.json).

## Capture concurrency

`qa/capture_under_load.py` copies the1K/5K indexed fixtures, drives20 real capture lifecycle commits with deterministic10ms network responses, and queries during work. Each dataset:19metadata completions, one manually edited resource safely skipped, zero resource loss. Thirty query rounds:1K P50/P9517.99/48.02ms;5K31.44/54.55ms. [Raw](evidence/capture-under-load.json). This validates task/index cooperation, not public-network latency.

## Remaining acceptance limits

- No isolated native foreground CPU/memory/scroll distribution, GPU attribution or sleep/fullscreen certification this round; tool visibility prevents honest foreground claims.
- V5.2 first-detail243–249ms risk remains; this work does not claim to resolve it.
- Large cumulative DOM galleries and broad first-query/UI latency need further profiling;50K stress is not full-product capacity certification.
- Existing10K JSON/ZIP/sync exchange limits remain. Do not rely on archive round-trip for a50K product library until exchange capacity is separately upgraded and tested.
- Python3.12 CI runtime may carry a different SQLite build; derived FTS capability probe and exact fallback protect correctness, but remote candidate Actions have not run before an authorized push.
