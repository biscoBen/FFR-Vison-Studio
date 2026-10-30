# Optional treasure radar and encounter testing

Studio bundles the three exact files supplied in
`MinimapShowTreasure_FieldObjects 90 1 2026-10-25T12-13Z owJxyjy1f.zip`.
The minimap toggle installs/removes them directly, with Resonance closed; no
vision rebuild, UE4SS loader or save modification is involved. The switch is
beside **Disable random encounters** with the other main toggles. Restart the game
to load or unload the package. Studio reads the files actually present in the
selected game, rather than relying on a saved checkbox from another PC.

The original `MinimapShowTreasure_P` basename is retained. New installs go in
`FFRS/Content/Paks/~mods`; exact existing copies in the main `Paks` folder are
recognized and are not duplicated. An explicit OFF removes recognized copies.
Different or edited versions are preserved. “Restore the original game” removes
only copies this Studio installed, keeping a pre-existing manual installation.
This local toggle is independent of vision builds and private Deck snapshots.

## Package inspection

The PAK contains no loose files. Its uncompressed IoStore container overrides
only these three assets:

| Asset | Purpose |
| --- | --- |
| `UI/Field/MiniMap/Entry/Data/DA_MiniMapEntryProperty` | Enable display properties for treasure/check objects. |
| `UI/Map/Icon/Data/DA_MapIconBinding` | Bind the field-object tags to map icons. |
| `UI/Field/MiniMap/Widget/WBP_MiniMapEntry` | Hide collected chest and field-pickup entries using native state. |

The widget's replacement `SetDisplay` function contains 30 decoded Kismet
expressions (1,229 serialized bytes). It resolves the entry's `ReferenceActor`,
casts it to `CPP_MapGimmick_TreasureBox` or `CPP_MapGimmick_FieldItem`, calls the
native `IsOpen` methods, then calls `orig_SetDisplay(false)` for collected
objects. Other entries retain the original display path, with a special check
for generic `Field.Object.Interact.Type.Check` entries. The native names and
function identities were cross-checked against the captured script-object data.
The supplied game package itself is unchanged.

This uses the game's current collected/open state, rather than starting a new
collection history when the mod is installed. It should respect existing saves
and previously visited dungeons. Respawning field pickups follow the game's
own respawn state. Static inspection cannot certify every tablet variant or
the timing of live marker refreshes; these still need an in-game check.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `MinimapShowTreasure_P.pak` | 347 | `75e7144577253917f6da7312ef5e585b12fb728226a22b0938323751a6b555cd` |
| `MinimapShowTreasure_P.ucas` | 23,492 | `5776c39b5b2790b6f7533d6cd8345df55596d75cd8495268bbd848f279fd1642` |
| `MinimapShowTreasure_P.utoc` | 819 | `6bba1df558c8ea077195734037d988d3b544dfd43c5dd9e6e574606f2c289588` |

## In-game encounter toggle

The user isolated intermittent native crashes in 1.2.137 to the encounter
controller: removing auto-battle did not resolve them, while encounter control
OFF stayed stable with auto-battle ON. The 1.2.139 candidate stops retaining a
field-player UObject across frames, resolves its object path afresh, checks
battle/event boundaries before field access, and rejects actor/HUD objects that
have begun destruction even when the loader still reports IsValid. The current
status compares object addresses without dereferencing a previous field actor.
These changes cover unsafe lifetime handling; long-session in-game validation
of the corrected encounter controller is still required.

Enable **In-game encounter toggle** in Studio, rebuild/install once, and restart
Resonance. Install the bundled UE4SS loader if Studio offers it. This replaces the
previous always-off map-table patch; native map flags now remain intact.

Press **F7**, or hold **both controller triggers (LT+RT / L2+R2) for one second**
while freely walking. Release both triggers before holding them to toggle again.
The shortcut reads digital button-down states only in native walking input
contexts. It suspends while the world map, destination list or another menu has
input; a hold carried back from those screens must be released before toggling.
The bottom-left field HUD shows **Random encounters: ON/OFF**. ON restores normal
game rules, including any native equipment effects. Encounters start ON at every
game launch. The choice is session-only and uses no equipment/ability slot.

The runtime temporarily applies the game's native Dragon Seal encounter effect
(effect 71000, passive source 1052) to live map parameters while OFF. It uses no
equipment or learned-ability slot and does not change save data. Only effect
instances created by Studio are removed when normal control resumes; equipped
Dragon Seal and other buffs remain. Menus, non-ground vehicles, events, battles and map
transitions release Studio's effect, with OFF reapplied on return to free walking.
Scripted/boss battles and rewards remain intact.

The working suppression path uses the resident native skill-effect row, copied
by Unreal rather than converted through a Lua table. It does not write actor
encounter ratios, walking thresholds, equipment or saves. Foot, chocobo and
magitek-armour travel remain supported.

An unavailable HUD leaves native encounters unchanged and logs the reason with
`[FFR encounters]`. Executable fixtures cover restoration, native row identity,
keyboard/controller toggles, map/event guards, retiring actors and HUD widgets,
and recovery on the next map. Keep auto-battle's existing controls and placement.

## Dungeon remaining-item counter

With treasure radar enabled, **Items left: N** appears at the minimap's bottom-left.
It includes unopened chests, glowing pickups and tablet fragments throughout the
current dungeon or shrine group, including other floors. It counts locations,
not item quantities. Collections from before installing the mod are recognized.
The counter reads the game's saved collection state and never writes saves.

After updating from an older radar install, close Resonance, switch **Show treasure
on the minimap** OFF and ON once in Studio, then restart the game. This installs
both the original radar and its small counter companion. No vision rebuild,
observer or UE4SS is required for the counter. Studio preserves recognized manual
radar files and adds only missing companions; restoring removes only owned files.
Explicitly switching OFF removes the exact reviewed radar/counter packages.

The original radar's three files retain their reviewed hashes. The companion
`FFRStudioTreasureCounter_P` adds one native minimap text binding, preserves the
native map functions and places its slot outside rotating panels. Its getter uses
`IsOpenTreasureBox(savedMapId, uniqueId)` for chests, pickups and fragments, rather
than relying on currently loaded actors or chest-only totals. Decorative chests
that start open are excluded. The captured native scope covers 108 dungeon/shrine
maps and 201 collectible locations; unknown world/town maps hide the label.

Native serialization and packed-getter checks pass. The user reports that the
counter is working after the OFF/ON upgrade. Detailed in-game coverage of every
dungeon and collection type remains
separate from the executable saved-state checks. The independent runtime status indicators use a
private passive UserWidget with one plain TextBlock and an explicit font, rather
than the game's input-aware key-guide contents. Those indicators still require
UE4SS and a control rebuild/install; controller targeting and rendering remain
subject to the live test.
