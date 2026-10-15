# Smart Capture Engine Implementation Plan

> Execution: implement inline in the existing isolated worktree, as explicitly requested by the user. No approval pause, parallel agent work, remote push, or main merge.

**Goal:** Save links immediately and durably, then enrich them with recoverable, cancellable local work without overwriting user edits.

**Architecture:** One SQLite-backed scheduler and one worker own metadata and preview tasks. The existing Store remains the only resource model. Network work happens outside database locks; final application and task completion share a transaction/lease fence.

**Tech Stack:** Python standard library, existing SQLite, JavaScript/CSS, SwiftUI/WKWebView.

**Spec:** User's 2026-10-14 SHIJI V6 Smart Capture Engine request in this conversation.

## Audit / baseline

- Local and fetched Next branch match `de06972346d9f1838bff0d2d91262f7b10c01577`; worktree initially clean. New branch: `feat/shiji-v6-smart-capture`, no upstream.
- `quick_capture.py` already implements durable-save-first and strict updatedAt/URL/attachment protection. Its optional enrichment is request-local, not recoverable.
- `preview_jobs.py` has one daemon worker, default-off persisted settings, but attempted IDs, results and failures are memory-only; each step scans full state.
- Browser clipping preserves existing identity/notes but downloads an explicitly selected remote image before saving the page; this must become post-save work. Screenshots remain local uploads.
- `capture.py` pins public DNS addresses, revalidates redirects, bounds requests/DNS/Chrome, and isolates Chrome behind a public-only proxy. Reuse these boundaries; do not add a production localhost exemption for fixtures.
- Resource JSON and iPhone App Group JSON remain schema 3. ZIP restore uses manifest 2 and reconstructs resources rather than trusting the archive's raw SQLite file. Sync transfers resources/attachments, not local settings or tasks.
- Existing quick-capture uncertainty reconciliation and stable resource nodes remain. Legacy enrichment helper stays a compatibility entry point; the HTTP endpoint will enqueue into the unified engine. No second background worker starts.
- V5.2 first-detail long frames and physical iPhone/extension acceptance limits remain open. This work does not claim to resolve them.

## Persistence / migration / rollback

Add optional `capture_jobs` and `capture_control` tables to the existing database, leaving `PRAGMA user_version=3`, resource payloads and ZIP manifest 2 unchanged. Jobs contain ID, resource ID, kind, normalized URL, expected updatedAt, attempts, nextAt, safe error code/summary, timestamps, lease token/expiry, suggestions and review state. Deduplicate by resource ID + URL + kind + initial resource version + normalized options; retain terminal history.

New website creation / URL change records its capture job in the same resource transaction. A failed transaction leaves neither a phantom resource nor a phantom task. Imports use the same Store write path; existing historical rows are not automatically sent to the network on migration. Legacy preview opt-in queues uncovered websites through indexed resource queries.

Tasks are **local derived state**, not authoritative synced content. JSON exports and sync exclude them. Raw SQLite snapshots naturally include the optional table; manifest restore does not import its jobs, credentials or leases. Old schema-3 databases/manifest-2 backups open unchanged. An older app ignores the additional tables. Rollback: stop the worker and remove the two optional tables; resource/attachment data stays intact. Re-enqueue is explicit after rollback rather than silently recapturing history.

One worker claims work in a short `BEGIN IMMEDIATE` transaction. A random lease token plus bounded expiry fences concurrent or late attempts. Expired running leases become retry/failed on subsequent polling/restart, never permanently running. A graceful stop invalidates its lease before returning; forced process termination recovers after expiry. Bounded network deadlines are shorter than the lease. Pause/cancel increments or invalidates the fence, so late I/O cannot publish files.

Any resource revision/URL/deletion/manual cover change during I/O wins: skip stale results. Only fallback titles and empty descriptions/favicon/source fields are filled. True covers win; external thumbnail URLs must be downloaded and structurally validated before being called local covers. Atomic commit errors remove only newly published files. Process death between file publication and SQLite commit remains a filesystem recovery consideration, not an asserted cross-file ACID guarantee.

