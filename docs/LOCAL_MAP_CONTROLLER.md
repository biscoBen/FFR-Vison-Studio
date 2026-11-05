# Controller local map sizing

The Home **Full local map on controller** option retains the native minimap
button cycle: minimap → full current area → hidden. The overworld keeps its
native cycle. Native exploration visibility and markers are unchanged.

The user confirmed switching in 1.2.158/1.2.159, but showed an enlarged frame
with a tiny map in its center. Version 1.2.161 corrects two sizing inputs:

- Native Image origin centers the **current area**, while the old fit used
  `MapLandCaptureData.LandWholeSize`, which can span many unrelated areas.
  Resolve `GetCurrentAreaId()` in `AreaLandCaptureDataMap` and fit its `BoxSize`.
- The widget's actual viewport is `MiniMapAppearance.DisplaySize`.
  `RangeSize` sizes the smaller range-ring image inside it; it is not the
  viewport boundary.

Project the selected capture size through the same native map projection and
fit its diagonal into 90% of the smaller viewport dimension. This keeps all
capture corners inside either a circular or rectangular viewport during native
rotation. Refresh after the real Blueprint appearance, zoom and world-position
notifications, including area changes. `SyncPlayerData()` recomputes the native
UI coordinates after a zoom change; no actor or game-world position is written.
The callbacks retain no UObject pointers and use no polling. Missing area bounds
fall back to the normal minimap. Exiting full view restores the native settings
and remembered zoom; the fitted scale is not saved.

Evidence comes from the existing controller capture and the already supplied
native-code/lookup captures; no additional collection is needed. In the image
with executable SHA-256
`b8c588e46ebadbe37feca7bdf2da0ae63a8538099d14a53ec0c2241b086e5ffa`,
the `CPP_VM_MiniMap` helper at RVA `0x04edc9a0` assigns vtable `0x088ac568`.
Its origin override (`+0x2e8`, RVA `0x051e00e0`) selects the current area ID,
finds that key in the capture-area map and projects/zooms the area's
`WorldLocation`, rather than using the whole-land center. The reflected
`GetCurrentAreaId` wrapper calls `0x051d3c30`, which reads the same area ID.
The runtime uses reflected APIs only; these addresses are evidence, not runtime
memory access.

The captured `WBP_MiniMap:SetAppearance` sizes `Size_Display` from **DisplaySize**
and `Image_RangeLine` from **RangeSize**. Its original WidgetTree puts the
`RetainerBox_Mask` under `Size_Display`. The native image, area layout, icons and
mask remain game-owned.

Regression fixtures include a surrounding land group hundreds of times larger
than the active area, different range-ring and viewport sizes, remote-wrapped
TMap keys/values, area transitions and bounded notification reentry. Native
metadata and fixture checks establish the implementation; the revised scale
still needs gameplay confirmation.
