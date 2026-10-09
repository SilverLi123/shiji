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

## P3 — native implementation built; runtime acceptance pending

Changed `mobile-app/App/ShijiApp.swift`, `Shared/Library.swift`, `Tests/main.swift`, native `DESIGN.md`/sidecar and README. The native large Hero source is byte-identical to the requested V2 baseline. `NativeResourceCover` derives tool/code/prompt/editorial/file presentations from real saved fields; LocalImage still wins. Code previews retain indentation/empty lines and are bounded to seven lines of 160 characters. Full code/prompt content is selectable in detail. Tool colors adapt to light/dark; native system typography and accessibility-size fallback remain. Gallery previews are 238pt, 160pt at accessibility sizes, without shortening Hero. The capture actions sit in a full-width adaptive safe-area rail above the native TabView.

Swift core + desktop ZIP interchange **passed**, including new exact-host/whitespace/bounded-preview/no-serialization regressions. Simulator Debug, unsigned iPhoneOS Release and compiled App/share matching App Group checks **passed**. Actual production Swift HTTPS sync tests **passed**: both directions, attachments, explicit conflicts, wrong pin rejection and late-share protection. `before-iphone-hero.png` is the actual pre-change owned simulator. **No native after-image or recording is available yet.** Device Hub AX/screenshot/input repeatedly timed out, including fresh binding, app path and a reset tool session. Process sampling shows its main thread servicing its event loop; this does not establish whether the Mac is locked. The user has been asked to keep the Mac unlocked and the owned QA window open. P3 is not marked visually accepted; light/dark, largest Dynamic Type, TabBar/dock occlusion and native motion remain pending actual interaction.

## P4 — diagnosis prepared; blank page remains unresolved

No speculative hosting rewrite is shipped. Existing evidence says the extension controller was instantiated and read providers, so a principal-class failure is not established. `ShareViewController.swift` now logs root/hosting dimensions, window presence, alpha and hidden state without content or credentials. It also throws if a save callback outlives its controller/context, instead of reporting success through a nil optional call. Debug and unsigned iPhoneOS Release builds **passed** after this diagnostic change (`/tmp/shiji-v21-share-diagnostics-build.log`, `/tmp/shiji-v21-final-release-diagnostics.log`).

`qa/share-host.swift` and guarded `qa/install-share-host.py` provide a QA-only UIKit host of the real system UIActivityViewController for URL, text, image and unsupported data. It is absent from production targets and only installs to a simulator explicitly named Shiji iPhone QA. The guarded host installer also compiled and installed successfully on the owned simulator (`/tmp/shiji-v21-share-host-install.log`). Prepared/compiled does **not** count as an actual extension test. Required next run: open each system share sheet, select Shiji, observe loading/form/error, cancel and verify unchanged App Group bytes; save URL/text/image and verify real App Group records/attachment bytes and main-App visibility; reopen after failure. These operations could not be performed while Device Hub input was unavailable. **Share blank-page root cause and fix are not claimed.**

## P5 — available regression completed; acceptance remains partial

- Python: **202 passed**, 79.128s; `/tmp/shiji-v21-final-python.log`.
- Node: **39 groups passed**, including cover/motion/cancellation/1000-card tests; rerun after label/contrast fixes passed (`/tmp/shiji-v21-final-node-after-contrast.log`).
- Swift/core and real desktop ZIP interoperability: **passed**, `/tmp/shiji-v21-p3-swift.log`.
- Actual native URLSession / temporary HTTPS desktop integration: **passed**, `/tmp/shiji-v21-final-sync.log`.
- macOS ad-hoc signed app build: **passed**, latest labels/contrast included (`/tmp/shiji-v21-final-mac-after-contrast.log`).
- iOS Debug / unsigned Release / App Group bundle consistency: **passed** as described above; no signed device IPA or physical-device claim.
- Desktop video decoded and displayed in the verification browser. It is a sampled actual UI capture, not a 60fps recording.
- Actual web missing-cover/image/long-title/filter/search/Calm/detail screenshots and 1000-row timings are in evidence. `p5-empty-search.png` is a no-match search, not an empty database. `p5-empty-library.png` records a separate zero-record temporary Store and its first-capture/file entries. Original requested viewport control did not apply to existing tabs (actual width 1412); therefore no tablet claim is based on those dimensions. `p5-tablet-hero.png` and `p5-mobile-hero.png` use an explicit QA-only iframe of the real running app: measured 1024/client1016/scroll1016 and 390/client382/scroll382. They validate responsive CSS, not native SwiftUI. Input into that cross-origin frame was unavailable, so interaction evidence comes from the top-level app.
- Static Impeccable scan: **29 primary findings**, mostly baseline cascade/context approximations plus real small labels. The live gallery had no nonempty visible text using the flagged old muted/error colors. Functional nav/motion/cover labels are now 11px; error/recovery colors and demo surface are themed. The existing pinned Hero ticker edge bleed, geometric stage, logotype/caption typography and animation identity are intentional and remain. The code stack is now explicitly documented. A clean detector pass is not claimed; no repeated scan was used to polish indefinitely.

Remaining acceptance risks: actual Share Extension is a blocking product defect; no native after-captures/recording or live system-share chain; exact background-tab measurement unavailable; category frame P95 still 32.3ms; old OS and physical iPhone not validated. Next action is restoring Device Hub access, completing P3 runtime evidence, then diagnosing/fixing and verifying P4 before claiming full V2.1 delivery. No push or merge performed.
