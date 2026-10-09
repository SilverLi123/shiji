# SHIJI Art Direction Lab — review delivery

2026-10-09. Local branch `feat/shiji-art-direction-lab`, baseline `7eda5f9` (`feat/shiji-cover-studio-2`). User approval is required before any production integration. No push or merge in this task.

## Reference and observed gap

Authentic V3 Poster Lab / V5 Spatial Poster supplied in `/Users/silver/Downloads/SHIJI_V3_V5_Design_References_for_Codex`. All six HTML/PNG/MP4 files copied byte-for-byte into `docs/shiji-v2/reference`; hashes recorded in `reference-sha256.txt`. Original HTML, provided screenshots and live browser rendering were inspected. Original video files are playable in the Lab; observed metadata: V3 14.56 seconds, V5 29.16 seconds. No claim that a new recording of the Lab has been produced.

| Aspect | V3 / V5 reference | Cover Studio 2.0 | Lab response |
| --- | --- | --- | --- |
| Typography | Letterforms form the poster, diagonals, foreground occlusion | Often an isolated left-hand name | Project-specific line breaks, diagonal SHIJI, editor-edge VS Code, serif print and transformed lettering |
| SHIJI | Strong lime/dark brand contrast; restoration also has lime frame/ticket | Cream + gray slab reduced energy | Folded acid-lime frame, dark tilted ticket with actual saved stack/tags |
| Focal object | Sculpted ball, chrome ring, laminated disc, terminal/UI specimen | Repeated small ring, cross, columns | Editor planes, projected stage, component specimen, paper spread, kinetic disc/strip, curved wireframe, transparent tensor sections |
| Materials | Printed registration, offset ink, sculpted highlights and cast shadows | Broadly flat planes | Paper/light/cast shadows; two geometric computational subjects and a real website image |
| Semantic art direction | Specific subjects have purpose-built artwork | ID hash selects layout/color; AI grouped with general tools | Explicit 12-resource curation outside schema. No hash or automatic matching claim |
| Spatial feedback | V5 layers and perspective; separate deck | Limited cover-internal depth | Optional Lab-only pointer perspective and foreground displacement; static default, no continuous loop |
| Data | Demo sample titles/records | Actual model | Actual Store-persisted temporary inputs; true names/URLs/snippets, existing local preview. No sample Demo records imported |

This is an interpretation of V3/V5 principles for real resource content, not a pixel clone. V3’s sculpted orb/ring subjects still have richer lighting than the Lab’s generally vector-based materials. Full V5 spatial deck, genuine foreground/body/background Z separation, continuous art loops and product animations remain outside this art-board milestone; pointer perspective plus foreground translation is a selective study, not V5-equivalent motion.

## Twelve masters

| Resource | Group | Authored focal/composition |
| --- | --- | --- |
| SHIJI | Development | Irregular folded lime frame enclosing diagonal name, foreground dark technical ticket |
| VS Code | Development | Two projected editor planes, near-edge typography and cursor geometry |
| Godot | Development | Exact isometric cuboids on a game-engine scene plane |
| React Bits | Design | Giant type specimen with overlapping component label/action sheet |
| Recent — Olla | Design | Violet/cream printed spread, serif name, offset page and registration |
| Motion Sites | Motion / 3D | Skewed type, layered disc, diagonal repeated-name ribbon |
| Poly Haven | Motion / 3D | Repository's actual website preview, local caption pane; no newly sourced image |
| Hugging Face | AI / ML | Curved wireframe surface overlapping the resource name, labeled abstract/non-model-output |
| PyTorch | AI / ML | Four transparent tensor slices, coral foreground type, labeled abstract |
| CSS transform / MDN | Technical article | Cream reference sheet; transformed echoes illustrate actual CSS syntax |
| 保留真实代码缩进 | Code | Real seven-line saved snippet with exact whitespace and punctuation |
| 为下一次创作留下线索 | Prompt | Chinese serif brief, actual saved body, overlapping paper and folded corner |

Website fields are manually curated test inputs, not scraped metadata. SHIJI's stack reflects this repository. Names and links are real; geometric objects are decorative studies, not app screenshots, model results or claimed statistics. Code and Prompt are locally authored QA resources already used in the earlier review harness. PyTorch and MDN are new manual reference inputs. Primary URLs: [PyTorch](https://pytorch.org/), [Hugging Face](https://huggingface.co/), [MDN transform](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/transform).

## Run and isolation

```sh
python3 docs/art-direction-lab/run.py
```

Always creates a new OS temporary directory, instantiates the existing Store there and binds `127.0.0.1` on an OS-assigned port. It accepts no production data path. HTTP exposes only a fixed read-only route map and `/lab-data`. POST/PUT/PATCH/DELETE return 405; arbitrary files/APIs return 404. Reference demos retain their own original sample/localStorage behavior solely on the isolated Lab origin. Lab itself has no localStorage business or mutations.

Current preview: `http://127.0.0.1:54102/`. Temporary data: `/var/folders/zf/9x8vcjy9091gxc3tdsz79_lm0000gn/T/shiji-art-direction-lab-82p70q4z`. This path is disposable, never part of the Git deliverable. The running Lab is separate from existing 54891/56184 review services and formal service ports.

Changed files: only `docs/art-direction-lab/` and the two authentic reference folders. No production static JS/CSS, Python service/store, native SwiftUI, extension, database format or ZIP manifest edits. Verified no tracked diff against baseline for runtime directories. Existing Hero and Motion Studio therefore remain byte-identical.

## Tests actually run

