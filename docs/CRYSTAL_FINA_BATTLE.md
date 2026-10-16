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
rotates on SS6 Y at 3.6 degrees/second, with a 6000-frame idle covering one turn. The accepted runtime explicitly turns the real mesh; the SS6 socket alone does not supply world yaw.

## Direct battle runtime (extension 1.2.26)

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
The fixture deliberately rejects registry-only loading and exercises cleanup/recreation on hidden actors and interruption.

**Do not rebuild this Niagara system with `tojson` / `fromjson`.** Native `NiagaraVariableWithOffset` and renderer
binding records contain fields omitted from that JSON representation. A direct native read found the source's
`User.Alpha` at offset 0, `User.EffectPosition` at 8, `User.LightPower` at 48 and `User.NiagaraAlpha` at 52. The JSON
copy had invalid names and every offset was zero; the game log nevertheless showed both components spawning.
JSON-to-JSON readback cannot detect fields omitted on both sides. Use `clone-package` with only package/object
name-map renames. Require the complete `.uexp` to remain byte-identical (117,357 bytes for this demo source), which
preserves native variables, curves, bindings and VM. Keep the original game package untouched.

The 12:13 runtime diagnostic proves extension 1.2.25 was installed and running. Its measured battle depth scale is
**0.139999996**, versus the cave's **0.138**, producing bias **12.08664**. This rejects the explanation that a much
larger inherited depth scale caused the difference. The adjustment was functional but almost identical to 12;
it was not an effective body-clarity fix. Both native body materials are masked, so translucent sorting remains
unproven. The screenshot shows severe bending across the deeper lower section of the casing.

The battle-only control now targets **20% refraction at the deepest of five head-to-feet body probes**, instead
of trying to infer clarity from component scale. Read the original native LOD0 positions/triangles with the same
strict codec used by the preview. Precompute centered triangle edges into runtime metadata; retain original mesh,
material and bulk bytes. With the actual player-camera location, transform each body probe/camera into mesh-local
space, intersect its ray with the original triangles (Moller-Trumbore), transform the front hit back to world space
and measure separation along the camera's view direction. Choose the last intersection before the camera,
which is the surface nearest the camera even with overlapping/concave facets. Sample the deeper lower body as
well as the center.

The shader's soft gate is `saturate(D / max(1, min(b/2, 50)) - b)`. Solve it for `b` with desired gate `s=.20` and
measured separation `D`: normally `b=(sqrt(s*s+8*D)-s)/2`, with the native minimum/maximum range branches. Apply it
only to an owned MID on Fina's battle mesh. This reduces bending over the sampled body while distant background
can still reach full refraction; foreground facets, opacity, roughness, Fresnel, geometry and rotation remain.
The target is an artistic readability choice, **not a measured match to the cave shader/camera**. Probes use the
physical sprite plane rather than reading GPU scene depth, so material pixel-depth offsets and unsampled pixels
can differ. A live visual test is required; do not describe the model as proof of all body pixels being capped.

