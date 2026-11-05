# Current evasion on character stat pages

Home → **Physical and magical evasion on stat pages** is optional and defaults
to OFF. Enable it, build/install with the existing UE4SS loader and restart the
game. The shared character stat grid gains **Phys. Eva** and **Mag. Eva** rows,
with percentages in a separate right-aligned column. Equipment comparisons report the current
loadout, not an unverified prediction for a hovered item.

The page's own `CPP_VM_UnitParam.UnitParam` supplies the selected character.
`CPP_VM_BtlUnitParam` uses its `BtlUnitParam` instead; an invalid battle reference
never falls back to a menu snapshot. Only friendly characters are shown. Current
equipment, applicable MR/passive rewards and temporary buffs follow the game's
live `GetContEffectList()`, rather than a separate learned-skill or description
sum. Native effect-list membership controls application and expiration.

These are evasion components. An attack's accuracy, its damage rules and effects
that guarantee hits can change the outcome; a stat row cannot predict every
incoming attack. No gameplay calculation, item, skill, passive or save is changed.

## Native evidence

The returned lookup capture is
`Evasion-Lookup-Reference-20261104-174123-e633d3-001.zip`, **16,568,977 bytes**,
SHA-256 `4b38f2d4e1105446d386ca7e540c10611e3711e746dd5b08719c65782c2d7cce`.
All restored payload sizes and hashes verify. It supplies the missing read-only
`.data1` section and contiguous code, including gaps between compiler exception
records. No file from the capture is executed.

The source `FFRS-Win64-Shipping.exe` is **495,708,416 bytes**, SHA-256
`b8c588e46ebadbe37feca7bdf2da0ae63a8538099d14a53ec0c2241b086e5ffa`.
Addresses below are RVAs in that image and are evidence only: the runtime uses
reflected methods/properties, not these addresses or private memory offsets.

| Evidence | Verified behavior |
| --- | --- |
| Hit routine `0x05233ac0`, arguments RDX/source and R8/target saved as R12/R15 | The aggregation at `0x05233dca`–`0x05233e73` reads the **target** effect list at `+0xb8`. Attacker accuracy is handled separately. |
| `UCPP_ContFxAvoidance` registration → helper `0x04dc2450` → vtable `0x08691bf0` → slot `+0x4a8` | Getter `0x05111a90` reads `ParamList[1]` as a byte selector (0 both, 1 physical, 2 magical), returns `ParamList[0]` for a match and zero otherwise. A missing parameter defaults to -1. It does not inspect a separate lifetime, probability or conditional flag. |
| Target loop at `0x05233e20` | Skip null/garbage objects, add integer contributions using float32, apply `min(live evasionLimit, sum)` and truncate toward zero. Raw 500 bonuses use this same limit. |
| Native live table type `0x13`, calculation row `+0x144` | Read the installed `UNIT_PARAMETER_CALC_DATA.evasionLimit`; the captured official value is 75. Runtime lookup uses `CPP_InputManager:GetDataTable(19)` and the native row name. It does not bake 75 into the readout. Unsupported/unavailable data hides both rows. |
| Earlier target loop, slot `+0x4b0`; `CPP_ContFxDecoy` override `0x0514ed70` | Returns true for physical type 1, causing avoidance before the ordinary capped roll. Represent an active Decoy as physical 100%; it does not override magical evasion. Ordinary Avoidance retains the base implementation at this slot, so raw 500 is not this bypass. |
| Remaining hit calculation `0x05233e76` onward | Uses skill accuracy, attacker modifiers and other attack-specific handling. The displayed evasion component is not advertised as final dodge chance. |

## UI and lifecycle

