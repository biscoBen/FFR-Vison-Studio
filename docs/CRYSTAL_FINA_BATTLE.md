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

## Direct battle runtime (extension 1.2.22)

The last asset-only attempt passed native serialization but the user still saw no casing or sequenced glow. Its
Niagara ComponentRenderer route and owner-versus-vision effect selection are not established runtime behavior.
They are retired from the builder. Do not describe a successful binary roundtrip as proof of rendered effects.

The current battle presentation uses the working UE4SS loader already needed for field cycling. It composes the
Fina module into the same three owned runtime files, retaining installation preflight, backups, restore and Deck
transfer. Cycling can remain off: its map hooks are not installed in a Fina-only payload. Removing Fina and turning
cycling off stages an empty payload. A missing loader stops installation before game files change; no loader is
silently installed. No save, gameplay, party identity or global Blueprint changes are made.

Read Actor.bHidden through reflection; Actor.IsHidden is an inline C++ helper, not a callable UFunction.
The source/API checks and Lua fixtures do not establish that the shipped game renders the result correctly.

`fina_battle.lua` finds native SsPlayerComponents whose project matches the current private Fina project, and whose
owner is CPP_BtlUnit or CPP_BtlSequencerSsPlayerActor. UI renderers, map/cinematic actors and other models are excluded.
If the actor/project disappears or changes, destroy only the components created by this module. Errors clean up
owned components and log `[FFR Fina] Presentation stopped: ...` in the existing UE4SS log.

Use KismetSystemLibrary.MakeSoftObjectPath → Conv_SoftObjPathToSoftObjRef → LoadAsset_Blocking for private
packages. UE4SS LoadAsset uses AssetRegistry.GetAssetByObjectPath and can fail for injected assets absent from the
original registry. Unreal's soft-path loader resolves mounted packages directly. Refresh references when components
are created, and reload an invalid glow asset before later pulses; Lua wrappers do not establish GC ownership.
The fixture deliberately rejects registry-only loading and simulates collection between glow pulses.

The runtime loads the private approved StaticMesh/material, creates an ordinary **movable**, non-colliding
StaticMeshComponent and attaches it directly to the SS6 `NULL_Crystal` socket. This uses the same ordinary mesh
shader family as the working cave. `SetMobility(Movable)` precedes attachment, since a static component cannot be
attached to a moving sprite component. Preserve native mesh/bulk bytes, bounds-origin correction and material.

The public SpriteStudio plugin implementation establishes the relevant transform contract:
`GetSocketTransform` resolves part names and composes their transform with the component transform.
`GetPartAttachTransform` multiplies translations by UUPerPixel, but returns scale `(1, partScaleX, partScaleY)`;
it does not multiply socket scale by UUPerPixel. Set the mesh's relative scale to `.12/2.7 * UUPerPixel` so both
actor-scale and pixel-scale configurations retain the approved body/casing ratio. The native bounds origin is
subtracted at that same local scale. The plugin calls UpdateChildTransforms while ticking. Its socket API exposes
an in-plane angle, so rotate the real mesh component about its vertical axis at 3.6 degrees/second instead of
assuming SS6 Roty becomes world yaw. Hide the owned mesh explicitly during the resonance's fall/seated interval.

