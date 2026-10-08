# Phone–computer sync implementation plan

**Goal:** Pair the existing native phone and desktop candidates and synchronize real resource metadata and attachment bytes without losing concurrent edits.

**Architecture:** Separate optional desktop HTTPS listener; pinned certificate and revocable per-device bearer token; phone three-way resource merge and guarded remote/local commits. JSON schema3 and backup manifest2 remain unchanged. No third-party runtime dependency.

**Tech stack:** Python stdlib SQLite/ssl/http.server; system openssl for generating a local certificate; Swift Foundation/Security/URLSession/SwiftUI.

1. Desktop sync engine (`desktop-app/mobile_sync.py`): consistent revision snapshots, immutable attachment staging, guarded transactional upserts and retry receipts. Add regression tests before implementation and exercise failures with temp Store instances.
2. HTTPS pairing and desktop controls (`sync_transport.py`, `desktop_service.py`, `desktop/App.swift`): default-off listener, expiring one-time pairing, device revocation, copy code/QR, explicit status. Keep existing origins and listener restrictions. Test protocol boundaries over real TLS.
3. Phone merge/storage (`Shared/SyncMerge.swift`, `Library.swift`): snapshot-based merge, conflict representation, ID/url matching and coordinated compare-and-apply. Add native core tests for concurrent changes, tombstones and attachment identity.
4. Phone transport and native UI (`App/ComputerSync.swift`, `ShijiApp.swift`, generator): exact-anchor HTTPS validation, Keychain, bounded file transfers, pairing/retry/auto-sync/conflict/disconnect. Test actual Swift URLSession against the isolated HTTPS server and compile both iOS targets.
5. Validate current desktop/mobile suites and builds; inspect native screens in one batched round, finish review, fix material findings, document behavior and limitations; package both source candidates and new macOS candidate without deploying or including test data.

All work is inline and sequential. Independent Impeccable review/documentation handoffs occur after implementation; implementation agents are not requested.