`scripts/build_evasion_ui.py` extends the captured native
`WBP_UnitParam_Detail` WidgetTree with two passive label/value rows. Labels use
the captured `BP_SystemTextStyle`; percentages use the native
`BP_SystemTextStyle_PramNUM`, the ordinary white color and right alignment.
Retain the existing grid, stat enum list, bytecode, bindings and view model.
Version 1.2.163 adds the user-approved white winged-dodge and crescent-ward
icons as private 128px BGRA8 UI textures. Each occupies the native 32-unit icon
column, followed by the captured four-unit gap; labels and percentages then
share the native text/number columns. Images hide with unavailable values.
The approved artwork and prepared texture inputs are kept in
`scripts/fixtures/evasion_icons`; the generator emits each private texture
alongside the widget JSON. It replaces no official icon or texture.
Version 1.2.165 inserts **Phys. Eva.** after physical defence and **Mag. Eva.**
after magical defence in the single-column stat page. The passive rows share
the native overlay while native entries keep their own grid/bindings. Native
desired height plus live grid padding sets row pitch. Presentation offsets are
absolute, not accumulated; a game-owned spacer reserves the additional height
and the inner grid inherits the expanded clipping bounds. The existing gap
before Attributes drops from 60 to 24 Slate units, moving that section up while
leaving Role in place. No new reflected Blueprint fields or gameplay parameters.
Multi-column shared comparison pages keep their native positions and a readout
below; failed reads clear added gaps/offsets. Both owning widgets are serialized
against their original schemas, including the embedded ten-byte stat instance.
Relocate both opaque platform-data FNames (pixel-format marker and final None)
against each private texture's name table. Ordinary UAssetAPI roundtrip alone
does not decode those Extras references; inspect the compiled stream explicitly.
The 1.2.163 in-game crash exposed another omission: the four-byte mip header
is a UE5.6 **data-resource index**, not a classic inline bulk header. Version
1.2.164 supplies one native resource-table entry with index zero, 65,536-byte
inline payload and export-relative offset 101 (17 property bytes + 84 header
bytes). Keeping the old index 352 without its table makes the native reader
interpret transparent pixels as zero-sized bulk metadata, consuming 141 bytes
instead of the export's 65,661. `verify_evasion_texture.py` follows the
independent bulk-header lookup/fallback contract, reproduces that exact mismatch
and validates the complete mip read and deferred payload offset. A real UE5.6
mod-container conversion/reverse extraction supplements the opaque JSON check.
Source: [CUE4Parse bulk-header reader](https://github.com/FabianFG/CUE4Parse/blob/f7303f56da41b9bc43b983e48ecc4644a684c310/CUE4Parse/UE4/Assets/Objects/FByteBulkDataHeader.cs).
Unreal constructs and owns every label. There is no raw UWidget construction,
live Slate-struct copying or saved actor/HUD pointer.

Keep this shared Blueprint's **original six reflected fields** and original
mappings exactly. The four labels/values are normal WidgetTree children; Lua
finds them through `UserWidget.WidgetTree.RootWidget` and native panel getters.
No new BP properties are needed. The compiled class-default stream remains
byte-for-byte identical to the original (110 bytes), with existing functions
and bindings preserved.

The 1.2.160/1.2.161 styling added four reflected fields. That shifted inherited
unversioned property indices for embedded instances in other native packages.
The reported status-detail page saves index 31 as `Slot` under the original
schema, but the altered schema reads `TickFrequency`, a one-byte enum, instead
of a four-byte reference. Its 10-byte stream is consumed as seven bytes,
matching the fatal error. A self-consistent standalone readback with altered
mappings did not test this compatibility. Version **1.2.162** removes the schema
expansion and tests the actual captured parent header and inherited schemas.

Lua refreshes after the real Blueprint view-model/stat notifications. Class-load
notifications attach hooks on the game thread; a one-time widget scan refreshes
an already-initialized first page. No input polling, per-frame scan or delayed
object reference is used. Failed reads hide both rows, avoiding stale or partial
numbers. `FindRow` struct memory is never subjected to UObject flag reads.

Fixture checks cover active-effect stacking, live cap changes, Decoy, raw 500,
float32 rounding, expired/garbage effects, selected-character changes, battle
versus menu sources, missing data/signature guards, initial class loading,
combined runtime controls, settings and checked native staging. These checks
establish code/package behavior. The user confirmed values appearing in 1.2.159
and supplied a screenshot showing 25% physical and 35% magical evasion, with
overflowing labels. Version 1.2.160 shortens the labels and uses native label and
numeric styles in separate columns. The revised layout, broader page coverage
and buff refresh still require gameplay confirmation. The combined 1.2.161
update retains this styling and also corrects the controller map's area fit.
The subsequent serial-size crash is addressed by the schema-preserving 1.2.162
layout. The next user screenshot confirms the stat page opens and values appear;
1.2.163 adds the requested icons and horizontal alignment, but its texture bulk
table omission causes the newly reported crash. Candidate 1.2.164 corrects that
metadata without changing the approved pixels or row layout. In-game opening,
icon appearance and broader buff/page coverage remain pending.