Source inspected:
- [SpriteStudio component implementation](https://github.com/SpriteStudio/SS6PlayerForUnrealEngine4/blob/master/Ss6PlayerExamples/Plugins/SpriteStudio6/Source/SpriteStudio6/Private/Component/SsPlayerComponent.cpp)
- [SpriteStudio reflected signatures](https://github.com/SpriteStudio/SS6PlayerForUnrealEngine4/blob/master/Ss6PlayerExamples/Plugins/SpriteStudio6/Source/SpriteStudio6/Public/Component/SsPlayerComponent.h)
- [UE4SS LuaUObject.cpp at the installed e3ba1016 version](https://github.com/UE4SS-RE/RE-UE4SS/blob/e3ba1016/UE4SS/src/LuaType/LuaUObject.cpp): non-struct out parameters are written into caller-supplied tables under their reflected parameter names.

The user's 2026-10-16 diagnostic log confirms the installed mod starts, matches the correct private Fina project,
loads the real mesh/material/glow and successfully attaches the mesh to CPP_BtlUnit at UUPerPixel=3.5. The very next
update fails at `name(animation.OutAnimationName)`: the assumed field is nil. Error cleanup immediately removes the
mesh and disables both glow and full-cast playback. The previous fixture copied the upstream field spelling and
therefore missed this game/UE4SS difference. The log does not reveal the game's actual parameter spelling.

Keep native actor identities and gameplay events intact. Read the **actual component animation** with
`GetPlayingAnimationName(outputs, outputs)`. Both caller arguments refer to one output table; identify the verified
private pack by its exact value and take the other FName as the current clip. Reflected parameter labels and table
iteration order are irrelevant. Do not assume an upstream header's parameter spelling or use an actor's cached
motion-name property. Temporarily missing/ambiguous outputs keep the casing alive and retry without starting a
new cast or aura. Log the first populated output fields, waits and initial motion/frame/rate transitions.

A reproduction using renamed output parameters makes the previous runtime fail at the same nil dereference and
remove its newly attached mesh. The corrected fixture tests renamed/reordered labels, upstream labels, startup
output gaps and recovery, then exercises the full cast and both glow pulses. This establishes a regression fix
for the observed failure; the corrected visuals still require a live game test.

## Full casting motion and resonance

Preparation now only opens her eyes; it no longer repeats the curled-up turn. `Studio_FinaCast` contains the exact
approved 229-frame body sequence: 65 eye-opening frames, 73 turning frames, 91 charge/fire frames. During an ordinary
release, play this private clip at rate 1 and one loop. If native preparation/recovery calls replace it early,
resume the correct absolute frame from the world game clock. Leave it playing naturally between interruptions;
do not restart at frame zero every tick. Death, damage and resonance motions cancel the cosmetic override.
Once complete, restore the native current pose, using idle for an expired ordinary release. No hit/healing/movement
keys are changed. An immediate later action can supersede this cosmetic presentation without changing game logic.

Both attack and resonance use SS6 body `Fliph=1`, preserving native texture pixels; return to unflipped idle when
she reforms. The seated hold is now exactly 75 frames (1.25 seconds), down from 100 in the preceding test.

| Resonance frame | Presentation |
| --- | --- |
| 0–121 | Float in crystal; no gold glow |
| 122–134 | Fade body-centered native glow in |
| 134 | Hide mesh and begin descent; native reaction key unchanged |
| 134–164 | Fade glow out, then destroy its component |
| 183–257 | Jacket-free seated pose |
| 246–258 | Fade second glow in at the current body socket |
| 258 | Restore crystal and floating pose |
| 258–282 | Fade second glow out and destroy its component |

Spawn the private native aura directly with NiagaraFunctionLibrary.SpawnSystemAttached at `NULL_Aura`, with auto
activation off. Set User.Alpha and User.NiagaraAlpha to zero before activating; update them from the actual LB1
frame and the shared triangular fade envelope. Destroy the component at the end of each pulse or when hidden.
Disable the private aura's light renderers to avoid lighting the floor. All native VM/particle bytes and original
source effects remain intact. Runtime parameter setters avoid the asset writer's unsupported EX_ArrayConst arrays.

The native Fina design row still receives explicit positive 2.7/1.0 presentation defaults only for nonpositive
Scale/attachEffectSacle values; positive values and other rows remain unchanged. The cave pair stays at the user's
accepted 15% enlargement, with its approved glass and spin. No old comparison NPC is generated.

## Studio and verification

`scripts/render_crystal_fina_preview.py` shares battle tracks, flipping and timings, and renders supplied LOD0 mesh
and sprite pixels. Its lighting/glow is a labeled approximation. Bundled WebPs use `native-fina-5` to invalidate
stale previews. Local native checks use the real asset writer, verify model parents/custom-value tails including
Fliph, full-cast cells and the restored casing, then pack and verify IoStore. A synthetic zero-scale design fixture
is confined to scratch. No user game data is replaced by fixtures.

Executable Lua fixtures cover actual animation-name out tables, owned movable mesh creation, scale/pivot setup,
early recovery without truncation, native full-rate playback, mirrored asset contracts, no idle glow, pulse alpha,
crystal hide/return, hidden actors, project swaps and cleanup. They cannot prove this game's rendered behavior.
Windows checks cover the frozen engine and managed runtime resource. Live use after the correction still needs checking the
actual crystal, glow, shot direction and battle completion; use the automatic `[FFR Fina]` log if anything fails.
Collectors continue to write to `Downloads\FFR Mod`.
