# Christine's cave crystal

The normal level-2 challenge is in the secret cave behind Rain's house in
Grandshelt, on the route toward the original Tronn/Leah room. Disable the
**Sephira visions: 1-gil Mitra shop** override to use that acquisition route.
The visible blue crystal is in the wider area at the north end. Interact with
it to open the challenge menu; entering the cave no longer opens a prompt.

The original Tronn item or story completion is required. Winning grants Christine
once. Losing, escaping, cancelling and entering the cave grant nothing. After
acquisition, the crystal remains and reports that the vision has joined you.
Removing, disabling or moving Christine suppresses the normal challenge.

## Placement and preservation

The returned full-game reference supplies actual `01Gra_44` / map 10001,
`/Game/Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL`, plus its background, navigation,
gimmick, event, sound and lighting levels. The native end-of-passage story
interaction is at X=5260, Y=-45, Z=75, and the native north-facing move target
is at X=4279, Y=31, Z=0. The new crystal is at X=5000, Y=31, Z=160; its approach
point is X=4700, Y=31, Z=0. Positive X is north on this map.

The native blue shrine crystal mesh/material and input interaction are cloned
into one private always-loaded level. All original cave streams, actors, story
conditions, navigation, exits and lighting remain; only an additional stream
reference is appended to the cave parent. No original crystal room is patched.
Native row/map/object readback and IoStore packing pass. Visibility, player
approach and interaction in the user's running game still need testing.

The two returned upload archives have SHA-256:

- `Christine-Cave-Reference-20261023-173751-cbffe5-001.zip`: `c1198cf5fa86678442b52a84fddf4166acd0118390114da5fdfe52cf170e93be`

- `Christine-Cave-Reference-20261023-173751-cbffe5-002.zip`: `d928966b62d8aeea004a9c21c24a4674d6090a832ae237d62636f9f068a0b325`

## Follow-up to the user's missing-crystal test

The user confirmed the shop override was off, the game was restarted, and the
cave re-entered. The added AlwaysLoaded streaming declaration did not produce a
visible crystal or interaction. The revised placement appends the decoded crystal,
trigger and approach-point graph directly to the cave's existing
`GD/Dng_01Gra_44_01_GD` level instead of depending on a new stream. Original name
and import indices, opaque story actors, exits and preload dependencies are retained.
Native serialize/readback passes; appearance and interaction still need a live test.
The optional `scripts/reference/cave-music` observer records F8 world/stream states
and installed scoped assets without rebuilding or preparing the game.
