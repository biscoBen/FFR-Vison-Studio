# Party replacement knockout — 2026-10-16

The user reported Lasswell stayed upright after knockout with regular Cleome
(5★/6★/7★/NV). He was logically dead and his equipped vision disappeared.

The returned `Party-Knockout-Reference-20261016-145454-1b5049-001.zip` contains all eight
original party SS6 projects and the native battle table. Collection succeeded with no
missing references or failed filters. Its party override list is empty, so it does not
identify the exact installed Cleome rarity or supply a generated Lasswell spec.

The native projects read back as follows (60 fps):

| Party model | Knockout motion | Frames | Other relevant motion |
| --- | --- | --- | --- |
| Rain / unit0010 | death | 11 | dying |
| Lasswell / unit0020 | death | 11 | dying, reverse_death, reverse_dying |
| Fina / unit0030 | death | 11 | dying |
| Lid / unit0040 | death | 6 | dying |
| Nichol / unit0050 | death | 11 | dying |
| Dark Fina / unit0060 | death | 6 | dying |
| Jake / unit0070 | death | 6 | dying |
| Sakura / unit0080 | death | 6 | dying |

The pinned FFBE converter instead emits **dead**, with no **death**. The native
SpriteStudio player rejects a missing animation name and leaves its previous motion
playing. This accounts for the standing replacement despite correct logical knockout.
All four checksum-verified regular Cleome forms (100030705/706/707/717) have proper
lying-down artwork at frame 19 for four ticks; dying is the separate kneeling frame 18.
Brave Shift 100030727 borrows its missing dead motion from base form 100030717.

`_ffr_party.party_motions` now copies the complete selected **dead** clip to **death**
and **reverse_death**, and **dying** to **reverse_dying**, for every party replacement.
It preserves all cells, frame counts, rates, positional offsets and the final held pose.
No shared vision converter, gameplay state, death/revival logic, idle or attack clip is
rewritten. The native player can switch back to the existing idle/command clip on revival.
This does not invent knockout artwork when a source look and its base both lack it;
the engine's existing missing-art fallback remains in effect for such packs.

Regression coverage checks native names, full falling sequences and final poses,
independent copies, unchanged idle recovery, idempotence, Nichol's mixture aliases,
and actual converter selection of main or base-form dead cells and offsets.
Native serialized build/readback and Windows package verification are recorded in the
publication changelog. Live knockout/revival confirmation remains pending.

The read-only collector and companion PowerShell script are in
`scripts/reference/party-knockout/`. Output goes to Downloads/FFR Mod. It does not
install a loader, start the game, or modify game/Studio files. PowerShell smoke checks
cover special-character paths, source immutability, exact filters, partial failures,
selected-source inclusion, unrelated-vision exclusion and output guards.

Preserve the accepted Crystal Fina presentation/timing from run 38968721767.
