# SHIJI V2 validation and evidence

Date: 2026-10-08. Branch: `feat/shiji-v2-motion-ui`. Baseline: clean `main` at `488d39e`. This report covers the local implementation and the checks available in this environment. It does not certify every device, OS version or existing product feature manually.

## Automated results

| Check | Command / scope | Actual result |
| --- | --- | --- |
| Python backend | `cd desktop-app && python3 -m unittest discover -s tests` | **202 tests passed**, 53.076s. Includes five new guarded metadata/persist-first tests. |
| Node DOM/controllers | `cd desktop-app && npm test` | **37 test groups passed** on final motion source. Includes per-URL timeout/retry recovery, rejected animation cancellation, inert/bounded exit proxies, real modal hooks and native preference bridge script. |
| Swift native core / desktop ZIP exchange | `cd mobile-app && python3 Tests/run.py` | **Passed**. Native data presentation and offline Quick Capture assertions included. |
| Real HTTPS sync | `cd mobile-app && python3 Tests/sync_integration.py` | **Passed**. Initial union, explicit conflicts, exact tags, attachment verification, both directions, wrong-certificate pin rejection and late local capture protection. Temporary stores and credentials only. |
| macOS build | `cd desktop-app && python3 desktop/build.py` | **Passed**, final signed local app in `desktop-app/dist/Dev Resource Library.app`. Not installed over the user's formal app. |
| iOS Debug simulator | `xcodebuild -project Shiji.xcodeproj -scheme Shiji -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- CODE_SIGNING_REQUIRED=NO ARCHS=arm64 build` | **BUILD SUCCEEDED**, including final native curtain/flight/offscreen visibility source. |
| iOS bundle structure | `python3 Tests/check_bundle.py build/DerivedData/Build/Products/Debug-iphonesimulator/Shiji.app` | **Passed**: matching app/share App Groups, opaque semantic light/dark accents, compiled AppIcon. |
| iOS Release device compile | `xcodebuild -project Shiji.xcodeproj -scheme Shiji -configuration Release -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath build/ReleaseData CODE_SIGNING_ALLOWED=NO build` | **BUILD SUCCEEDED** on final source. This is an unsigned device build, not an installed or distributed iPhone app. |
| Diff hygiene | `git diff --check` | **Passed**. |

Builds/tests initially caught a duplicate native preference declaration and an unhandled rejected `Animation.finished` promise when canceling infinite loops. Both were corrected, then the final affected builds and full Node suite passed. Logs were retained in `/tmp/shiji-v2-delivery-*.log`, `/tmp/shiji-v2-expanded-ios-debug.log`, `/tmp/shiji-v2-final-python.log`, `/tmp/shiji-v2-expanded-native.log` and `/tmp/shiji-v2-final-sync.log`; generated credentials are not committed as evidence.

## Actual running UI checks

All browser changes were performed against disposable SQLite stores. The five original websites were represented by explicit QA fixtures using existing local preview assets; a real prompt fixture checked long Chinese titles and the literal tag `New, exact`. Actual capture requests added QA URLs to those stores. No Demo localStorage data replaces the real resource API.

