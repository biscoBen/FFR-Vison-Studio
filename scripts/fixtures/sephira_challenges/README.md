# Full-game shrine challenge fixtures

These scoped rows and two small interaction maps come from the user's official full-game references,
collected on 2026-10-22. They are test inputs, not installable game overrides.

Game fingerprint: `8ce7a0746d0cc1b2c9b97e44d186f8036212b156fc52b91571da94703168b5b4`.
The native reference ZIP SHA-256 is `09fc7c7d31047bb5c89a0dde20ed81d0ad0efc950af8dce63efc9dd34609537f`;
the prepared shrine-table ZIP SHA-256 is `a393967156ad5d9a1bcc0712cfb96f30e9131138934971f00a311e199b79dc3b`.
World interactions and Blueprint declarations were subsequently supplied in the small world and schema packs.

`rows.json.gz` retains the native donors used by the challenge builder, original grant/replay rows, boss curve
anchors and item prices. The source-correction regression additionally retains all native MR rows, passive/effect definitions, equipment bonus references, the Mitra inventory and the new enemy-skill donors. `tronn-room.json.gz` is the original Com_00Com_237_PL, with its two dynamic streams.
`crystal-interaction.json.gz` is the decoded native WoL repeat-crystal interaction, Com_00Com_223_EV.
`repeat-crystals.json.gz` retains all 13 native shrine repeat-interaction levels from the same world reference.
The decoded Blueprint fixture also includes the native button-operated `BP_MapGimmick_InteractEventTrigger`,
whose C++ parent differs from the automatic overlap trigger. These fixtures verify targeted class/archetype
replacement while preserving unrelated story actors, original event movement, conditions and replay paths.
All gzip streams have deterministic timestamps. The boss bytecode fixture is shared with the earlier Fina test.

The accessibility regression also retains the native `01Gra_44` secret-cave row
from both physical map tables. It is the room/path behind Rain's house requested
for Christine, replacing the blocked Tronn crystal-room placement. The private
challenge appends its guarded entry prompt and instance-loads the same native
battle stage; original map startup events and story state remain intact.

The entrance-to-encounter-volume audit applied the native 32-unit box half-extents/sphere radii, cooked overrides,
scale and rotation, then used the highest-priority enclosing volume's weighted ordinary-enemy median level.
Cactuar/gil/metal specials and boss-category actors do not set ordinary area levels. Tronn uses the Earth Shrine's
inner-floor encounter table; Wilhelm's new cave uses Zoldaad's fifth area. The resulting runtime manifest records
native encounter tables, ordinary enemy IDs/levels and the original individual quest/flag unlock evidence.

Native verification also patched all 29 physical full-game tables through the pinned engine's real ffr-dt,
read back every row, and checked all generated AI, dialog, grant and Tronn-interaction packages. This verifies
serialization and original-row preservation, not controller behavior or combat balance in a running game.
