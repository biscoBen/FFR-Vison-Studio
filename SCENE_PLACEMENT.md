# Cooked map placement and interaction

These rules come from the demo's decoded maps, Blueprint defaults and `Mappings.usmap`, rather than screen-space
estimates. Implementation: `assets/existing_visions/payload/_ffr_crystal_cave.py`; regression checks:
`scripts/test_crystal_cave.py`. Native SDK and IoStore roundtrips are also checked with the supplied reference assets.

## Coordinates and size

Unreal uses world X/Y for the ground plane and Z for height. `RelativeLocation` is relative to `AttachParent`;
without a parent it locates the component in the level. Apply the complete parent transform before comparing objects.
`BoxExtent` is **half** the box size, before component/parent scale. A decorative mesh's pivot is not its center,
its floor height or its collision boundary. Read mesh bounds and the actual collision mesh, not just its origin.

SpriteStudio `UUPerPixel` converts sprite pixels to world units. The map unit's `m_SsPlayerScale` can reapply it;
set both consistently. Crystal Fina now uses 4.25, exactly 85% of the previous 5.0. This changes artwork only, not
her capsule or interaction reach. Her billboard has a separate local Z lift of 40 units. The importer preserves
FFBE part positions and cell pivots; the character origin is distinct from the surrounding crystal's visual bounds.

The NPC hierarchy is capsule → foot → penetration adjustment → billboard → shake → SpriteStudio player.
The native capsule half-height is 33.333332 and radius 18.666666; the foot is Z=-33.333332 relative to its center.
The crystal room's visible ground mesh has an origin at Z=0 and `NoCollision`; a separate colground mesh supplies
collision. Do not place characters at Z=0 based on that decorative origin. Spawn above the platform and let the
capsule fall onto the native floor with `bRunPhysicsWithNoController`, gravity and floor checking enabled. Move
interaction volumes with the capsule; a detached box at the spawn height stays suspended after the NPC lands.

Fina uses the midpoint of the two original acquisition lights (approximately X=5989.931, Y=-760.228, Z=341.971),
plus Y=144 for the user's reported two-character-width offset to the right in this room's camera.
The final 16-unit nudge follows the next live test; sprite scale remains 4.25.
Z is a safe initial height, not a measured floor surface. The lights, floor and
ambient god rays are separate effects; their combined brightest rendered pixel is not derivable from light origins
alone. The lights locate the acquisition area; exact alignment with the rendered white patch still requires a game render.
Screen-left/right changes with camera orientation and is not a universal world axis.

The native clear crystal's mesh bounds have origin (-0.014322, -0.919101, 48.652589) and half-extents
(27.772989, 27.477618, 58.152823). At its copied scale of 3, horizontal half-extents are about 83 units. The portal
blocker uses 85 horizontally and spans Z=-200..400, containing both the native floor reference Z=0 and the
portal trigger's Z=100. The visual
crystal's elevated pivot is not used as the collision center.

## Interaction and blocking are separate

A `CPP_MapTransitionTrigger` root intentionally overlaps Pawn; it detects proximity for automatic/manual transitions.
`m_IsAutoTransition=False` requires the interaction button. A marker mesh and an overlap trigger do not form a wall.

Fina's dedicated manual trigger uses native `MAP_TRANSITION_TRIGGER_DATA.isEventOnly=True`, an unowned-item
condition and `EventList` entries of type `TalkEventPlayData`. Restore the earlier native NPC talk binding too;
both use the same conditioned event and allocated vision ID. Keep this event-only lifecycle: running the grant as a
regular transition pre-event in run 37157852608 regressed controller confirmation of the obtain dialog (mouse still
worked). The trigger follows the grounded capsule, independently of sprite lift/size.

The obtain popup alone did not grant the vision. The original Leah/Tronn timeline explicitly calls the native director's
parameterless `ExecuteHeader` and `ExecuteFooter`; the private 0.2-second timeline uses those with the current event row.
It has no original actor bindings, dialogue, camera tracks or story changes; compiled evaluation data is invalidated.
Keep the obtain screen, white loading setting and `TransitionLocation` stone cave 29990 / point 1 on that row.

The live test found **both** ordinary room exit and acquisition returned outside the new cave. Both targeted point 1;
overworld entry via point 0 worked. Therefore the acquisition-only explanation was insufficient. The copied native NAV
level still referenced `Dng_01Gra_44_01_GD.PersistentLevel.BP_MapTransitionTrigger_C_1` and lacked our portal connection.
This was an observed stale reference, not proof of the native C++ warp's cause.