| Surface / scenario | Actual observation | Evidence |
| --- | --- | --- |
| Desktop Web | Settled dark gallery/Hero, preserved real navigation, three content types, detail, search and focus. Actual list/board/select controls exercised. | `motion-desktop.png`, `p5-gallery.png`, `p5-list.png`, `p5-board.png`, `p5-detail.png` |
| Responsive Web | CSS viewport targets 1440×900, 820×1180, 390×844 and 340×740. Client/scroll widths 1432/1432, 812/812, 382/382 and 332/332 after the overflow fix. Latest mobile motion capture again measured 382/382. | `p5-web-desktop.png`, `p5-web-tablet.png`, `p5-web-mobile.png`, `p5-web-small.png`, `motion-web-mobile.png` |
| Empty store | Real zero-resource store, visible empty guidance and actions. | `p5-empty.png`, `p5-empty-content.png` |
| Large store | 1000 real disposable records; existing browse window renders 60 initial cards. Layout test separately checks 1000-card packing with two bounded layout flush phases. | `p5-large.png`, `p5-large-gallery.png` |
| Quick Capture | Actual save 7→8 records, modal closed and one visible flight after persistence; duplicate save retains URL and readable error. | `motion-capture-flight.png`, `p5-capture-duplicate.png` |
| Studio / Calm | Actual category burst/exit/stamp, detail proxy, modal entry and success flight; Calm produced **zero** decorative proxies/particles/rings/stamps. Browser error console empty on the checked final interactions. | `motion-category.png`, `motion-detail.png`, `motion-calm.png` |
| Native Mac | Dedicated `local.silver.shiji.v2.qa` app, temporary data and port 61739. Neutral glass/lime capture controls readable collapsed and expanded in active window. Final bundle contains current motion assets and preference bridge. Actual Calm toggle disabled replay and the dock still expanded correctly. | `p5-native-mac-active.png`, `p5-native-mac-expanded.png`, `motion-native-mac-calm.png` |
| Native iPhone | Agent-owned iPhone 17/iOS 27 simulator. Actual dark/light galleries, large Dynamic Type, Reduce Motion/high contrast/reduced transparency/VoiceOver checks, resource-first accessible detail and actual offline URL capture. | `p3-iphone-dark.png`, `p5-iphone-light.png`, `p5-iphone-large-type.png`, `p5-iphone-accessibility.png`, `p5-iphone-accessibility.txt`, `p5-iphone-detail.png`, `p5-iphone-capture.png` |
| Native motion follow-up | Running native geometry and replay/category interaction recorded; OS Reduce Motion checked. | `motion-iphone-studio.png`, `motion-iphone-reduced.png`, `motion-iphone-interaction.mp4` |

Evidence paths are under `docs/shiji-v2/evidence/`. Responsive PNG raster dimensions are scaled by the browser capture (approximately 0.98), e.g. the 390×844 CSS viewport produces a 382×827 image. CSS viewport sizes are not claims of exact reference raster parity. Native screenshots include the Device Hub window and its inspector, not just the simulated screen.

Final evidence inspection found an inherited list-preview margin overlapping the title. A scoped CSS fix removes that margin, sets a 14px column gap and fits text previews to the thumbnail. Actual running DOM measured preview right 363.99px and body left 377.98px; the refreshed `p5-list.png` shows separated titles. Node's 37 groups and the macOS build passed again after this CSS change. The independent motion review preceded this layout-only correction.

The 18-second `motion-iphone-interaction.mp4` contains actual recorded frames 0–18s from the owned simulator's 30.835-second recording. It shows native brand replay, moving geometry and category switching; save flight and delayed recovery are not demonstrated in this recording. `p5-iphone-interaction.mp4` is an earlier separate actual 18-second category interaction recording. No generated or reconstructed frames were added. Video was opened in the local browser and displayed the real App screen.

`motion-intro-start/middle/end.png` and `motion-brand-intro.png` are early transient samples of the curtain/blurred headline, not settled page captures or proof of an entire animation sequence. Earlier P1–P4 screenshots describe those stages; the final error contrast evidence is `p5-capture-duplicate.png`.

## Independent review

- Original finish review requested three material fixes: error contrast, native Mac capture contrast and pending Quick Capture recovery. The final verdict was **ship for those three findings only**, each scored resolved. A→B→A timeout recovery was independently rerun.
- A fresh reviewer examined the user's additional full-motion request, current motion sources, eight actual captures and the isolated Studio/recovery tests. Verdict: **ship for the motion-integration scope**, no material fixes identified.
- Neither verdict is a claim of complete platform/device/performance acceptance. Final build results are the concrete local results above.
- One Web design detector pass ran earlier. Remaining advisories concerned the user-pinned world / inherited visual tokens; native code is outside that detector. No repeated detector/polishing loop was used.
- A separate documenter extracted the final implemented system into both token-bearing DESIGN.md files and schemaVersion2 sidecars, retaining PRODUCT facts.

## Remaining limits and provenance

Existing Share Extension blank-page behavior is unresolved. Mac inactive-window glass, physical devices, additional iPhone classes and older OS fallback branches were not actually inspected. Native save-flight runtime and actual delayed-network recovery UI remain unrecorded; native Calm/dock interaction was checked but animation timing was not instrumented; source/build/controller evidence is not presented as live UI proof. Sustained 60fps, battery and memory benchmarks were not measured. Extension regression and HTTPS sync are automated; live production pairing was not attempted.

An early native Mac binding incidentally selected the already-running same-bundle window on port 8782; inspection stopped without resource/pairing actions. All subsequent QA used the dedicated bundle, temporary stores and separate ports. No production library, credential, schema or manifest was modified, no remote push/merge was performed, and no third-party runtime was added.
