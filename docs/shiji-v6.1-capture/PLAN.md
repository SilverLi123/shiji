# Capture Everywhere Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Complete reliable phone-to-desktop enrichment and durable browser capture delivery.

**Architecture:** Reuse the V6 worker for synced resources. Add optional local receipt records atomically with existing Store writes; an extension outbox freezes payloads and reconciles receipts before retrying. No second resource model or backend worker.

**Tech Stack:** Python/SQLite, vanilla JavaScript Manifest V3 extension, SwiftUI/WKWebView.

**Spec:** `docs/shiji-v6.1-capture/SPEC.md`

## Global Constraints

- SQLite schema 3, ZIP manifest 2, phone sync protocol 1 unchanged.
- Preserve V5 visuals and user-edited fields; no new runtime dependency.
- Temporary databases, random ports, disposable credentials only.
- Reuse clean linked worktree; branch from c393671. No push or main merge.

## Review Focus

- Replayed sync receipt must not create jobs or overwrite enrichment completed since first request (Task 1).
- Phone edit during parsing and synced deletion must reject late writes (Task 1).
- Lost save response followed by trash/purge must not recreate saved resource (Task 2).
- Pairing change, service-worker restart, simultaneous retry/cancel must not misroute or duplicate frozen content (Task 3).
- Outbox storage quota failure must not falsely claim saved or queued (Task 3).

### Task 1: Synced resource capture

**Files:** `desktop-app/mobile_sync.py`, `desktop-app/tests/test_mobile_capture.py`, `mobile-app/Tests/SyncIntegration.swift`, `mobile-app/Tests/sync_integration.py`.
**Interfaces:** existing `SyncEngine.commit(body)` consumes protocol-1 resources; `Store.enqueue_capture(c,item)` schedules only new/URL-changed active websites after attachments are installed. Snapshot returns actual enrichment on subsequent sync.
- [x] Write and run failing tests for new phone resource enrichment/cover snapshot, idempotent replay, URL change, manual edit and deletion races; temporary Store and HTTP fixture.
- [x] Implement the narrow sync hook and invalidation without changing sync payloads.
- [x] Run `python3 -m unittest discover -s tests -p test_mobile_capture.py` and existing sync regressions; add real Swift TLS roundtrip verification.
- [x] Commit the synced capture module.

### Task 2: Atomic clip request receipts

**Files:** `desktop-app/capture_receipts.py`, `storage.py`, `server.py`, `tests/test_clip_receipts.py`.
**Interfaces:** optional `request_id` on `Store.capture_page`; optional local table `clip_receipts(request_id,payload_hash,resource_id,created_at)`. Authenticated `POST /api/clip/status {requestId}` returns saved/not_found. `/api/clip/ping` advertises `captureReceipts:1`; `/api/clip` accepts `requestId` and returns matching receipt.
- [x] Write and run failing tests: repeat after lost response/edit/trash/purge, changed-payload rejection, concurrent requests, atomic rollback, authentication and old-client compatibility.
- [x] Implement receipts in the same transaction as resource/attachment/tasks; retain compact tombstone after resource purge; no full payload or credentials in receipts.
- [x] Run `python3 -m unittest discover -s tests -p test_clip_receipts.py` plus capture/API/backup regressions.
- [x] Commit receipt support and API compatibility notes.

### Task 3: Durable browser outbox and controls

**Files:** `desktop-app/browser-extension/outbox.js`, `background.js`, `popup.js/html/css`, `manifest.json`, `tests/test_extension_outbox.js`, `tests/test_extension_app.js`, `tests/test_extension_popup.js`.
**Interfaces:** `ShijiOutbox.create({storage,send,config,now,id,pairKey})` with enqueue/list/drain/retry/remove. Chrome local storage persists frozen payloads, request IDs and pairing fingerprint; one serial mutation lane and one network drain, alarms wake a stopped worker. Pending/failed/blocked records remain visible until delivered or explicitly removed.
- [x] Write failing behavior tests for offline/restart/lost response, pair change, concurrent enqueue/drain, removal during request, quota failure and bounded storage.
- [x] Implement receipt reconciliation and capability check before POST; retries retain original screenshot bytes and request ID; credentials are read at send time, never stored per queued item.
- [x] Add compact popup counts, pending list, retry/remove, distinct queued versus saved feedback, keyboard focus and error feedback. Update popup behavior tests and docs.
- [x] Run complete Node tests and receipt/API tests; commit extension module.

### Task 4: Isolated acceptance and delivery

**Files:** `docs/shiji-v6.1-capture/REPORT.md`, `qa/`, evidence summaries; existing native QA tooling reused.
**Interfaces:** actual Store/HTTP/Swift sync and production extension code; no fixture logic in product.
- [ ] Run complete Python/Node/Swift sync and macOS build; test backend stop/restart with persisted extension payload and receipt.
- [ ] Exercise actual browser extension UI and isolated iPhone sharing where available; record real screenshots and explicitly list unavailable device checks.
- [ ] Final independent code review, fix material findings with regressions, commit report.

## Compatibility and recovery

New receipt table is optional local derived data created with IF NOT EXISTS; user_version remains 3. Old clients can keep sending clips without requestId. New extension waits with actionable feedback on older servers lacking receipt support. ZIP manifest export omits receipts; restoring a library may lose transport receipts, so pairing changes block old queued requests and restored-library behavior must be documented. No receipts contain tokens or full page/screenshot data. Rollback to V6 ignores the optional table; uninstalling the extension removes its local outbox, which must be surfaced in help text.