Use a private `_Stone_NAV`, retaining its cooked Recast chunks, bounds, export indices and opaque physics. Its
`m_TransitionTriggerList` must point to the private `_Stone_GD` exit and portal actors. Retarget the persistent level's
AlwaysLoaded NAV stream. Place point 1 in `_Stone_PL`'s actor/dependency lists, with its native root component and an
explicit `m_AreaBoxList` soft reference to the private `CPP_Map_NavMeshBoundsVolume_1`. Do not depend on the dynamically
streamed GD level for the return point. Keep native point 0 in GD for entry.

Point 1 is (3500,31,100), 500 units from the portal and clear of its blocker and the cave-mouth exit trigger. The cave
mouth exit now requires a button too (`m_IsAutoTransition=False`); arrival cannot automatically walk-trigger another
map change. The ordinary room exit and acquisition row both target the same persistent point. The build console prints
this route and the manual-exit setting so an installed rebuild can be identified.

The user confirmed grant, hiding, size and collision. Revised return placement and restored controller confirmation
still need live-game testing. SDK/IoStore checks verify authored actors, links and cooked data; they cannot execute the
native map task or establish its runtime event ordering.

The generic Actor/instance BoxComponent approach passed serialization checks but **did not block in the game**.
Use the native `BlockingVolume_1` from `Dng_01Gra_43_GD` instead. Its constructor supplies the BrushComponent;
its BodySetup contains a cooked Chaos convex, with `CTF_UseSimpleAsComplex`. Preserve the complete level's
export/name indices and opaque Model/physics bytes. Activate only its world settings and volume in the actor list.
Scale the BrushComponent from the actual convex half-bounds (375,100,300), then place it at the trigger's ground
location. Load these private collision levels through native `LevelStreamingAlwaysLoaded` entries in the persistent
world (`Wld_PL` for the entrance, the private stone-cave PL for the portal), retaining every original stream.
The user confirmed both repaired volumes block in-game. Do not treat an overlap trigger or a successfully
serialized generic component as proof of blocking.

Keep a wider interaction volume around each blocker. The player must be within the trigger while standing outside
the solid box; leave more than the capsule radius between their horizontal bounds. The portal trigger is half-size
160×200×200; its blocker is 85×85×300. The overworld trigger is 160×250×350; its blocker is 90×150×350.

## Cooked asset safeguards and limits

Preserve original export/name indices and opaque bytes. Append names and retain the complete referenced-name prefix
through IoStore; stale prefixes caused the earlier `Bad name index` crash. Remap only fully decoded graphs, including
component owners, attachments, delegates, imports and preload dependencies. Use actual Blueprint declarations in
private mappings; aliasing a Blueprint to its C++ parent shifts unversioned property indices.

Validate event conditions, component registration, profile/type, parent-relative positions and serialized readback.
Pack and re-extract the final maps to verify IoStore name/reference retention. A roundtrip proves asset integrity,
not live input/collision behavior. The supplied assets expose serialized settings and Blueprint defaults; native C++
interaction code, the running game and the complete collision mesh are not available in this workspace. Do not
claim that screenshots or data inspection alone prove runtime placement. Future scenes need their native donor
map, geometry/collision bounds and an in-game smoke test before being called gameplay-verified.

## Editable Resonance Cave placements

Version 2 cave snapshots store the footprint center in world X/Y, absolute base Z, yaw (degrees) and size relative
to the earlier entrance normalization (75% by default). Version 1 snapshots remain readable; generic caves gain
native grounding and 75% sizing, while the tested original Crystal Fina placement stays unchanged until edited.
The engine and preview normalize the selected mesh to a horizontal half-bound of `120.52937316894531 * .8`,
then apply the saved size. Subtract the yaw-rotated native bounds origin from the actor pivot so the transformed
footprint center equals the saved XY. Clear donor pitch/roll; place the transformed lowest bound at saved Z.
The blocker is centered at Z + 160 and its horizontal extents follow the saved size; the wider trigger retains reach.

`scripts/build_cave_terrain.py` decodes the supplied single-subsection 128-square UE5.6 mip0: U16 big-endian deltas
start at 32768 and accumulate across rows. Check every decoded minimum/maximum against CachedLocalBox; world
height is root Z + (height - 32768)/128 * root Z scale. The shipped data covers Grandshelt and Dirnado, not all regions.
Both Studio and engine bilinearly sample the same checked data. Moving in the editor preserves the offset above
terrain; Snap to ground clears it. Older generic placements without Z use native height if covered, otherwise zero;
set Z manually where references are absent. Full-game source refresh is tracked in README.

The portal uses a separate item-free event row with LoadingScreenSetting=White, the existing header/footer timeline,
and TransitionLocation targeting this cave's crystal room / point 0. Its manual trigger is event-only, preserving
controller input ownership. The acquisition event, ownership condition and stone-cave return remain separate.
Native SDK and IoStore readbacks validate the graphs, transformed bounds and route data; they do not run the game.
