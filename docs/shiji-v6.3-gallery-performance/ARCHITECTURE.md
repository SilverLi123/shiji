# V6.3 gallery contract

## Evidence before implementation

Frozen product579d447, real Store fixtures copied into disposable databases. Chrome155 headless fresh profiles, actual HTTP/query/UI; automated input, not physical Mac or WKWebView. The diagnostic trace is intentionally separate from untraced timing runs. Inclusive trace events overlap and are not exclusive CPU totals.

At1020 mounted cards, the first untraced5K run records106.4ms synchronous render and250.1/316.6/383.4ms scroll rAF P50/P95/max. At2040 cards:269ms render and949.9/1316.7/1433.3ms gaps. Input-to-double-rAF after that heavy scene is2621ms for the mixed query. These are observations, not stable FPS claims. Final report aggregates all rounds and flags interference.

Trace attribution: Layerize33.84s and draw-properties21.47s inclusive over55.66s trace; Layout0.75s, style0.93s, DecodeImage4.1ms. Offscreen nodes retain preserve-3d and will-change artwork even after their CSS animation is paused. This implicates retained composition work; it does not prove one CSS declaration is the sole cause. Each append also calls card() for all accumulated records; search highlighting scans all mounted nodes once per loaded record.

## Ownership

The existing resource/query state is the only resource authority. The window controller stores references to the current display sequence, cached geometry and a bounded presentation cache. It never filters, sorts, selects, fetches or changes resources. Full-match selection and revision checks remain in query-integration.js. Server API, SQLite schema3, ZIP2 and sync1 stay unchanged.

ShijiBits remains the only owner of layout/FLIP/Tilt. It supplies width, columns, spans and gaps to the window controller, which uses the existing ShijiBits.pack; Bits animates mounted positions. Scrolling reconciles only the window and never invokes global render or cancels an in-progress detail transition.

## Geometry and measurements

Window only the V5 pure-cover grid. List and project-board retain their existing local rendering because visible descriptions/lane flow need a different measurement contract; this limitation is explicit. Zero document-width environments bypass controller creation and use the existing path. A secondary positive-width/zero-profile-measurement edge was identified by review and is deferred; see REPORT.md rather than treating every no-layout environment as supported.

Measure presentation skeletons with the actual card/wrapper/preview CSS, including wide and compact styles, rather than assuming a universal height. Frame-mode children are positioned absolutely and descriptions are hidden; these measurements describe all frame cards. Fit mode uses per-resource decoded image ratios, initially the same1.6 fallback as existing Bits. Mounted actual heights are checked and cached. Image load/error, width/column/density/preview-mode changes invalidate appropriate measurements. Geometry retains stable IDs and the full loaded height; mounting includes viewport, overscan and pinned interactions.

Before height/width/list changes, capture a visible stable-ID anchor and its screen offset. After packing, correct scroll instantly (without inheriting the page smooth-scroll CSS) by that anchor's delta when the query identity is unchanged. Query changes intentionally reset geometry identity and do not restore a card from old results. Native browser scroll anchoring is disabled only on this explicitly anchored grid.

## Lifecycle and access

Pointer-down pins its stable article through pointer-up/click dispatch; a global render fence also retains the pressed hit area and existing pointer capture when metadata changes ordering. The latest presentation flushes once after the ensuing click; blur/cancel/hidden teardown release it. Focus pins the active article. Hydration/detail-origin has a separate pin until close, cancellation or replacement. A detail ghost uses the existing motion owner; scroll mounting does not call beforeListUpdate. Deletion/query changes invalidate obsolete pins. Keyboard navigation can mount the adjacent logical record before focusing, including across a DOM boundary. Selection is a resource-ID set, never the mounted node set.

Viewport callbacks are one rAF, cancel on hidden/pagehide, refresh on visibility/resize. Unmounted nodes, observers, animation proxies and handlers are released. The presentation cache is bounded; geometry is proportional to loaded summaries. No second FLIP, tilt, cover engine or runtime dependency.

## Validation and rollback

Pure geometry tests cover variable heights/spans/overscan/append/reorder. Real Chrome tests use actual CSS and business endpoints for mount bounds, remount, image resize/anchors, pressed-node races, details, focus and selections. Existing tests cover server cursor/revision/backup/sync semantics. Development-only Playwright is excluded from application packaging. Removing the window script and integration restores the original DOM path without data migration.
