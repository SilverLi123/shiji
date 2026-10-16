# V6.3 performance acceptance

## Method and provenance

Frozen before source:579d447; after performance source:245639d (interaction-only review fixes are tested separately, not retroactively substituted into this matrix). Actual Store libraries contain1K/5K/20K/50K total resources,941/4705/18823/47058 active rows. Three new browser contexts per dataset/mode, identical fixture copies,1280×900, DSF1, Chrome155.0.8059.80 headless. No build/native test was run concurrently with accepted timing samples. The separately labelled earlier diagnostic trace also identifies Chrome.80 and is excluded from these untraced medians. A contaminated baseline1KCalm round was explicitly excluded and replaced; its raw file remains in ignored dist.

These are main-thread rAF interval samples from real mouse-wheel automation, not compositor FPS. Each before/after pair uses the same driver and probe. All counts are actual loaded/mounted rows; target2000 reaches2040 by60-row pagination.1K cannot supply1020/2000 unique active rows, so the headline table uses600 and raw evidence records unavailability. Traced and untraced measurements are separate. Lower rendering cost does not prove universal60FPS.

## Repeated comparison

Values below are medians of three round values. Scroll P95 is the median of each round's P95, not a pooled percentile. Round maxima, all60/300/600/1020/2040 stages, both clear-search operations, React search, detail return deltas and heap are retained in evidence/scale-summary.json. Raw file sizes and SHA256 provenance are included there; large artifacts remain in ignored dist.

| Mode / total resources | Loaded | DOM before → after | Render median ms before → after | Scroll P95 median ms before → after | Mixed search median ms before → after |
|---|---:|---|---|---|---|
| studio / 1000 | 600 | 600 → 16 | 76.7 → 11.7 | 116.7 → 16.7 | 592.7 → 216.8 |
| calm / 1000 | 600 | 600 → 16 | 62.7 → 10.9 | 33.4 → 16.7 | 270.4 → 177.7 |
| studio / 5000 | 2040 | 2040 → 16 | 269 → 14.7 | 1316.7 → 16.8 | 2620.2 → 254.3 |
| calm / 5000 | 2040 | 2040 → 16 | 270.4 → 19.5 | 550 → 16.8 | 815.8 → 252.4 |
| studio / 20000 | 2040 | 2040 → 15 | 295.9 → 16.5 | 1466.7 → 16.7 | 2739.3 → 311.5 |
| calm / 20000 | 2040 | 2040 → 15 | 192.3 → 20.7 | 316.6 → 16.8 | 692.9 → 291.9 |
| studio / 50000 | 2040 | 2040 → 18 | 234.2 → 22.6 | 1249.9 → 16.8 | 2823.4 → 517.1 |
| calm / 50000 | 2040 | 2040 → 18 | 178.8 → 24.1 | 333.3 → 16.7 | 1111.8 → 513.2 |

Mixed search is `动效 React`, entered after the accumulated browsing scene. Input→double-rAF includes input dispatch, debounce, scheduling, HTTP, parsing, application/reconciliation/layout and the probe's two rAF callbacks. It is not merely SQLite query latency. Server-Timing, request start/header/JSON completion, synchronous render, card HTML and reconciliation costs are preserved separately in each raw result. Search/filter semantics and backend SQL are unchanged; this task removes proven presentation/teardown overhead.

## Initial presentation and memory

| Library / mode | First list double-rAF ms before → after | First successful QA control upper bound ms before → after | JS heap MiB at largest measured stage before → after |
|---|---|---|---|
| 1000 / studio | 415.5 → 259.3 | 1833.8 → 1750.7 | 13.58 → 6.39 |
| 1000 / calm | 443.7 → 300.7 | 1946.2 → 1737.5 | 10.61 → 7.63 |
| 5000 / studio | 374.6 → 329.5 | 1777.3 → 1703.4 | 37.35 → 18.63 |
| 5000 / calm | 518.8 → 377.2 | 2087 → 1846.8 | 47.26 → 13.41 |
| 20000 / studio | 416.6 → 344.6 | 1829 → 1714.6 | 21.88 → 16.73 |
| 20000 / calm | 379.5 → 337.5 | 1859.4 → 1775.1 | 38.57 → 14.1 |
| 50000 / studio | 516.2 → 447 | 1855.4 → 1829.3 | 24.54 → 8.75 |
| 50000 / calm | 518.7 → 454.1 | 1992.1 → 1924.3 | 43.29 → 8.16 |

