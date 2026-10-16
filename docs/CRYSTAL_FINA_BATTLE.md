# Crystal Fina battle presentation work

Requested after comparison build aee9e8c (run 38829455821). Both battle reference uploads have been inspected. The body animation drafts were approved by the user.
The managed build now generates a private battle presentation for the selected custom Crystal Fina, without changing her saved identity, kit, menu assets or the existing cave comparison.

## Requested presentation

- Use the approved rotating Sanctum glass casing and native introductory Fina in battle.
- Attack: open eyes, turn toward the target, gather energy and fire; keep the casing intact.
- Resonance: apply her introductory golden glow, make the casing disappear, let her descend and finish seated.
- Avoid the jacket in the native seated cells. The user authorized the old imported jacket-free sitting frame as a
  fallback. An image-generation attempt was rejected; use the existing supplied pose rather than generating another.
- Preserve current vision identity, kit, mechanics, hit timing and saved edits. Derive timing for the new presentation
  from the actual selected motions and effect lifecycle; do not silently retime damage or healing.

## Confirmed evidence

`/Game/Chara/Field_Unit/pc0030/pc0030_01/pc0030_01` contains these native motions at 60 fps:

| Motion | Frames | Candidate use |
| --- | ---: | --- |
| openarmidle2 | 49 | Closed-eye floating idle already used in the cave |
| openarmopeneye2 | 65 | Opening eyes |
| openarmidleopeneye2 | 49 | Open-eye hold |
| curlup2 | 73 | Front-to-side/body turn; inspect actual cells before sequencing |
| curlup_pose6 | 6 | Side hold |
| magicattack6 | 91 | Casting motion |
| magicattack_pose6 | 6 | Cast hold |
| down6 | 49 | Descent candidate; inspect placement before use |
| sit_pose2 | 6 | Native pose includes Rain's jacket; do not use unchanged |

The yellow aura is separate: `NS_EF_EV_CMN_FinaCristalAuraParticle`, alongside
`NS_EF_EV_CMN_FinaCristalAppearance_001` / `_002`. Those references already exist locally.
The current custom vision is sprite ID `99887755552703`, with its allocated game ID resolved at build time.
Its existing imported sheet includes the allowed jacket-free seated pose.

The approved glass is a StaticMeshComponent in a streamed cave NPC level, with its own turn sequence. That setup
cannot simply be assigned to `UNIT_ANIMATION_ASSET_DATA`, which exposes only Ss6Project/material/textures and a flag.
`BTL_UNIT_EFFECT_ASSET_DATA` exposes per-unit `effectBundleList`; each bundle includes `niagaraAsset`,
`attachPartsName`, `offsetLocation`, `additionalRotation`. The follow-up found the actual table at `Datatable/Asset/Battle/Effect/DT_BtlUnitEffectAsset`. Native monster rows attach effects to `root`; the special vision-aura row uses `null_center`. The implementation adds only Fina's allocated ID, with `NULL_Crystal` and `NULL_Aura` part attachments.
Do not flatten the crystal to a sprite or apply a global battle Blueprint change as a substitute without discussing it.
The ordinary JSON decoder does not expose SsValue cell hash contents. `scripts/prepare_crystal_fina_battle.py` now
reads the native custom-value trailer in animation/part/attribute/key order, matching the installed Ss6Builder writer.
It decodes 180 floats and 45 cell hashes, consuming all 2731 bytes. Cell map/name records use name-map references and
native typed-value headers; scalars are float32. Reject changed headers, nonfinite/truncated values, invalid name
references or extra bytes. Do not use the empty reflected HashType fields as the actual cell references.

The body draft joins `openarmopeneye2` (65), `curlup2` (73), `magicattack6` (91) for attack. Resonance uses a glowing
floating hold (49), eye opening (65), the first 20 turn frames, `down6` (49) with descent, then original custom frame
174 as the jacket-free seated hold. Crystal disappearance is planned at frame 134, matching the existing resonance
reaction frame. These are presentation drafts, not an installed battle model or a verified attack-impact timeline.
Native cell pivots and positions are preserved in the previews; original seated pixels are reused without repainting.
The standard inline BGRA texture layout is checked before extracting its 256x512 mip (offset 84, 24-byte footer).

## Received battle references

`Crystal-Fina-Battle-Reference-20261015-190739-30e3dd-001.zip` contains 309 assets including `DT_BtlUnitAsset`, the
440110 resonance shell and Fina effects. No battle-unit effect table was found under the requested unit folder. The
broad Blueprint search yielded AI classes but no per-vision battle actor class/mesh slot. Searches for the guessed
attack, 440280 and BP/Unit folders returned no assets; those guesses are not confirmed paths.

The Fina aura has CPU mesh/sprite emitters and GPU sparkle emitters. Its mesh renderer uses `SM_EF_CMN_Plane_020`;
it is not a pre-existing crystal mesh renderer. The approved SingleLayerWater glass material declares static-lighting
usage, with no Niagara usage flag in the decoded source. Do not assume a Niagara mesh replacement can use its cooked
shader permutations merely by setting a usage flag. A native component-based renderer/attachment may be needed.
Its exact runtime binding and lifecycle still need evidence; do not edit global battle actors or invent a table path.

