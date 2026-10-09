# SHIJI V3 Beta Foundation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan in this session.

**Goal:** A tested integration baseline of art be9e04c and V2.1 4cf4580 without a new product feature.
**Architecture:** Reuse the clean linked worktree and create an integration branch. Preserve the art branch renderer and sole Bits layout/gesture owner; integrate cancellation/native improvements from V2.1 and test their interaction.
**Tech Stack:** SwiftUI, WKWebView, HTML/CSS/JavaScript, Python, SQLite.
**Spec:** docs/shiji-v3-beta/SPEC.md

## Global Constraints

- No main merge, remote push, production database/ports or existing pairing credentials.
- SQLite schema 3; ZIP manifest 2; no new third-party runtime.
- Keep large Hero markup/sizing/brand loops and approved Lab masters intact.
- Protect both existing checkouts' uncommitted changes; isolated test directories and loopback port 0 only.

## Review Focus

- Whole-card gesture plus FLIP/detail must cancel without suppressing keyboard activation.
- Calm/system reduced motion and hidden document must clean finite/ghost animations.
- Missing real images must fall back to safe covers, never hide preserved real content.
- Restores/sync must preserve comma tags, attachment bytes and explicit conflicts.
- iPhone capture rail, large type and Share Extension diagnosis cannot be declared accepted from compilation.

### Task 1: Audit and baseline

**Files:** docs/shiji-v3-beta/SPEC.md, branch audit/plan.
**Interfaces:** produces pinned source SHAs, clean worktree and test logs.
- [ ] Fetch refs via existing SSH authorization; create feat/shiji-v3-beta-foundation at be9e04c in the clean linked checkout.
- [ ] Run Python, Node and native core/ZIP baseline. Expected: green suites; document any pre-existing failure.
- [ ] Read differing presentation/motion/native implementations; record selection and conflict policy.

### Task 2: Integrate existing work

**Files:** desktop-app/static/resource-bits.js, shiji-v2-motion.js, index.html, scoped shiji-v21.css; mobile-app sources and existing tests; docs/branch history.
**Interfaces:** consumes source SHAs; produces merged owners and native V2.1 source, no new business API.
- [ ] Add cross-branch DOM/controller assertions for cancellation and cover detail fidelity, run against baseline. Expected: missing V2.1 modal behavior fails.
- [ ] Merge V2.1 without committing; resolve overlaps explicitly. Retain art covers/IDs/whole-card gesture; integrate motion interruption and native files. Keep Lab/source assets unchanged.
- [ ] Run all Node and Swift/core/ZIP tests. Expected: both branch contracts pass with obsolete V2.1 cover-selector assertions translated to the retained renderer's equivalent contract.
- [ ] Commit integration; preserve conflict notes.

### Task 3: Isolated validation and deliverable

**Files:** desktop-app/tests/test_v3_foundation.py, desktop-app/tests/v3_resource_contract.cjs, docs/shiji-v3-beta/qa/run.py, REPORT.md, evidence.
**Interfaces:** consumes the real Store/Handler/renderer; produces reproducible temp environment and evidence without production access.
- [ ] Add and run HTTP workflow tests: capture/search/filter/attachment/detail/backup preflight/restore; real HTTPS sync integration. Expected: persisted states/bytes/format match and canceled restore leaves state unchanged.
- [ ] Run full Python/Node/native suites and build native targets. Expected: green tests; no fallback from unavailable runtime to invented evidence.
- [ ] Capture actual desktop Hero/gallery/detail and owned QA iPhone. Record exact runtime bounds and unresolved native/share acceptance.
- [ ] Review whole branch independently per executing-plans, fix material integration findings with regressions, write report and commit. Keep baseline local pending user push instruction.
