## verdict

1. **Resolved — Editorial A/B text fit.** `board-after.png`, both after/mobile cover crops, and both large editor captures show separate headline and subtitle regions. The long Chinese title clamps cleanly with an ellipsis; the subtitle remains visible with a clear gap. The large captures also demonstrate the bottom-position / bold-density case without the original collision.
2. **Resolved — mobile workspace containment.** `mobile-editor.png` has an opaque workspace, clear header and Cancel, preview-first stacking, and visible Save. `desktop-editor.png` retains the desktop hierarchy. Reopening the exact absolute `evidence/mobile-editor-controls.png` (390×844; SHA-256 `b433702fa7a719744222fb904cb7d70dbc3ec9145361fdabc02254f09145d9fe`) shows the header ending at y86, Cancel at approximately x310–371 / y21–64, and “颜色” below y110. Header, controls, and footer are distinct. The previous overlap/absent-Cancel finding was an incorrect factual read and is withdrawn.
3. **Resolved — truthful failed-image status.** `art-editor-desktop.png` now says “图片不可用，已显示海报。可在‘封面来源’更换图片。” below the visible fallback. `failed-image-fallback.png` retains the readable poster, while `actual-image-priority.png` retains the real Poly Haven image. The false “已有真实图片” label is gone.

## remaining

Clear. This ship verdict covers the three scored fixes only, not the whole surface. No further defect hunt was performed; native, full-surface, motion, and performance acceptance are unchanged.

disposition: ship
