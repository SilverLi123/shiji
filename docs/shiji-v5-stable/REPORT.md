# V5 Stable Beta — acceptance record

## Phase 1

Clean baseline `9d013bc`; separate branch `feat/shiji-v5-stable-beta`. V2.1 is already an ancestor; there are no missing source commits on that branch. Its unresolved share-extension/runtime limits remain unresolved. Existing V5 UI is retained.

Fresh baseline: 205 Python tests passed (32.946s), 46 Node groups passed, Swift native core and desktop ZIP exchange passed. Logs are in `evidence/baseline-*.log`.

The new GitHub Actions workflow runs the complete Python and Node suites for pull requests and V5 branch pushes. A macOS runner is necessary because an existing Python test compiles the real SwiftUI/Vision QR model using xcrun. Node 24 and pinned jsdom are development-only dependencies. PR targets the V5 feature baseline rather than main. Remote execution will be recorded only after it actually runs.

## Phase 2

Reproduction: launch the instrumented isolated native bundle in the background. The service becomes ready and loads 60 cards, but the initial Hero title has opacity 0.12 and blur(9px). `startup-before.jsonl` and `startup-before.png` show this actual state. Initialization unconditionally installed a backwards-filled finite intro while `document.hidden` was already true; there was no new visibility event to cancel it. Fix: defer the first intro until actual visibility, consume the session flag only then, and reject new finite Motion/Bits animations while hidden. Preserve all visible Studio animations. No delay/reload workaround.

`test_native_startup_motion.js` fails on the old implementation (4 finite animations vs 0), then passes with hidden startup, first visible intro exactly once, background cancellation and resume. Two historical foreground animation fixtures now explicitly use jsdom's visual mode. 47 Node groups passed.

Native window-close reproduction revealed SwiftUI `Window` terminates the app and service. Apple documents this behavior: https://developer.apple.com/documentation/swiftui/window . Changed the primary native scene to `WindowGroup`; actual close/reopen kept owned service PID 42490, requested start with owned=true, recreated the WebView, and displayed the same 100 persisted records. `startup-window.jsonl` records this. Service interruption was exercised by terminating only the verified temporary Python child; the native error appeared and the real Restart button recovered the same QA library. Screenshot: `service-recovery.png`.

Added bounded, private lifecycle diagnostics for service start/ready/exit, WebView creation/navigation/failure/content termination, app/window activation and close/reopen, plus teardown. All values are metadata; URLs, resource text and tokens are excluded. Native navigation cancellation is ignored; failures/content-process termination show an explicit user retry instead of silently reloading. Handler removal and delegate cleanup break the WebView/runtime retention cycle. Actual compiled Swift delegate tests cover these contracts and diagnostic rotation; tests passed (4.013s). macOS build passed.

Background native startup after the fix shows opacity 1 / filter none without a search repaint (`startup-after.png`, `startup-fixed.jsonl`). True foreground pointer access currently reports no available windows, although native AX actions and window captures work. Foreground timing, fullscreen/user wake and real WebContent crash recovery are not certified; the content-termination delegate is tested directly, not through a deliberate crash of unrelated WebKit processes.

## Phase 3

Real app pages use temporary Store/SQLite libraries containing 100, 1000 and 5000 explicitly marked pressure fixtures. They use the actual HTML, renderer and HTTP API. The optional probe is injected only by the QA server/bundle; normal pages do not load it. Samples are bounded to 600 frame intervals per phase and 240 reports. Values are metadata only. See `PERFORMANCE.md` and raw `perf-web-*.json`.

Measured initial browser script-to-render times: 1589.3 / 427.4 / 808.4 ms. Search unique record response: 22.4 / 56.8 / 48.3 ms. Development category: 56.5 / 236.2 / 82.6 ms. Rendering stays bounded at 60 gallery cards with all records available for real search/filter. These are individual instrumented runs, not percentiles across repeated cold launches. Browser automation and other isolated native previews may affect frame sampling; no 60 FPS claim.

Reproducible unnecessary work: every child-list mutation (including status text, particles and QA output) scanned all artwork and updated all loops. A new test failed with one unrelated full scan, then passed after the observer was limited to added/removed artwork and relevant overlay/stage attributes. Background CSS rules now pause all descendants/pseudo-elements, including legacy Hero loops, while retaining Studio rendering when visible. Native classified evidence confirms cssRunning=0 while hidden; the remaining running entries at startup were finite CSS transitions, not persistent artwork loops. The diagnostic probe now distinguishes these.

