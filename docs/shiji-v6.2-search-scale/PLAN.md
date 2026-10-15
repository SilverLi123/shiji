# Search & Scale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Correct local full-text search and bounded V5 browsing for tens of thousands of resources.
**Architecture:** Derived dirty tracking and FTS candidate index; transactional server filtering/query pages and versioned selection; existing frontend progressively consumes summaries, hydrates details and uses one existing motion system.
**Tech Stack:** Python stdlib, SQLite/optional FTS5, vanilla JS/CSS, SwiftUI/WKWebView.
**Spec:** `docs/shiji-v6.2-search-scale/SPEC.md` plus the user's V6.2 request.

## Global Constraints

- user_version 3, ZIP manifest 2, sync protocol 1 and iPhone JSON remain compatible.
- Preserve V5 visuals, manual content, all filters and complete-match selection semantics.
- No new runtime dependencies, formal data/ports/credentials or main merge.
- Start from 9433afc; keep modules as separate commits and document actual evidence.

## Review Focus

- Old clients/direct SQL must never bypass index maintenance (Tasks 2, 3).
- A summary must never overwrite full notes/code during edits (Task 4).
- Query mutation between pages or bulk confirmation must never silently narrow selection (Tasks 3, 4).
- Short Chinese/code punctuation must retain legacy substring matches without executing SQL/FTS syntax (Task 2).
- Missing/corrupt derived tables and absent FTS5 must preserve authoritative resources (Task 2).

### Task 1: CI, compatibility audit and before measurements
**Files:** `.github/workflows/tests.yml`; `docs/shiji-v6.2-search-scale/qa/baseline.py`, `probe.py`; audit/evidence docs.
**Interfaces:** deterministic temporary Store datasets and untouched V6.1 source snapshot; environment/tokenizer measurements.
- [x] Run baseline Python/Node/Swift/HTTPS/Mac build and record V6.1 manual acceptance limits.
- [x] Verify branch filter matches V6.1/V6.2/subsequent V6 refs and fix.
- [x] Seed and measure 1K/5K/20K/50K with repeated before samples and full-resource response sizes; preserve raw temp paths and source snapshot.
- [x] Commit baseline tools and CI.

### Task 2: Rebuildable search index and batch resource reads
**Files:** new `desktop-app/search_index.py`, `search_text.py`; `storage.py`, `mobile_sync.py`, `backups.py`; `tests/test_search_index.py`.
**Interfaces:** `Store.flush_search()`, `rebuild_search()`, `_read_many(c,rows)`; SQL dirty triggers for all direct writes. FTS capability and safe fallback exposed to query layer.
- [x] RED: Chinese short/mixed/code/phrase AND queries, updates through all write paths, no-FTS fallback, missing/damaged index and restart; batch attachment query count.
- [x] Implement capability-probed ASCII gram index plus exact text validation; chunked dirty processing with short transactions, no network under locks.
- [x] Run relevant suites and commit.

### Task 3: Query API, filters, cursor and full-match selection
**Files:** new `resource_query.py`, `server.py`, organization batch methods; `tests/test_resource_query.py`, `test_query_api.py`, differential Node fixture.
**Interfaces:** `POST /api/query`, library metadata, ID summary lookup, full-match IDs and guarded bulk writes. Cursor rejects query/revision mismatch with 409; deterministic tie-break by ID.
- [x] RED: all legacy filter combinations versus JS matching, sorts, pages/trash/smart/project descendants, concurrent mutation, complete-match batch, restored/synced/background results.
- [x] Implement parameterized SQL over derived query document, bounded projections, metadata counts, transactional revision guards and compatibility routes.
- [x] Run Python/API/differential tests and commit.

### Task 4: V5 search/query migration
**Files:** new `static/resource-query.js`, search interaction helpers/CSS; existing `app.js`, `index.html`, organizing/tag/project pickers, gallery/browse helpers as needed; Node DOM and true API integration tests.
**Interfaces:** one state of loaded summaries; stable-card reconciliation; async detail hydration; cancelled outdated requests cannot apply. Legacy server fallback only when capability absent, never on transient query errors.
- [ ] RED: rapid searches/cancel, exact totals, deep loading, cross-page select, full-detail edit, search navigation/focus/history/highlights, board/gallery and related resources off-page.
- [ ] Integrate summaries, server filters/sort/pages and all-match IDs; remove recurring all-resource loads from default path.
- [ ] Run complete Node and real API UI regressions; commit.

### Task 5: Scale, regression, native evidence and final review
**Files:** QA benchmark/browser/native tooling and docs under this directory; CI build jobs as appropriate.
**Interfaces:** same deterministic datasets, 1K/5K/20K/50K, raw multi-round measurements and candidate V5 UI.
- [ ] Measure before/after retrieval/index/query/filter/page/selection cost, network volume and background capture responsiveness; collect real browser/native performance where tools permit.
- [ ] Complete Python/Node/Swift/HTTPS/Mac build and available CI validation; preserve real-device gaps without stalling.
- [ ] Independent read-only final review, RED→GREEN material fixes; screenshots/recordings and final architecture/API/compatibility/performance report; clear commits.