First list double-rAF is a list-presentation proxy, not TTI. The successful QA-control timestamp is an observed upper bound after the driver waits for the brand intro to finish, not a measurement of the first possible interaction. Fresh browser contexts are used; OS filesystem caches are not evicted, so these are not disk-cold startup claims. JS heap is sampled without forced GC and cannot be equated with resident memory, physical footprint or a leak proof.

## Attribution and remaining cost

The initial instrumented55.66s diagnostic records inclusive Layerize33.84s and DrawProperties21.47s versus Layout0.75s, style0.93s and image decode4.1ms. Those categories overlap. The frozen page retains all loaded complex3D cover DOM; every append regenerates all accumulated markup and highlighting repeats DOM scans. The windowed page keeps viewport/overscan plus interaction pins, bounds markup caching to240, skips unchanged residency and reuses unchanged Spatial Deck presentation. Geometry/loaded summaries remain proportional to data loaded through existing pagination. List/project-board are deliberately not newly virtualized.

Chrome did not expose layer-count events in this headless setup; no fabricated layer count is reported. CDP/physical-process sampling for newer QA runs is retained where available, but the initial baseline has no equivalent physical-footprint series, so there is no valid browser CPU/physical-memory percentage comparison. Shared GPU allocation is not wholly attributable to one app.

## Native and real input

The user-driven foreground native5K sample and coordinate-click recording are separate from headless timings: evidence/native-user-interaction.json, native-real-input.json and native-user-process.json. The mixed session had13418 rAF intervals,44scroll events and hidden=false; P50/P95/max17/18/283ms. The later physical coordinate detail phase still recorded246ms maximum, P50/P9517/18ms, zero proxies after close and identical scrollbar return. This native first-detail risk remains unresolved.

The30.119s mixed-session sampler used actual Host6246/WebContent6262/backend6254 identities. WebContent peak physical footprint493.67MiB and peak RSS54.91MiB are different accounting measures. Its0.28% one-core CPU delta occurred in this mixed/post-interaction interval and is not a quiet Studio/scroll performance certification. A fixed-mode native comparison, where obtained, is recorded separately; background or interrupted runs must not be accepted as foreground results.

Manual touchpad inertia, sleep/wake, full-screen, VoiceOver virtual cursor and multi-scale native cold-start distributions remain explicit acceptance items. Retain the V5.2 Instruments investigation and do not mark native latency fixed on the strength of browser improvement.

## Final candidate confirmation and matched tracing

Final shipping-code revision922daa8 was rechecked in three fresh5K Studio contexts after the review fixes:2040loaded,27mounted each round; synchronous render16.9/13.4/12.3ms, scrollP9533.3/16.8/16.7ms, maxima66.5/16.8/16.8ms; mixed search246.2/229.8/243.8ms. See evidence/final-confirmation.json. Instant anchor correction changes the actual scroll trajectory and sampled viewport; these rounds are recorded separately, not silently substituted into the48-round matrix.

A matched diagnostic pair uses the same current driver, Chrome155.0.8059.80, categories `devtools.timeline,blink.user_timing,v8`, fixture library and60→300→600→1020 input sequence. Frozen579d447 trace duration49.91s; final922daa8 trace10.73s. Complete-event inclusive Layerize totals33936ms→567ms; style1056ms→338ms; Layout698ms→292ms; Paint892ms→228ms. These nested events overlap and instrumented runs are not used as untraced percentiles or exact GPU utilization. This separately confirms that the main retained-composition cost is removed along with offscreen DOM, while ordinary style/layout/paint still occur. Raw files: `desktop-app/dist/v63-before-matched-studio.trace.json` and `v63-final-profile-studio.trace.json`; compact summaries are committed in evidence.

The final native fixed-mode run could not begin because the Mac was locked again. Both isolated QA bundles compile, but no new native foreground data is inferred from that fact. Earlier real user/coordinate evidence remains attached to its actualdf2c380 revision.