After the observer fix, a 5000-record run measured search 30.6 ms, category 64.1 ms, return-all 53.6 ms. Detail still has a first-open gap of 233.4 ms; subsequent gaps vary (33.7–67.5 ms). This is a remaining performance risk, not claimed fixed. Repeated close/open settles to zero proxy ghosts and bounded animation counts. Calm settles to zero running animations in the 5000-record run. 48 Node groups and the actual native build passed.

Native 1000 and 5000 background launches loaded all matching records and 60 cards with Hero opacity 1 / filter none. A 10.18 s actual process interval measured host CPU 0%, owned Python about 0.196% of one core. Host+Python RSS is recorded separately; WebKit helpers are not positively attributed and these numbers are not total renderer memory/foreground 3D CPU. An actual classified native foreground/background transition occurred, but its short frame sample is poor (p95 905 ms during simultaneous preview/tool activity); it is not representative performance certification. Mac foreground pointer tool still reports unavailable windows/timeouts after unlock. Physical fullscreen/wake and clean foreground profiling remain required.

Files: `shiji-v2-motion.js`, `shiji-v5.css`, `runtime-diagnostics.js`, native diagnostic whitelist in `App.swift`, `test_motion_observer_scope.js`, isolated `qa/web.py`, performance/native evidence. No resource, schema, ZIP or UI layout changes.

## Phase 4

Fresh final full run: 207 Python tests passed in 75.293 s. 48 Node groups passed. Swift native core / desktop ZIP exchange and actual Swift-to-Python HTTPS sync passed, including both directions, conflict handling, certificate-pin rejection and late-capture protection. All data, pairing secrets and certificates were disposable. No formal library/credentials were read or modified.

Expanded the existing ephemeral HTTP regression so persisted records feed the V5 renderer itself: real attachment cover priority, generated fallback beneath images, exact source/title/code escaping, stable deck IDs, empty deck and search. Added a real HTTP batch-delete/undo check preserving exact resource and attachment identity/bytes. An initial test assumed the newly saved GitHub record was first in API sort order; corrected the test to locate its stable ID, rather than changing real sorting. The V5 contract uses the existing development jsdom dependency (`npm ci`); no runtime dependency was added.

Actual browser acceptance: a separate empty temporary store displayed the empty state, Quick Capture saved `https://github.com/SilverLi123/shiji` through the normal UI, the HTTP state confirmed one persisted inbox resource, and its real detail drawer displayed exact source/title. Screenshots: `empty-library.png`, `capture-detail.png`. Failure/offline metadata behavior remains covered by actual storage/HTTP tests with controlled fetch outcomes; this run does not claim successful public metadata extraction. Existing extension tests exercise MV3 controller behavior and real paired HTTP capture/restart; installation in Chrome/Safari is not certified by these tests.

CI first macOS-only run 38035342138 reached the 15-minute cap during Python tests; Node was skipped, not passed. Read actual job logs. Reconfigured CI into complementary portable (205 test IDs, Linux) and native (2 compiled Swift/WebKit test IDs, macOS) partitions; no test is dropped or marked skipped. Added per-test output for diagnosis, pinned the installed Xcode 26.3 SDK for native tests, and retained the existing Python/Node versions. Local partition runs passed: portable 205/32.454 s and native 2/25.605 s. Also added native core/ZIP and real HTTPS sync to CI. Remote final results remain pending until an actual run completes.

Files: `.github/workflows/tests.yml`, `tests/run-ci.py`, `tests/test_v3_foundation.py`, `tests/v5_resource_contract.cjs`, `qa/web.py` empty-store option, browser/native screenshots and test logs. Next: consolidate acceptance limits, performance table, lifecycle reproduction and future iPhone share-extension plan; publish the review branch, never merge main.

### Phase 4 remote CI follow-up

Remote run 38037382562 passed its native job (compiled WebKit/QR contracts, Swift core/ZIP and real HTTPS sync). Its Linux job exposed Python 3.12 removal of `ssl.match_hostname`, plus an existing test that assumed the asynchronous startup snapshot had already finished. Replaced the certificate helper with a real verified in-memory TLS handshake against the renewed IP SAN, rejecting the old IP. Backup regression now polls the observable snapshot with a bounded 5 s deadline, without altering asynchronous production behavior.

An additional QA-probe regression found duplicate frame reports on pagehide after a completed sampling window. Delete completed bins; the red test (2 vs 1 reports) now passes. Final Node run: 49 groups. A simultaneous UI/native/build/Python run failed the unchanged network deadline assertion (0.823 s vs 0.45 s) and took 360.562 s. Kept the timing bound intact, stopped verified disposable preview hosts, switched only the QA browser to Calm, and the focused deadline suite passed. This under-load failure is retained in evidence; a final quiet full run follows. No unrelated apps or official services were stopped.

