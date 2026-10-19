# Cover Studio 3.0 — performance evidence

## Scope and method

Frozen before: `31eeea27547ae9c00a1c88212a5bbc2f70ed268f` (V6.3). Optimized runtime: `7bc01cb`; iPhone UI runtime `748d8af` is unchanged by the web-only geometry optimization. Both read identical copies of the candidate-created schema3 fixtures: 1K/5K/20K/50K total rows, 941/4705/18823/47058 active rows, mixed Chinese/English/code/Prompt, project notes and real local attachments. Optional cover preferences are present in both copies; the old renderer ignores them. Fixture construction is reproducible with `qa/fixtures.py`; no formal library was read.

The existing V6.3 browser probe and exact same driver are reused, three fresh 1280×900 DSF1 Chrome contexts per dataset/mode. Studio/Calm runs use actual mouse-wheel input, API pagination, search, category switch and opening/closing a real resource. The 2000 target reaches2040 in60-row batches; 1K cannot reach1020, so its comparable stage is600. The gallery is windowed, not all50K full DOM cards. These are headless-browser tests, not foreground WKWebView or physical iPhone performance.

## Repeated comparison

| Mode / total resources | Loaded | DOM before → after | Render median ms before → after | Scroll P95 median ms before → after | Mixed search median ms before → after |
|---|---:|---|---|---|---|
| studio / 1000 | 600 | 30 → 30 | 12.5 → 7.6 | 16.8 → 16.7 | 229.8 → 172.6 |
| calm / 1000 | 600 | 30 → 30 | 15.7 → 9.1 | 16.7 → 16.7 | 221.9 → 170.4 |
| studio / 5000 | 2040 | 30 → 30 | 18.7 → 15.5 | 16.8 → 16.8 | 266.8 → 258.9 |
| calm / 5000 | 2040 | 30 → 30 | 12.5 → 10.9 | 16.8 → 16.8 | 191 → 217.5 |
| studio / 20000 | 2040 | 30 → 30 | 15.5 → 21.6 | 16.8 → 16.8 | 409 → 385.6 |
| calm / 20000 | 2040 | 30 → 30 | 15.3 → 11.8 | 16.8 → 16.8 | 425.1 → 319.6 |
| studio / 50000 | 2040 | 30 → 30 | 17 → 21.2 | 16.7 → 16.7 | 910 → 503.6 |
| calm / 50000 | 2040 | 30 → 30 | 16.7 → 15.2 | 16.7 → 16.7 | 1423.4 → 523.6 |

All values are medians of three round measurements; scroll P95 is the median of three per-round P95s, not a pooled percentile or FPS certification. Search includes input, debounce, network/API, parsing, render and the probe's double-rAF. It is not SQL-only latency. Raw round values, errors, input timings, frame arrays, query Server-Timing, process CPU counters and hashes are retained in ignored `desktop-app/dist/v64-before-{size}-{mode}.json and v64-optimized-after-{size}-{mode}.json`; compact provenance and all measured stages are in `evidence/scale-optimized-summary.json`.

## Startup and memory

| Library / mode | First list double-rAF ms before → after | First successful QA control upper bound ms before → after | JS heap MiB at largest measured stage before → after |
|---|---|---|---|
| 1000 / studio | 433.8 → 327.6 | 1834.4 → 1717.1 | 5.93 → 6.84 |
| 1000 / calm | 525.8 → 317.6 | 2049.8 → 1815.4 | 6.48 → 7.11 |
| 5000 / studio | 360.2 → 435.5 | 1766.8 → 1846.1 | 13.77 → 18.69 |
| 5000 / calm | 208.6 → 481.6 | 1647.1 → 1982.6 | 19.25 → 18.36 |
| 20000 / studio | 594.2 → 461.4 | 1978.8 → 1853.1 | 17.35 → 14.99 |
| 20000 / calm | 700.4 → 628 | 2156.2 → 2173.2 | 17.16 → 16.48 |
| 50000 / studio | 794.7 → 826.5 | 2161.2 → 2208.2 | 14.65 → 13.2 |
| 50000 / calm | 1474.3 → 624.2 | 1910.2 → 1920.3 | 19.43 → 11.89 |

First-list double-rAF is a presentation proxy, not TTI. Successful QA-control time is an observed upper bound after waiting for the preserved brand intro. OS caches were not evicted; fresh contexts do not prove disk-cold launch. Heap is JS heap without forced GC, not WebContent RSS, GPU ownership or a leak proof. CDP process CPU counters are cumulative browser observations, not quiet native one-core CPU percentages. No physical-memory or native60FPS claim is made.

## Review corrections and retained risks

Review corrections affect the editor ownership/source policy and native code captions, and reserve shared Editorial text regions. A final-candidate browser confirmation is recorded separately below rather than retroactively replacing the initial measured source. The completed16scene sets contain48rounds and no page errors; the raw data is the authority for individual long frames and query outliers.

No heavy native build ran during the initial matrix; lightweight reviewer checks could overlap early samples. Therefore these results are functional/performance regression evidence, not a quiet CPU calibration. The retained V6.3/V5.2 foreground-native first-detail ~246ms risk is not addressed or declared fixed. Physical-device capture/sync, native sleep/wake, touchpad inertia, VoiceOver and large Dynamic Type require separate acceptance.

## Measured optimization

The pre-optimization50K Studio accumulated2040 stage rendered in34.8ms median (baseline17ms); HTML creation itself was only4.2ms in a representative36.1ms round. The residency regression exposed1000 unnecessary cover resolutions for1000 unmeasured frame-mode rows. Optional chaining still evaluated the comparison RHS. The cache now returns its existing frame/ratio fallback without resolving a cover when no measurement/decoded ratio exists. This changes no markup, image quality, motion controller or resource data. The test first failed at1000calls, then passed its bounded-call gate, followed by full Node, real browser and Python regression.

This fresh optimized-after24-round matrix ran after the tests, with the owned simulator stopped. The initial/pre-optimization samples remain in scale-summary.json / scale-final-summary.json and their hashed raw files; they are not silently replaced.
