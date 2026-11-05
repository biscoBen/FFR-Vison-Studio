The user approved the generated white winged-dodge and crescent-ward artwork
in `approved-sheet.png` on November 5, 2026. `physical.png` and `magical.png`
isolate those two atlas cells and fit the unchanged artwork into transparent
128px production images. No original game art was substituted.

`build_evasion_ui.py` writes private single-mip inline BGRA8 Texture2D JSON
for the pinned native SDK. The native header/settings template contains no
source terrain pixels. Compile each texture and the shared widget with the
original Mappings.usmap, then read back the actual files. Ship only the six
compiled uasset/uexp files in evasion_stats.zip; these source PNGs are not
required by the app or installed game.
