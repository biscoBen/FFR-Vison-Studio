# Crystal Fina battle presentation

The selected custom vision (`99887755552703`, source `CUSTOM`) uses native introductory Fina inside the approved
rotating Sanctum glass. Resolve her allocated game ID at build time. Preserve saved identity, kits, mechanics and
native hit/healing/movement events. Original party models and other visions keep their own presentation.

## Native body and coordinates

Source: `/Game/Chara/Field_Unit/pc0030/pc0030_01/pc0030_01`, 60 fps, native 256×512 atlas.

| Motion | Frames | Use |
| --- | ---: | --- |
| openarmidle2 | 49 | Closed-eye floating idle |
| openarmopeneye2 | 65 | Eye opening |
| curlup2 | 73 | Turn toward target |
| magicattack6 | 91 | Charge and fire |
| down6 | 49 | Descent |
| sit_pose2 | 6 | Contains Rain's jacket; do not use |

Use supplied custom frame 174 for the authorized jacket-free seated fallback. Preserve native pixels and pivots.
The inline BGRA decoder checks offset 84, a single mip and the 24-byte footer. SsValue cell/scalar values come from
`Ss6Project.Extras`, in animation/part/attribute/key order; the reflected HashType fields are empty placeholders.
Reject unknown headers, bad name references, truncated/nonfinite values and unconsumed payload bytes.

**Animation tracks do not create model parts.** `make-ss6` accepts a separate top-level `model.parts` array. Author
root, body and every NULL attachment there with explicit indices/types/parents. Parent the flattened body and NULLs
to root; retaining the native `position` parent adds inherited offsets. Strictly read back `Model.PartList` and
check names, parent/index assignments and empty mesh/bone lists. Trailer-only tests missed this in the first build.

The body pivot is at `Posy=22 + BODY_FLOAT`; its visual center is one pixel below that. The crystal center is
`183.5/2.7` sprite pixels. `NULL_Aura` follows the body's center throughout descent and recovery. `NULL_Crystal`
rotates on SS6 Y at 3.6 degrees/second, with a 6000-frame idle covering one turn. Runtime axis inheritance still
needs in-game confirmation.

## Casing renderer and dependencies

`UNIT_ANIMATION_ASSET_DATA` has no ordinary mesh slot. Add Fina alone to the confirmed
`Datatable/Asset/Battle/Effect/DT_BtlUnitEffectAsset`, attaching a private Niagara casing to `NULL_Crystal`.
There is **no persistent aura bundle**. Private battle assets live under `Chara/StudioCrystalFinaBattle/<ID>`.

Clone `NS_EF_EV_CMN_FinaCristalAuraParticle`. Preserve compiled scripts, handles/order and all opaque VM trailers.
Use its CPU `BrightSting_0` emitter with an **appended** `NiagaraComponentRendererProperties` and one movable,
non-colliding StaticMeshComponent template. Clear other emitters' renderer lists and disable their renderers;
handle enable flags alone are insufficient evidence that a cooked renderer cannot draw.

Keep the original mesh renderer and class intact: `NiagaraDataInterfaceMeshRendererInfo.MeshRenderer` still points
to it and the CPU VM depends on its data. Replacing that export's class with ComponentRendererProperties invalidates
this dependency. The new renderer alone goes into BrightSting's renderer list. Preserve native mesh bulk/render
bytes and the approved ordinary glass shader; do not claim a Niagara shader permutation can be added by a usage flag.

Public Unreal source inspected: `NiagaraRendererComponents.cpp` falls back to enabled when the particle's enabled
attribute is absent. With empty PropertyBindings it does not overwrite the template transform. In
`NiagaraSystemInstance.cpp` the duplicate template attaches to the Niagara component, retaining relative transform.
These corroborate the intended attachment; they do not substitute for testing this game's cooked runtime.

Use the fresh Fina design row's separate `Scale` and `attachEffectSacle` values. Set nonpositive fields explicitly
to 2.7 and 1.0 respectively; preserve positive values and all unrelated fields/rows. Canonicalize authored floats to
float32 before readback comparison. Casing/body ratio remains `.12/2.7`; correct the native mesh pivot from its bounds.
The cave pair separately grows by 15% about its grounded origin, retaining that ratio and its approved glass/rotation.
The old comparison NPC/table row/stream is no longer generated.

## Battle sequencing

Ordinary release presentation completes in 60 frames instead of stretching to the imported 307/346-frame clips,
which the game's shorter spell recovery can interrupt before the shot. Preparation opens eyes and turns in 30 frames.
The normal-skill animation repair uses the replacement's one-second duration rather than accelerating it based on
old FFBE CSV durations. No damage/healing keys are moved. Exact visual alignment with each spell needs live review.

| Resonance frame | Presentation |
| --- | --- |
| 0–121 | Float in casing; no golden glow |
| 122–134 | Native introductory glow fades in at body's center |
| 134 | Hide crystal; begin 49-frame descent; original reaction frame unchanged |
| 135–164 | Fade glow out, then destroy its Niagara instance |
| 183–307 | Original jacket-free seated hold (125 frames, previously 249) |
| 296–308 | Brief second body-centered glow ramps up |
| 308 | Restore floating pose and crystal together |
| 309–332 | Fade glow out and destroy instance |
| Existing recovery | Return to idle without changing gameplay event timing |

Author these on Fina's exact private resonance job only, using the builder's `lb_id` function and exact asset path.
The confirmed native events are `EffectSpawnNiagaraAtRandom` (caster/vision attachment),
`EffectDiactivateNiagaraToNiagaraID` and `EffectDestroyNiagaraToNiagaraID`. `BTL_SEQUENCER_NIAGARA_DATA` supports
PartName, following and bPlayVisionUnit. The source system exposes User.Alpha, User.NiagaraAlpha and User.LightPower.
The asset writer rejects EX_ArrayConst user-parameter arrays, so do not ship per-event alpha arrays.
Use the original particle alpha curves and explicit deactivation/cleanup instead. A private glow copy disables native
light renderers to avoid a floor-level light beam; source effects remain unchanged. Import the actual
Niagara object/package into the cooked shell; preserve its bound battle actor and rebuild the event channel and
compiled one-shot tree together. Verify spawned object references, attachment fields and lifecycle constants through seqdump.
Exact fade appearance remains a live-rendering check, rather than a claim established by serialization.

## Studio and verification

`scripts/render_crystal_fina_preview.py` shares battle body/attachment tracks and timings and renders the supplied
LOD0 mesh/native sprite pixels. It approximates glow/glass and is labeled accordingly. The checked bundled WebPs use
presentation revision `native-fina-3`; literal API routes and URL revision bypass old previews without deleting them.

Local integration uses the real native asset writer on the supplied references and a clearly labeled synthetic
zero-scale design-table fixture. Validate actual model parents, native renderer dependencies, all original VM bytes,
SS6 trailer values and cooked glow lifecycle events, then pack/verify an IoStore container. Scratch fixtures never
replace user game data. Windows CI checks the real frozen engine, Flutter suite, managed resources and package.
Actual crystal visibility/rotation, attachment following, cast timing and glow appearance need an in-game test.
Reference collectors continue to write to `Downloads\FFR Mod`.
