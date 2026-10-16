# Gallery Performance & Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound mounted gallery DOM while retaining V5 art, variable-size masonry, input correctness and all query/selection semantics.
**Architecture:** Keep existing state/resources/query pages authoritative. Existing ShijiBits.pack and its FLIP/Tilt remain layout/motion owners; a geometry/viewport cache chooses mounted IDs and reconciles through existing stable cards. New QA separates lifecycle milestones and records real browser/native traces before changes and after.
**Tech Stack:** Existing Python/SQLite, vanilla JS/CSS, SwiftUI/WKWebView; development-only real-browser tests if needed, no application runtime dependency.
**Spec:** `docs/shiji-v6.3-gallery-performance/SPEC.md` (the user's complete request).

## Global Constraints

- Base579d447 on latest fetched feat/shiji-v6.2-search-scale; independent feat/shiji-v6.3-gallery-performance. No main writes/merge, no user work overwritten.
- Preserve SQLite schema3, ZIP manifest2, sync1, mobile JSON, capture/receipts and all canonical fields.
- Preserve large Hero, Spatial Deck, variable art heights/spans, pure covers, Studio/Calm,3D/Flat, detail continuity, hover/tilt and reduced motion.
- Temporary Store/data/ports/credentials only. Never use formal services or library.
- Actual CI failure logs and Ubuntu/Python3.12 reproduction precede fixes. Require complete remote green candidate before formal acceptance; do not mark unavailable native/device scenarios passed.
- Clear module commits, all docs/raw bounded metadata under this directory; large traces/video in ignored dist or CI Artifacts.

## Review Focus

- Pressed/focused/detail-origin cards must survive asynchronous enrichment or window eviction; test pointer-down→update→pointer-up and origin pin lifetime (Tasks3/4).
- Measured height updates, image decode and responsive spans cannot move the user's visible scroll anchor; test above-anchor height and resize (Tasks3/4).
- A changed query/revision must invalidate geometry, stale fetches and full-match selection without narrowing bulk operations to mounted nodes (Tasks4/5).
- Windowing must preserve assistive navigation, keyboard reach beyond the window and stable identity, including failure/hidden-page recovery (Tasks3/4).
- Empty results, list/board special cases and older/no-geometry test environments must have explicit behavior, not silent ordinary-grid assumptions (Tasks3/4).

### Task 1: Reproduce and fix portable CI lifecycle race
**Files:** tests/query_ui_integration.cjs, test_query_ui_integration.py; .github/workflows/tests.yml; qa/ubuntu.Dockerfile; evidence/CI diagnosis.
**Interfaces:** Actual HTTP page initialization with a controllable first capability request and actual desktop heartbeat callback. Six-second condition deadline remains; distinguish asset load from held-capability phase.
- [x] Reproduce original failure on Ubuntu24.04/Python3.12/Node24 with exact source and preserve version/timeline evidence; no guessed SQLite changes.
- [x] Replace wall-clock fixture delay with a first-request barrier; drive heartbeat before capability release and assert no full-library requests. Include controlled late asset-load characterization and mutation that removes readiness gate must fail.
- [x] Split Python and Node CI jobs, preserve native/capture jobs; full local/container suites, module commit, push isolated candidate to run required Actions, read real results. User's explicit request to run GitHub Actions authorizes this candidate push; no shared/main merge.

### Task 2: Capture V6.2 performance and audit geometry/motion
**Files:** qa/serve.py, probe/tracing tools, BASELINE.md, evidence/before metrics.
**Interfaces:** Frozen base579d447, real Store1K/5K/20K/50K; same deterministic data and input scripts. Milestones include input/debounce/fetch/parse/apply/reconcile/layout/post-paint; real trace distinguishes JS/style/layout/paint/composite/decode/GC when tooling exposes it.
- [ ] Record multi-round60/300/600/1020/2000 browsing, repeated search/filter/detail/scroll; raw DOM peaks, long tasks/frame gaps, anchor deltas and heap where exposed.1K cannot contain2000unique rows; record not-applicable rather than duplicate fake records.
- [ ] Audit existing ShijiBits/stable-cards/motion lifecycle and CSS measurements. Freeze original code and document measured bottlenecks before gallery implementation.
- [ ] Finalize window geometry/measurement/anchor/pin contract in ARCHITECTURE.md, then commit baseline/tools.

### Task 3: Geometry cache and minimal working window
**Files:** static/gallery-window.js (geometry/viewport lifecycle only), resource-bits.js, stable-cards.js, app.js/index.html, necessary existing CSS; tests/test_gallery_window.js plus real-browser fixture.
**Interfaces:** `setItems(entries,key)` references existing resource IDs/display signatures; cache rectangles generated by ShijiBits.pack; `visible(viewport,overscan,pins)`; one reconcile callback mounts IDs; total grid height represents all loaded rows. Actual measurements update cache by ID/width/signature; no second resource model or FLIP owner.
- [x] RED: variable heights, spans,1/2/3columns, overscan/unmount/remount, append, reorder and total height; integration asserts actual DOM bounded after1020+rows.
- [x] Implement bounded real-DOM measuring of new/invalid cards, cached packing, viewport range/overscan, resize and image ratio invalidation. Preserve V5 geometry and anchor before/after changed heights.
- [ ] Verify actual browser geometry against original reference within tolerance, no blank fast scroll or growing DOM; module commit.

### Task 4: Interaction, focus and transition lifecycle
**Files:** existing app/query integration/gallery/motion/bits hooks, gallery-window controller; targeted real DOM tests.
**Interfaces:** Pin IDs for pointer/focus/detail-origin lifetimes; existing motion completion or close releases pin, no detached origin before measurement. DOM changes never redefine selection or query results. Keyboard can ensure an ID mounted before focusing.
- [ ] RED: click/enrichment race, quick save/open, repeated/late detail, close/anchor return, focus across viewport, background/resize, pagination409/revision/filter/selection conflicts, reduced motion.
- [x] Add minimum lifecycle hooks, cleanup cancelled/closed proxies, focus/scroll preservation; keep list/board special cases explicitly tested.
- [ ] Run targeted and full Node/API regressions, commit.

### Task 5: Broad search and incremental render cost
**Files:** app.js/query-integration.js/stable-cards.js/shiji-v5.js, optional query/index changes only where tracing proves need; timing QA and regressions.
**Interfaces:** Existing query API/revision semantics unchanged; resource/display signature cache and bounded mounted work, global controls/deck update only when inputs change.
- [ ] Measure phase costs before changing each bottleneck; test HTML cache invalidation, highlights, metadata counts and stale responses.
- [ ] Remove proven repeated global work/DOM scans, preserve title accuracy and full search scope. Compare same queries/versions and actual presented milestones, not only backend medians.
- [ ] Full suites and module commit.

### Task 6: Final scale, native and branch review
**Files:** REPORT.md/PERFORMANCE.md/ARCHITECTURE.md, raw evidence and QA instructions; necessary regression fixes.
**Interfaces:** Identical before/after data/scenes/modes,3+ rounds for key cases; real foreground visibility is prerequisite for native foreground metrics.
- [ ] Run required1K/5K/20K/50K and60–2000scenarios, actual UI interactions, traces/process attribution and recordings where tools permit. Clearly separate background/automatic/real-input and interference.
- [ ] Python/Node/real-browser/SwiftCore/HTTPS/Mac build, Ubuntu and actual GitHub Actions green on final candidate; preserve known native/detail/exchange limits.
- [ ] Fresh whole-branch review required by executing-plans, single meaningful regression fix pass, final commits/report. Summarize solved/improved/remaining, visual/interaction regressions and formal-PR readiness honestly.
