# V5 Stable Beta — acceptance record

## Phase 1

Clean baseline `9d013bc`; separate branch `feat/shiji-v5-stable-beta`. V2.1 is already an ancestor; there are no missing source commits on that branch. Its unresolved share-extension/runtime limits remain unresolved. Existing V5 UI is retained.

Fresh baseline: 205 Python tests passed (32.946s), 46 Node groups passed, Swift native core and desktop ZIP exchange passed. Logs are in `evidence/baseline-*.log`.

The new GitHub Actions workflow runs the complete Python and Node suites for pull requests and V5 branch pushes. A macOS runner is necessary because an existing Python test compiles the real SwiftUI/Vision QR model using xcrun. Node 24 and pinned jsdom are development-only dependencies. PR targets the V5 feature baseline rather than main. Remote execution will be recorded only after it actually runs.