The follow-up helper searches attachment names across folders and runs the upstream-supported `retoc list --path`
command to include a package index. It retains the index/report ZIP even when no attachment assets match, so an
unused/missing demo table can be distinguished from another incorrect path. Tested successful and empty-result
collections with paths containing spaces, input preservation, PowerShell parsing and readable ZIP contents.


## Implemented attachment and validation

The casing is a private copy of the native Fina aura Niagara system. All compiled scripts, emitter handles/order,
VM trailers and native source assets remain intact. Only its CPU `BrightSting_0` emitter is enabled; its renderer is
replaced by `NiagaraComponentRendererProperties` with one ordinary movable, non-colliding StaticMeshComponent
archetype. Empty property bindings retain its authored transform instead of the original plane particles' motion.
This uses the approved ordinary static-mesh glass shader without claiming that a new cooked Niagara-mesh shader
permutation can be made by changing a usage flag. The renderer and template survive strict native roundtrips.

The independent body/casing assets live under `Chara/StudioCrystalFinaBattle/<allocated ID>`. The original converted
summon and menu assets remain for the old cave comparison and editor. Only the freshly built Fina battle row is
retargeted; all other rows, sound data, skills, stats and sequence events remain. No roster file is written.
Casing size uses the freshly built Fina design row's separate sprite Scale and attachEffectSacle fields, retaining
the approved .12/2.7 casing/body ratio. The native bounds origin corrects the mesh pivot.

The first live build log rejected a nonpositive native scale. The original positive-only donor check was too strict;
its synthetic integration design row had not covered that case. The corrected build authors explicit positive values
on Fina's current design row wherever the value is nonpositive: sprite Scale 2.7 (the approved native body scale) and effect scale
1.0. Existing positive values remain unchanged. The casing calculation uses these same authored values, rather than
guessing the game's C++ inheritance behavior or dividing by zero. Nonfinite/unsupported values still fail
with the field and value. New float values are canonical float32 before strict serialization comparison. All other
design rows and Fina's non-scale design fields remain unchanged.

SS6 `NULL_Crystal` carries the slow 3.6-degree/second Y rotation. Its 6000-frame idle makes one complete 100-second
turn. At resonance frame 134, the attachment moves below view; the body descends and holds original seated frame
174 at frame 183. `NULL_Aura` brings the native intro effect into view for preparation/resonance and moves it below
view after landing. The unit's native effect lifecycle owns cleanup. Actual attachment rotation inheritance,
component spawning and cleanup still require the user's in-game battle test; binary roundtrips cannot establish
runtime rendering. There is no global actor or shader edit.

Normal attack/cast body keys are fitted to the existing converted clip durations (Crystal Fina's attack is currently
307 frames, casting fallback 346). The resonance is 273 frames and holds its seated endpoint until the existing
432-frame presentation's recovery event. Native hit, healing, effect and movement event times are unchanged.
This preserves mechanics; the perceived alignment of the cast with existing effects still needs live review.

Local native integration generates the original converted sprites, then the complete private battle system, crystal,
material, two data tables, SS6 project and all three textures using the real asset tool. Every generated graph/table
passes strict native write/read checks. Decoding the newly generated custom-value trailer confirms the seated cell,
frame-134 hide and the 6000-frame turning idle. A clearly labeled synthetic native-format design table now exercises both zero fields through the full builder;
it is never substituted for a real game table. Native supplied source files are copied into a scratch engine and
remain unchanged. The cave's approved glass/mesh/sequence generators are unchanged.

## Studio preview

`fina_battle_preview.zip` contains checked native idle, attack and resonance WebPs. The supplied native body pixels,
original seated fallback and crystal LOD0 geometry are rendered by `scripts/render_crystal_fina_preview.py`, using
the shared body tracks and current converted action durations. The native game assets are not repainted or changed.
The software renderer shows the new shape/motion and a glow approximation; it does not execute Unreal's glass shader.
Studio labels this preview so it is not mistaken for exact game lighting/refraction.

Literal custom-Fina API routes register before the generic FFBE routes, cover both Studio and Advanced preview
requests, and bypass old generated preview files without deleting them. Other forms keep their existing routes.
Responses use no-store and the Flutter image URLs include a presentation revision, avoiding both disk and in-memory
stale previews. The selector identifies the finishing motion as Resonance. Bundled extension 1.2.18 installs the
preview module/archive along with the scale fix; it does not overwrite the old cave comparison sprites or saved kits.

The read-only collection helpers remain under `scripts/reference/crystal-fina-battle`, outputting to
`Downloads\FFR Mod`. `scripts/prepare_crystal_fina_battle.py` renders the shared motion draft without installing
assets. Runtime rendering, controller interaction and final visual timing must be checked in Resonance.
