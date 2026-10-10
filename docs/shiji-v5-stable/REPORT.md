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
