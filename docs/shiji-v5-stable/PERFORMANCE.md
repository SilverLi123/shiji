# V5 measured performance and limits

This is instrumented acceptance evidence, not a 60 FPS or release claim. All libraries are isolated SQLite stores containing explicitly labelled QA pressure fixtures, saved through the real Store. No Demo data/backend or user library is substituted. The actual V5 HTML/CSS/JS, search/filter and API are used.

## Method

macOS 26.6.2 ARM64, WK-based Codex in-app browser, temporary 1440×900 viewport override. 100/1000/5000 stored records; initial gallery DOM is bounded to 60 cards. Open each origin, search `QA 00000`, clear, select the development category, return all, scroll three pages down/up, repeatedly open/close details and select Calm. The QA script is injected at document start only in isolated QA pages/bundles. Normal HTML does not load it.

“Interactive” means the first completed actual `render()` event, from probe script start. It includes page/API loading but excludes native process launch and is not proof of first composited paint or all controls being ready. Search/category response ends at render completion, not presentation to the display. Frame values are consecutive requestAnimationFrame callback gaps; they reflect scheduling, layout, painting and automation/system contention, not a GPU-presented FPS counter. Each phase has at most 600 intervals and 240 reports. Raw JSON preserves individual sample counts; do not treat a short phase as a statistically representative percentile.

## Actual browser runs

| Stored records | First render from script start | Unique search response | Development category response | Startup RAF samples | Startup p50 / p95 / max |
|---:|---:|---:|---:|---:|---:|
| 100 | 1589.3 ms | 22.4 ms | 56.5 ms | 346 | 16.7 / 33.3 / 616.8 ms |
| 1000 | 427.4 ms | 56.8 ms | 236.2 ms | 451 | 16.7 / 17.5 / 133.4 ms |
| 5000 | 808.4 ms | 48.3 ms | 82.6 ms | 462 | 16.7 / 17.3 / 165.8 ms |

These are single instrumented runs under different cache/system states, not averages across repeated cold starts. The non-monotonic numbers must not be interpreted as resource-count scaling guarantees. Search clear/return-all is more expensive because 60 posters are reconstructed/reconciled, unlike the one-result search.

Explicit scroll windows show >16.7 ms gaps: 100-record windows have p95 around 33–34 ms, up to 116 ms; the 1000-record run includes p95 50–83.5 ms and max 183.3 ms; the 5000 run includes p95 33.3–33.6 ms and max 67.1 ms. Tool interaction and automated scrolling are included. Continuous idle smoothness alone does not certify interaction or scrolling.

After limiting the artwork MutationObserver, a 5000-record run observed first render 505.5 ms, search 30.6 ms, category 64.1 ms, return-all 53.6 ms. This is an uncontrolled before/after observation. The deterministic regression proves unrelated status/particle/probe mutations no longer trigger full artwork scans; it does not prove these timing differences were all caused by that change.

First detail open still reached 233.4 ms; later openings varied around 33.7–67.5 ms. Closed details settled to zero detail proxies and bounded animation counts; no monotonic proxy growth was observed across four/eight actual open/close operations. Existing Node tests additionally verify actual cancel/reopen/teardown paths. This is not a WebKit heap-leak certification. Calm settled to zero running animations in the 5000-record run.

The initial probe could emit a completed frame window again during pagehide. Final probe deletes completed bins; a red/green regression covers this. Raw earlier data is retained and duplicate rows are not independent observations. The final probe also counts the actual `.shiji-dialog-exit` class and distinguishes CSS animation vs CSS transition counts.

## Native runtime

Actual isolated WindowGroup bundles with 1000/5000 stored resources loaded 60 gallery cards. Script-start to first-render values were 793/710 ms; render work 312/319 ms. Background Hero opacity=1/filter=none, without a search-triggered repaint. Classified 100-record native logging confirms `backgroundPaused=true`, `cssRunning=0`; remaining running entries at initial sampling were finite CSS transitions. Actual visibility events show foreground resume and background return. Opening/closing a window preserved the owned backend PID in phase 2.

A 10.18-second process interval measured only positively identified QA hosts and their owned Python children:

| Library | Host CPU, % one core | Python CPU | Host RSS | Python RSS |
|---:|---:|---:|---:|---:|
| 1000 | 0.000% | 0.196% | 14,320 KiB | 4,448 KiB |
| 5000 | 0.000% | 0.196% | 15,456 KiB | 6,736 KiB |

These are hidden Studio measurements, not foreground 3D CPU or total app footprint. RSS can omit compressed/nonresident pages. WebKit GPU/WebContent/Networking processes have launchd parentage and were not positively associated to one app, so their memory/CPU is excluded rather than attributed speculatively.

A short native foreground sample reached p95 905 ms during simultaneous previews, tools and compilation. Later process inspection showed substantial WindowServer/Codex/other process activity. Keep that result as a warning; it cannot certify steady foreground performance or isolate a rendering bottleneck. Native input repeatedly returned unavailable-window/timeouts even after unlock. Foreground continuous profiling, full renderer memory, wake/fullscreen and genuine WebContent-crash recovery remain open.

## Required next acceptance

Run one QA app at a time, with other QA previews stopped and compilation finished. Capture a continuous 30-second native foreground profile with attributable WebContent/GPU processes, then 30 seconds hidden. Repeat cold starts and detail opening under the same conditions; profile the first-open >200 ms cost before changing visual effects. Check sleep/wake/fullscreen, real WebContent termination and retry. Preserve Hero/poster quality and all Studio/Calm/Space controls.