- `python3 docs/art-direction-lab/test.py`: **2 tests passed**, latest 0.643 seconds. Persisted exact category counts, twelve unique IDs, actual saved image cover, schema 3, loopback, read-only methods, route whitelist and unchanged resource state after rejected writes.
- `NODE_PATH=/Users/silver/shiji/desktop-app/node_modules node docs/art-direction-lab/test.cjs http://127.0.0.1:54102/`: **passed**. Twelve masters, deterministic markup, escaping, actual code/Prompt, real image, unique SVG paint servers; actual persisted-resource DOM and comparison controls, coalesced pointer RAF, background cleanup and system reduced-motion precedence.
- `NODE_PATH=/Users/silver/shiji/desktop-app/node_modules node desktop-app/tests/run-node.cjs`: **40 groups passed**. Includes current app operations, current cover renderer, motion lifecycle and 1000-resource layouts.
- Six supplied reference files: **byte equality passed**.
- `git diff --check`: passed.

The earlier 202 Python tests belong to the Cover2 baseline; they were not rerun or relabeled as results of this milestone. Native Swift was not rebuilt; no native code changed. Real system reduce-motion preference was not toggled: precedence was tested through the actual controller in JSDOM; CSS has a reduce-motion rule. No measured FPS claim is made.

## Browser evidence

All new screenshot files in `evidence/` are actual CUA browser captures, JPEG as returned by the browser, not composed mockups. Reference PNGs are original user-supplied artifacts. Browser screenshot dimensions differ slightly from observed CSS viewport due to the IAB capture surface; dimensions are reported honestly.

- `desktop.jpg`, `user-1412.jpg`: complete twelve-poster board. Observed CSS viewport 1412×980, no horizontal overflow. Desktop capture 1375×2105.
- `mobile.jpg`, `mobile-viewport.jpg`: fixed same-origin **390 px CSS review frame**, width=scrollWidth=390; one-column board. Full capture 382×5399. This is responsive web review, not an iPhone simulator screenshot.
- `comparison.jpg`: all twelve same-record comparisons against the unmodified Cover2 renderer and source CSS in Shadow DOM (only `:root` selectors are mapped to `:host` so original tokens take effect), plus restoration comparison.
- `pair-01.jpg`…`pair-12.jpg`: larger actual viewport comparisons, record order matches table above. Adjacent resources remain visible where the browser scroll positions include them.
- `shiji-comparison.jpg`: focused Cover2 versus Lab comparison view.
- `restoration-comparison.jpg`: complete large card-restoration / 3327d44 versus Lab pair, captured separately because the long full-page comparison truncates the final pair.
- `spatial-left.jpg`, `spatial-right.jpg`: real pointer poses; foreground ticket displaces independently from type/background. Observed transform matrix and CSS pointer values changed. They are still frames, not a recording.
- `v3-running.jpg`, `v5-running.jpg`: actual live reference Demo rendering in the same browser (Calm used for reliable reference capture).
- `reference-comparison.jpg`: supplied V3/V5 screenshots displayed together; original videos and links available under the reference tab.

Superseded or wrong-width captures were discarded. Browser viewport override reset. Standalone Lab interaction never loads Bits/Motion or adds a second FLIP/Tilt system to the application.

## Remaining boundaries

- Await user art review. Do not broaden this hand-authored board into an automatic generator before approval.
- Semantic matching, variant customization, 1000-resource generation, iPhone cover templates and merging the divergent V2.1 branch remain future work.
- Platform font fallback is intentional/offline and follows the references. Cross-platform font reproduction still needs evaluation before integration.
- Independent finish review: **SHIP FOR STANDALONE USER ART REVIEW**, with no unresolved material finding at board scope. Full record in `REVIEW.md`; this verdict does not represent user acceptance or production readiness.

## Poly Haven correction — 2026-10-09

User accepted the other eleven covers and flagged Poly Haven. The earlier Lab cover retained screenshot navigation, original branding and roadmap UI, then overlaid another large title and blurred caption. This duplicated the hierarchy and obscured the real image.

Only the Poly Haven markup and CSS were changed: a cream photographic print on a forest-green surface, actual saved 3D category, one authored title, and a CSS crop of the existing website image's architectural detail. The 1280×720 source window is x=820..1240, y=120..510; it avoids site navigation, logo and embedded title without altering the source image. Its label and alt text explicitly say this is a cropped website preview. This crop is specific to this curated reference image, not a general content-aware cropping engine.

The other eleven master blocks, shared layout and motion code were compared with commit `9fe3adb` and are byte-identical outside the Poly Haven block. Source image, saved resources and runtime code remain unchanged. The existing finish review in REVIEW.md applies to the original board; it is not a new independent verdict on this correction.

Validation actually performed for this correction: existing Lab JavaScript tests and actual saved-resource DOM/control/reduced-motion checks passed; `git diff --check` passed. Python, the full Node suite and Swift were not rerun for this local visual adjustment. Actual CUA inspection confirmed the two-column current browser layout (652 CSS px) and the 390 CSS-pixel mobile review frame. The attempted wider browser override did not change the background Lab's reported viewport, so no new three-column capture is claimed. The temporary override was reset.

Final browser evidence: `evidence/polyhaven-board-v2.jpg`, `evidence/polyhaven-mobile-v2.jpg`, `evidence/polyhaven-comparison-v2.jpg`. Earlier board/pair images remain historical before evidence. The comparison-v2 screenshot is Cover Studio 2.0 versus corrected Lab, not original-Lab versus corrected-Lab. Current mobile evidence is web, not native iPhone. No production integration or remote push.
