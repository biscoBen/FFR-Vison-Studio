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
condition and `EventList` entries of type `TalkEventPlayData`. It runs the existing once-only acquisition event;
the trigger follows her capsule, so its button area is independent of sprite lift/size.
The user's live test confirmed the capsule blocks and manual input opens the dialog, but the old event row's
`ObtainItemList` plus obtain popup **did not add the vision**. The original Leah/Tronn acquisition timeline explicitly
calls the native director's parameterless `ExecuteHeader` and `ExecuteFooter`. The private 0.2-second grant timeline
now uses that lifecycle with the current event row and actual allocated vision ID. It has no original actor bindings,
scene/camera tracks or story changes; compiled evaluation data is invalidated. The obtain screen and return-to-cave
settings remain on that row. The invoking Transition trigger also needs an explicit return route: both its
`m_MapId`/`m_PointID` and conditional entry `mapId`/`pointId` target stone cave 29990, point 1. Keeping these at -1
left a fallback route despite the event row's correct destination; the live test returned to the overworld.
Point 1 is (3500,31,100), 500 units from the portal and well clear of its blocker and the cave exit trigger.
Visibility, interaction and grant share the same unowned-item condition. Actual
inventory acquisition and hiding on return require a live-game smoke test; the SDK cannot execute native event code.

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