## Phase 5 — delivery / acceptance boundary

Final quiet full run: **207 Python tests passed, 34.254 s**. **49 Node groups passed** after the final QA probe fix (including the correct modal proxy class). Swift core/desktop ZIP and actual HTTPS sync passed; final macOS bundle build passed. Logs are `evidence/final-{python,node,swift,sync,build}.log`. GitHub runs **38038173955 / 38038178270** passed both complementary CI jobs on code commit `09f48ae`; see `ci-code-results.json`. Final delivery adds the report, performance table, screenshots/preview and a QA-only modal counter assertion; its checks are available on PR #1.

Draft review: https://github.com/SilverLi123/shiji/pull/1 . Base `feat/shiji-v5-spatial-ui`; head `feat/shiji-v5-stable-beta`. No main merge. Phase commits: `0bf55fb` baseline/CI; `5d0a1c0` native startup/lifecycle; `0a1b12e` measured motion/performance; `f692ebe` business regression/CI partitions; `09f48ae` remote-test/probe corrections; final report commit follows. No user uncommitted changes, formal library, fixed production ports or real pairing credentials were used.

Delivery references:

- [Actual performance and methodology](PERFORMANCE.md): single-run timings, RAF gaps, CPU/RSS scope, background pause and cleanup limits.
- [Future iPhone share-extension investigation](IPHONE_SHARE_PLAN.md): real host entry, hosting layout, expanded entitlements and three provider/save paths; no speculative fix claimed.
- [Native before](evidence/startup-before.png) / [native after](evidence/startup-after.png), [native 1000](evidence/native-1000.png), [native 5000](evidence/native-5000.png), [service recovery](evidence/service-recovery.png).
- [Real empty store](evidence/empty-library.png), [persisted capture detail](evidence/capture-detail.png), [5000-record gallery](evidence/gallery-5000.png).
- [Actual sampled motion preview](evidence/motion-sampled.gif): eight real CUA screenshots with original sampling intervals preserved. It is a sampled preview, not continuous native recording or a frame-rate measurement.

Resolved: indefinitely blurred background Hero; service termination on closing the sole window; missing navigation/content-termination retry state; WebView/runtime handler retention; unbounded/unprivate diagnostic history; unrelated full artwork scans; legacy background CSS loops; Python 3.12 certificate-test API and async-backup assertion race; duplicate QA frame windows / wrong modal proxy selector. Private diagnostics rotate at 1 MiB plus one prior log, without resource text or tokens.

Still open / not release-certified:

1. First detail open shows >200 ms gaps. Subsequent intervals also exceed one 60 Hz frame. Root cost needs a continuous native profiler run; transform usage does not prove smoothness.
2. Clean foreground native 3D CPU/total renderer memory, fullscreen, sleep/wake and a genuine WebContent crash remain unverified. Native screenshots and activation logs are real, but pointer automation repeatedly failed even after unlock. A direct delegate regression is not a genuine process-crash test.
3. Physical iPhone signing/App Group/system share, Wi-Fi and camera QR paths are not certified. Existing share-extension blank-page issue remains; iPhone source is unchanged.
4. Chrome/Edge installation and actual extension-host interaction still need manual installed-browser acceptance; paired capture API/MV3 controller tests passed.
5. During actual newly saved resource acceptance, one initial automated card click did not open the drawer; a subsequent click did. It was not isolated/reproduced consistently and is retained as an interaction observation, not silently certified as absent.
6. Heavy simultaneous UI/build activity caused the unchanged network deadline test to fail once (0.823 > 0.45 s); the focused suite and quiet complete rerun passed. Keep the bound and failure evidence. Native foreground samples under that activity must not be used as representative performance approval.

**Status: stable development candidate with verified automated/business baseline; complete product/native-performance/physical-device acceptance is not finished. Keep PR draft.** The large Hero, purple stage, Spatial Deck, pure-cover gallery, V5 posters, Studio/Calm and Space/Flat remain. All implemented management/sync/backup paths and schema 3 / ZIP 2 contracts are retained. No overall visual redesign or new feature was introduced.

Final changes beyond phase 4: README/current status and test-dependency order; this report; performance and share plan; actual sampled preview; QA-only correct modal proxy counter plus regression. Next work is acceptance/profiling of the listed gaps, before declaring release or starting new capture/cover features.
