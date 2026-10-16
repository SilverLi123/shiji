# Frozen V6.2 baseline

Product source:579d4471d05a. No gallery changes were made before the diagnostic profile and first complete5K60→2040 experiment. Raw artifacts are in ignored desktop-app/dist/v63-before-*; qa/run_matrix.py repeats the frozen source against all four disposable datasets, three fresh browser contexts per mode. Runs still in progress are not accepted results. Final aggregated evidence is recorded with the after comparison.

Chrome155.0.8059.39,1280×900,deviceScaleFactor1, headless with standard GPU settings. This is automated desktop-browser input, not native/physical mouse certification. rAF is a sampled main-thread interval, not compositor FPS. Each sample records visibility. Original1K fixture has941 active resources;1020/2000 unique browsing is unavailable.60-page accumulation reaches2040 for target2000; report actual counts.

The first diagnostic trace includes detailed compositor categories and adds overhead; do not compare it as an untraced FPS benchmark. See evidence/before-trace-summary.json. The untraced run separately confirms cumulative DOM and scroll cost. Probe itself counts mounted nodes per sampled rAF; both before and after use the same probe.

| First5K untraced round | Mounted | Render ms | scroll P50/P95/max ms |
|---|---:|---:|---|
|60|60|51.3|16.7/16.8/49.9|
|300|300|30.8|33.3/50/50|
|600|600|74.3|116.6/150/166.7|
|1020|1020|106.4|250.1/316.6/383.4|
|2040|2040|269|949.9/1316.7/1433.3|

Mixed search after2040 cards:2621.4ms input→double-rAF; following clear189ms, React189.7ms, clear174.3ms. This isolates teardown/presentation cost from the server query itself in raw request/server-timing records. A single round is diagnostic evidence only, not a percentile claim across repeated runs.

Architecture review and the minimal intervention contract are in ARCHITECTURE.md. Subsequent source edits cannot affect the ongoing baseline matrix because each baseline server serves an archived579d447 tree. CPU-heavy builds/tests will be sequenced apart from performance sampling; any interrupted or contended samples must be identified.
