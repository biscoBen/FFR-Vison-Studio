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

Enable **In-game encounter toggle** in Studio, rebuild/install once, and restart
Resonance. Install the bundled UE4SS loader if Studio offers it. This replaces the
previous always-off map-table patch; native map flags now remain intact.

Press **F7**, or hold **both controller triggers (LT+RT / L2+R2) for one second**
while freely walking. Release the triggers before holding them to toggle again.
The bottom-left field HUD shows **Random encounters: ON/OFF**. ON restores normal
game rules, including any native equipment effects. Encounters start ON at every
game launch. The choice is session-only and uses no equipment/ability slot.

The runtime sets the field player’s native `m_OverwriteEncountRatio` to zero while
OFF and remembers its prior value. It restores that value during menus, vehicles,
events, battles and transitions, then reapplies OFF when free walking resumes.
New native zone overrides are retained. Scripted encounters, boss/challenge
rewards, equipment, learned abilities and save data are not edited. The UI badge
is a non-interactive UMG TextBlock attached to the existing field HUD; shipping
builds can suppress PrintString, so debug screen messages are not used.

An unavailable HUD leaves native encounters unchanged and logs the reason with
`[FFR encounters]`. Local executable Lua fixtures cover state restoration,
controller hold/release, keyboard toggles, HUD lifecycle and unavailable contexts.
Native schema/method evidence supports the bindings, but live encounter suppression,
controller recognition and visual placement still need testing in the game.
