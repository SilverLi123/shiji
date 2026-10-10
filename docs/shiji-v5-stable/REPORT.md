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