The UE HLSL translator explicitly compiles `RefractionDepthBias` as a scalar parameter for SingleLayerWater as well
as translucent blend modes; `MaterialTemplate.ush` supplies it to the refraction data. This validates the parameter
path. Logs record measured view depth, target, applied bias, MID readback and camera FOV by phase, plus glow cleanup.
Missing cameras keep the accepted cave bias and retry. Preserve the battle body material's status/flash behavior.

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
- [SS6 attribute decoder (legacy flips ignored; image flips supported)](https://github.com/SpriteStudio/SS6PlayerForUnrealEngine4/blob/master/Ss6PlayerExamples/Plugins/SpriteStudio6/Source/SpriteStudio6/Private/SSSDK/ssplayer_animedecode.cpp)
- [SpriteStudio reflected signatures](https://github.com/SpriteStudio/SS6PlayerForUnrealEngine4/blob/master/Ss6PlayerExamples/Plugins/SpriteStudio6/Source/SpriteStudio6/Public/Component/SsPlayerComponent.h)
- [PrimitiveComponent reflected MID API](https://github.com/chenyong2github/UnrealEngine/blob/5.3/Engine/Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h): CreateDynamicMaterialInstance owns/applies the instance to its mesh.
- [MaterialInstanceDynamic reflected scalar API](https://github.com/chenyong2github/UnrealEngine/blob/5.3/Engine/Source/Runtime/Engine/Classes/Materials/MaterialInstanceDynamic.h): SetScalarParameterValue updates only that instance.
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
output gaps and recovery, then exercises native attack recovery and the warm glow envelope. This establishes a regression fix
for the observed failure; the corrected visuals still require a live game test.

## Short native attack and resonance

The supplied 11:01 trace finally shows the full cast completing, but also proves why damage appears first:
`magic_idle` lasts 0.516 seconds, `magic_attack` lasts 0.516 seconds, while the former independent 229-frame cast
continues for 3.817 seconds after release. The user chose the game's short timing. Remove all runtime `Play` /
`SetPlayRate` overrides; native preparation, release, impact and recovery now own playback again.

Split the native body at `magicattack6` frame 66, the first hands-forward shooting pose (`npc_0_15`): eye opening,
turning and charge from the preceding 204 source frames fit the **30-frame preparation**; the remaining shot cells
fit the **30-frame release**, beginning with the shot at release frame zero. The supported release aliases share
that body. This aligns the shot to the observed native release cue rather than leaving it several seconds after
impact. The diagnostic is a motion trace, not a timestamped damage-event trace; precise on-screen impact alignment
still needs live confirmation. Skills, hit keys and damage remain unchanged. Skill-animation duration calculations
use the 0.5-second release, not the preview's combined 1-second body. `Studio_FinaCast` is now only a preview
concatenation of preparation and release, never an independently played runtime animation.

Both attack and resonance use SS6 body **`Imgfliph=1`**, preserving native texture pixels and socket origins;
return to unflipped idle when she reforms. The public SS6 decoder comments out legacy `Fliph` handling as unsupported,
but explicitly reads `Imgfliph` into `imageFlipH`. A serialized legacy flag is not evidence of a rendered mirror.
Read back every native `Imgfliph` key and its `Bool_temp` fallback cache (the writer stores these as FloatType values).
The labeled Studio preview consumes the same supported track. The seated hold is now exactly 75 frames (1.25 seconds), down from 100 in the preceding test.

| Resonance phase/frame | Presentation |
| --- | --- |
| `lb1_before` starts | Activate body-centered native gold effect immediately |
| LB1 0–133 | Build native particles to full brightness before the fall |
| 134 | Hide mesh and begin descent; native reaction key unchanged |
| 134–164 | Fade the single glow out; hide/destroy it at 164 and latch completion |
| 183–257 | Jacket-free seated pose, with **no glow** |
| 258 | Restore crystal and floating pose, with **no second pulse** |

The remaining ground flash was an authored second pulse at frames 210–282. It started while the body/socket was
seated, so moving destruction to frame 282 left it intact. The supplied trace has a single initial component spawn,
consistent with reusing that warm component for the second pulse. Remove the second envelope entirely; merely
blocking late frame resets does not address that scheduled flash. Keep early build-up, mirroring and 75 seated frames.

Spawn the private native aura directly with NiagaraFunctionLibrary.SpawnSystemAttached at `NULL_Aura`, auto activation
off. Set `User.Alpha=2`, `User.NiagaraAlpha` to the current envelope before activation, `User.EffectPosition=0` and
`User.LightPower=0`. Keep the valid preparation/body attachment, then hide and destroy the owned effect as soon as
its one fade ends. Use the component itself as the explicitly permitted K2_DestroyComponent context. Log cleanup.
Retain the completion latch through frame resets/name gaps, and reset it for a genuine later resonance. Native
Niagara creation allows destruction and uses the attachment owner's actor; an ownership failure was investigated
but is not established as the cause. Preserve the native clone's opaque metadata/VM; never JSON-roundtrip it.

The native Fina design row still receives explicit positive 2.7/1.0 presentation defaults only for nonpositive
Scale/attachEffectSacle values; positive values and other rows remain unchanged. The cave pair stays at the user's
accepted 15% enlargement, with its approved glass and spin. No old comparison NPC is generated.

## Studio and verification

`scripts/render_crystal_fina_preview.py` shares battle tracks, flipping and timings, and renders supplied LOD0 mesh
and sprite pixels. Its lighting/glow is a labeled approximation. Bundled WebPs use `native-fina-8` to invalidate
stale previews. Local native checks use the real asset writer, verify model parents/custom-value tails including
Imgfliph and its bool cache, short preparation/release cells and the restored casing, then pack and verify IoStore. A synthetic zero-scale design fixture
is confined to scratch. No user game data is replaced by fixtures.

Executable Lua fixtures cover actual animation-name out tables, owned movable mesh creation, scale/pivot setup,
native recovery without presentation overrides, short native attack windows, mirrored asset contracts, single-pulse glow,
crystal hide/return, hidden actors, project swaps and cleanup. They cannot prove this game's rendered behavior.
Windows checks cover the frozen engine and managed runtime resource. Live use after the correction still needs checking the
actual crystal, glow, shot direction and battle completion; use the automatic `[FFR Fina]` log if anything fails.
Collectors continue to write to `Downloads\FFR Mod`.


## Gentler normal attack timing (2026-10-16)

After accepting the glass and single glow, the user requested a slightly slower normal attack and matching damage.
The private SS6 phases remain 30 frames each; the runtime applies **0.8×** to both the body and the owning action's
clocks (25% longer). Studio's concatenated preview uses 48 fps to represent the same rate.

The supplied mapping declares `CPP_BtlJobSkill.m_pActionUnit`, `m_pLinkUnit`, `m_TimelineList`, and inherited
`CPP_BtlJob.m_ActionUnitList`, `m_pLevelSequenceActor`, `m_pSoundSequenceActor`. Match the private Fina actor
through owner/link/action lists; never through targets. Retiming uses `UTimelineComponent.SetPlayRate` and
`UMovieSceneSequencePlayer.SetPlayRate` via the level/sound actors' `GetSequencePlayer`. No damage event is
removed, duplicated or synthesized, and no global speed or party data is changed.

Clocks and the sprite retain their native base rate, including existing battle speed. Repeated scans do not
multiply the slowdown. Restore only our own applied value on recovery, loss of association or cleanup. Without
a linked native clock, keep the body at native speed; an unsupported timing API disables only timing and leaves
the approved crystal/glow running. Logs distinguish a linked slowdown from that fallback. The mapping verifies
property names, not live job relationships: the actual game's associations and perceived hit alignment remain
an in-game validation requirement. Resonance is excluded by its animation names.

Verification for this candidate: static analysis, 20 focused Flutter tests and 377 Python checks pass (four Linux
skips). Real make-ss6/readback verifies native preparation/release at 60 fps and the preview concatenation at
48 fps; emitted runtime configuration carries 0.8× and the unchanged single glow/258-frame reformation. Native
mesh/material/glow construction and IoStore pack verification pass. These do not simulate live game scheduling.
