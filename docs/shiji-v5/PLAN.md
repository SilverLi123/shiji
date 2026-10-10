# SHIJI V5 Spatial Poster — real App integration

Visual authority: the user's `SHIJI_V5_Spatial_Poster_Demo.html`, preserved verbatim in `reference/spatial-poster.html`. This request supersedes previous layout choices. Code-led port of supplied HTML/CSS, not a new visual concept.

Branch: `feat/shiji-v5-spatial-ui`, from V3 integration `549457e`. Clean initial worktree. No remote push, main merge, formal data/service/credentials, schema or ZIP changes.

## Direction contract

First viewport: Demo's 238px dark sidebar, compact studio toolbar, large two-line lime headline and purple layered brand stage. Immediately below: the three-pane spatial deck, then lime motion ribbon and poster gallery. Use the Demo's own CSS/SVG construction and typography.

Signature interaction: real resource posters float in the spatial deck and open the existing detail drawer. Whole-card elastic tilt/drag and FLIP remain owned by ShijiBits; ShijiMotion owns stage/deck parallax, finite feedback, cancellation and loop pausing. Calm, flat-space and system reduced motion disable dynamic depth. Offscreen/background artwork pauses. Saved resources and actual user covers stay authoritative; no Demo seed or simulated persistence.

1. Port shell, Hero, spatial section, gallery art and responsive controls; keep all business IDs/actions.
2. Adapt poster compositions to actual title/source/type/tags/snippets, with image precedence and failure recovery. Bind deck and UI toggles to real state.
3. Add regression tests for content, stable IDs, cover recovery, spatial lifecycle and native packaging. Run existing suites.
4. Compare real desktop/mobile/user viewport with Demo in two bounded visual rounds, then independent Impeccable finish review. Build isolated native App for the user. Keep native runtime limits explicit.

No iOS HTML replacement: this port targets the shared macOS WKWebView/web workspace. Existing native iPhone architecture and functionality remain intact; responsive web screenshots cannot certify native iPhone visuals.
