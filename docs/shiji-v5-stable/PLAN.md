# V5 Stable Beta stabilization

Baseline: `feat/shiji-v5-spatial-ui`, `9d013bc`. Working tree was clean. Isolated integration checkout: `/Users/silver/shiji-card-restoration`; stabilization branch: `feat/shiji-v5-stable-beta`. No official data, ports, or pairing credentials may be used.

1. Audit ancestry and retained tests; establish Python/Node PR CI and fresh Python/Node/Swift baseline. Commit phase 1.
2. Instrument service, WebView navigation, window lifecycle and front/background state; reproduce incomplete native painting; fix only demonstrated causes with regression tests. Commit phase 2.
3. Measure actual startup, search/category, scrolling, process CPU/RSS, pause and transition cleanup against 100/1000/5000 persisted QA records. Improve demonstrated bottlenecks. Commit phase 3.
4. Exercise capture/extension, metadata conflicts, covers, browsing, bulk recovery, ZIP backup/restore and HTTPS sync in temporary stores. Commit phase 4.
5. Consolidate measured results, native screenshots and remaining physical-device acceptance, plus the iPhone share-extension investigation plan. Commit phase 5.

The approved large Hero, purple stage, spatial deck, pure covers, content-driven V5 posters, all management flows, Studio/Calm, Space/Flat, schema 3 and ZIP manifest 2 are invariants. No V2 toggle, new parallel motion engine or runtime dependency. Remote CI/PR may only be claimed after an actual GitHub result; native build success is not runtime acceptance.

Ancestry audit: the current V5 branch already contains the V2.1 motion/native/test branch (no commits unique to V2.1). Share-extension blank-sheet diagnosis and physical iPhone acceptance remain unresolved, not silently merged as completed work.
