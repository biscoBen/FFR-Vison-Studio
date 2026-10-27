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

## Disable random encounters

This separate testing toggle requires a normal rebuild/install and game
restart. It clears only `doMovementEncount` on maps where that native flag was
true, in the selected game's region/shared/production tables and cooked map
composites. It preserves encounter group IDs, distance thresholds, story
conditions, startup events, boss events and Sephira challenge definitions.

Turning it off and rebuilding emits no encounter edits, restoring the original
walking-encounter settings. No save or UE4SS runtime patch is used. A missing
or changed native flag fails before installing a silently incomplete recipe.
Live travel and scripted-fight checks are still required.