Classification is an extensible local rule set. Store suggestions in the task, never silently change tags/category. Accept uses the displayed resource version, merges tags, fills only an unclassified category; ignore persists locally. Neither creates new categories nor changes sync.

## Global constraints

- Preserve V5 large Hero, Spatial Deck, cover-only gallery, Studio/Calm and Space/Flat.
- No production data, ports or real pairing credentials; fixtures use temporary stores, random ports and disposable identities.
- SQLite schema 3 / ZIP manifest 2 / sync protocol unchanged; no new runtime dependency, AI API, cloud service or replacement resource model.
- Record measured performance and actual UI separately from test/build success. Large recordings/traces remain temporary, not Git blobs.

## Review focus

1. Save/queue transaction failure: no success animation or orphan queue item.
2. Cancel/pause/edit during network return: no late metadata, attachment or suggestion write.
3. Leased worker death / second worker: no stale lease completion or duplicate cover.
4. Invalid/truncated/deceptive images and private redirects: no attachment or weakened SSRF policy.
5. Old backup/sync/manual metadata and uncertain browser response: identity and curated fields survive.

## Ordered modules and checks

### 1. Durable lifecycle

Files: `capture_jobs.py`, `storage.py`, `tests/test_capture_jobs.py`.
Interfaces: `enqueue_capture(c,item,kind='capture')`, `capture_status(limit=30,offset=0)`, `capture_action(body)`, `capture_step(kind=None)`.

- [x] Add failing real-Store tests for atomic enqueue, duplicate/stale jobs, leases, restart, cancel, pause and safe retry.
- [x] Implement optional tables, indexed claim, local controls and fenced commits; retain legacy preview API through this scheduler.
- [x] Run focused and full Python regression; commit.

### 2. Parsing, covers, suggestions

Files: `capture.py`, `capture_images.py`, `capture_rules.py`, `preview_jobs.py`, `tests/test_capture_engine.py`.
Interfaces: `capture_payload(url,cover_url='',need_cover=True)`, `validate_image(bytes,content_type)`, `suggest(resource,metadata)`.

- [x] Test real public-fetch boundary, local HTTP fixtures via test-only transport routing, invalid images, partial metadata, all manual edits and failures.
- [x] Implement bounded metadata/image parsing, canonical hints, rules, preview compatibility; keep all network outside Store locks.
- [x] Verify manifest-2 roundtrip and resource/sync compatibility; commit.

### 3. API and lightweight UI

Files: `server.py`, `static/capture-tasks.js`, `static/app.js`, `static/index.html`, CSS; Python API and Node DOM tests.

- [x] Test save-first clipping, duplicate URL reconciliation, state/actions and versioned suggestion review through real APIs.
- [x] Route existing enrichment/preview APIs into one scheduler; add `/api/capture/tasks` GET/POST, compact expandable task feedback, retry/cancel/pause/review.
- [x] Poll only while visible; preserve existing stable nodes, focus, Reduced Motion and Calm. Run Node suite; commit.

### 4. Recovery, performance and real acceptance

Files: `docs/shiji-v6-capture/qa/`, reports and small screenshots only.

- [x] Run 100 deterministic URLs through real Store/service/HTTP fixture, kill/restart midway, assert resources/tasks/edits/covers.
- [x] Measure 1000/5000 resource scheduling and UI response; record environment and distributions, no transform-based FPS claims.
- [x] Run Python, Node, Swift, real HTTPS sync and macOS build; inspect live V5 UI, save and task controls.
- [x] Commit delivery report with raw-artifact locations, explicit limits and Search/Cover integration guidance. No automatic push/merge.

## Delivery qualification

Completed module commits and acceptance records are in REPORT.md. Actual native popup clicking, installed extension end-to-end and physical iPhone remain unverified; checked implementation steps do not imply device certification. V5.2 frame risks remain open.
