# CI failure: lifecycle timing, not SQLite

Source: run38880059498/job116904354248, head579d447; retrieved actual decoded GitHub log. Ubuntu24.04.5 x64, Python3.12.15, Node24.21.0. Python portable281tests had one failure: `test_slow_capability_discovery_never_starts_legacy_full_library_poll`. Native and capture-recovery succeeded; Node was skipped by a combined job.

`JSDOM.fromURL()` resolves before external app scripts finish loading. The harness started its six-second condition deadline immediately, while a fixture's first capability fetch deliberately slept3300ms. Normal CI page requested root09:24:02, first capability09:24:05 (~3s script delivery). Slow case root09:24:08, capability09:24:14.499 (~6.2s), after the condition assertion expired. Its error contains only capture/tasks and website-previews because the delayed fetch was logged only after sleeping. Metadata/query requests later succeeded. No SQLite/FTS error is in the stack.

Reproduction: Docker Ubuntu24.04 arm64/Python3.12.3/SQLite3.45.1/Node24.21.0 against frozen579d447 source. The original slow case fails with the same stack; a three-second controlled app.js delivery fixture also fails. macOS characterization reproduces the controlled late-asset failure. Docker's architecture/Python patch differ from hosted x64/3.12.15; remote Actions is the exact additional acceptance environment, not assumed equivalent to local pass.

Fix is confined to the harness and workflow:

1. Wait for the real DOMContentLoaded lifecycle (existing Python subprocess30second upper bound retained).
2. Hold the first capability request with an explicit Promise barrier.
3. Trigger the actual captured desktop refresh callback while the request is held, and assert **observable absence of full resource/trash requests**.
4. Release the request, then keep the original six-second condition deadline for results and all downstream actual HTTP interactions.
5. Close cleanup releases a held barrier. No production timeout increase, no test skip, no changed FTS/security constraints.

Removing the production libraryReady guard in an isolated source copy makes the updated test fail at the full-library request assertion. This mutation confirms the test still catches its intended product regression; it is not merely faster by omitting the risky refresh.

Python and Node are now independent jobs. Python still installs Node/jsdom because Python's actual-page tests execute shipped browser scripts. Native Swift/HTTPS/build and100URL recovery jobs remain. Local Mac: full portable282tests and Node57groups passed. Ubuntu full portable/Node and remote candidate results will be appended once observed; no green claim before results.

Evidence: v62-ci-failure.txt, ci-red-ubuntu.txt, ci-red-mac.txt, ci-green-mac.txt, ci-mutation.txt. Container setup is test-only, uses verified official Node SHA256 and Ubuntu package Python; no application dependency or formal data.

Verified outcome: Docker full portable282tests + Node57groups passed. Remote run38892576373 at bddce2e has Python/Node/native/capture-recovery all completed/success; exact hosted Ubuntu x64 Python3.12.15 startup guard is green. Baseline is accepted for subsequent gallery measurements, not a final V6.3 release claim.
