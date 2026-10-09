# SHIJI V2.1 — Motion & Visual Polish

Date: 2026-10-09. Baseline: `feat/shiji-v2-motion-ui` / `cc91d1a54dc0d7e7c858412e65aeb46500fd70ba`. Working branch: `feat/shiji-v2.1-motion-polish`. The initial worktree was clean.

## Execution plan and safety

1. P0: read the current design, rendering, persistence, native and test contracts; rerun Python/Node/Swift; capture an isolated baseline.
2. P1: derive tool/code/prompt/editorial/file covers from real fields, preserve image precedence/keyed IDs/Bits layout; refine connected controls; capture the same fixture before and after.
3. P2: refine the existing motion owners, interruptions and modal exits; measure frame intervals, scrolling and pause behavior rather than claiming 60fps.
4. P3: native SwiftUI cards/themes/capture/navigation polish, preserving the existing large brand Hero.
5. P4: diagnose the actual Share Extension blank page, verify real extension launch and URL/text/image import with App Group persistence and recovery.
6. P5: complete regression and isolated UI matrix, actual screenshots/recordings, design documentation and local commits. No push or merge authorized.

The homepage large headline, purple geometric stage, ticker and brand motion are pinned. Their markup and layout sizing must remain intact. No production database, 8765/8782/formal ports, user device data or real pairing credentials are used. All QA resources are explicitly labelled test fixtures in temporary stores. SQLite schema 3 and ZIP manifest 2 remain unchanged. No third-party runtime is added.

## P0 — baseline

- Git status clean; independent feature branch created from the requested baseline.
- Python: `python3 -m unittest discover -s tests` — **202 passed**, 32.125s.
- Node: `npm test` — **37 groups passed**.
- Swift/core/desktop ZIP interchange: `python3 Tests/run.py` — **passed**.
- Logs: `/tmp/shiji-v21-baseline-python.log`, `/tmp/shiji-v21-baseline-node.log`, `/tmp/shiji-v21-baseline-swift.log`.
- Existing known problem: native Share Extension blank page. Prior compilation/core tests do not verify the extension's system-hosted UI. Physical devices, old-OS fallbacks and sustained frame rate remain unverified baseline limits.

## P1 — desktop presentation completed

## P2–P5 — pending

P1 changes: `static/shiji-v2.js` adds five escaped real-field cover presentations; `app.js` delegates fallback rendering and preserves real image priority; `static/shiji-v21.css` contains scoped visual refinements; `index.html` loads that stylesheet; `tests/test_v21_covers.js` exercises content integrity, code whitespace, bounded previews, malicious input, no mutation and real image/failure precedence. Hero markup and all existing V2 Hero sizing rules are unchanged. Existing resource IDs and keyed/Bits rendering remain the owners.

Initial inspection found inherited `span` typography overriding cover labels; specificity was corrected, and the cover metadata reserves space for the favorite control. Baseline fixture: eight explicitly labelled temporary records, including self-authored code/prompt, a GitHub URL, long title, broken cover and existing local image bytes. No fixture is shipped as production seed data.

Node: **38 groups passed**, including the new cover group. Baseline Python/Swift remain passed; P1 changes only Web presentation. Before/after captures use the same temporary SQLite store and resource IDs. Responsive CSS target width 390 measured client/scroll 374/374 in this browser's scaled environment.

Hero invariant: the same 1440×1000 target viewport measured Hero 1093.93×427.18, purple stage 533.97×427.18, heading 63.5294px / 152.45px high before and after. Screenshots: `before-desktop-hero.png` / `after-desktop-hero.png`, `before-desktop-gallery.png` / `after-desktop-gallery.png`, `before-mobile-gallery.png` / `after-mobile-gallery.png`, and `p1-code-detail.png`. No P2 performance or native/share success is claimed at P1.

## P2 motion thesis

The large brand entrance and continuously moving purple stage remain the focal moment. Operational continuity uses the existing Bits FLIP only; routine card entry/reorder becomes shorter with smaller blur. Text-based covers must preserve their actual typography through the detail proxy. Modal exits are quicker than entry and use a single inert visual proxy after native close, so real close/focus does not wait. Repeated open/close/category/save events cancel old decoration. Metrics use actual RAF intervals and long-task observations in an isolated, QA-injected probe; they are not GPU FPS measurements.

## P2 — motion integration completed; measured limits retained

Changed `static/shiji-v2-motion.js`, `resource-bits.js`, `shiji-v21.css`, updated the existing Studio assertion and added `tests/test_v21_motion.js`. Bits remains the sole card transform/layout owner. Reorder 480ms; enter 520ms / 3px blur / capped 175ms stagger; exit 240ms. Detail 560ms clones the actual escaped cover hierarchy into one sanitized inert proxy. Modal enter 320ms, exit 160ms with native close/focus immediate; reopening and Calm cancel proxies and owned animations. Search expansion uses one interruptible 220ms FLIP on the search field only. Real save/favorite success hooks are unchanged. Hero motion and sizing are unchanged.

Node **39 groups passed**, including 1000-card/two-layout-flush contract and actual controller cancellation tests. The first run caught the minimal layout mock's absent ownerDocument; optional document listeners preserve that API/test contract without removing any assertion.

QA-only probe `qa/metrics.js` is injected by a temporary server, never linked from App HTML. Real temporary SQLite contains 1000 records; measured current filter 500, rendered cards 60, Chromium 155 viewport 1255×706. Raw results: `evidence/p2-performance.json`. Restricted action windows: category n=155, P50 16.7ms / P95 32.3ms / max 50.1ms, 8 intervals >25ms; scroll n=76, P50 16.7ms / P95 17.4ms / max 33.4ms, one >25ms. One observed 57ms long task. These RAF intervals include tooling and do not certify GPU FPS, all browsers or sustained 60fps. Offscreen Hero loops were all paused. Hiding the verification browser still reports document visibility=visible, so an actual hidden-tab measurement was unavailable; controller background pause/resume is covered by regression tests and is not represented as live proof.

`p2-desktop-interaction.mp4` uses 44 actual CUA screenshots and their original timestamps (4.944s), without generated/interpolated frames. It is a sampled runtime capture (about 9 samples/s), not a 60fps recording. It shows actual category switching and a real code-card detail transition. `p2-rich-detail-transition.png` and `p2-large-gallery.png` are runtime screenshots. P3/native and system-share behavior are not claimed by this stage.
