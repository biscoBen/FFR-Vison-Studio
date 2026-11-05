# Current evasion on character stat pages

Home → **Physical and magical evasion on stat pages** is optional and defaults
to OFF. Enable it, build/install with the existing UE4SS loader and restart the
game. The shared character stat grid gains **Current Physical Evasion** and
**Current Magical Evasion** rows. Equipment comparisons report the current
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
`WBP_UnitParam_Detail` WidgetTree with two passive CommonTextBlocks, retaining its
font style, existing grid, stat enum list, bytecode, bindings and view model.
Unreal constructs and owns every label. There is no raw UWidget construction,
live Slate-struct copying or saved actor/HUD pointer.

The captured mappings already declare this BP. A private mapping copy extends
that exact existing schema with the two object properties, preserving other
schema indices and extensions. The original mappings and capture stay intact.
The compiled asset decodes fully and round-trips through the pinned native SDK;
its readback verifies the original defaults and all existing functions.

Lua refreshes after the real Blueprint view-model/stat notifications. Class-load
notifications attach hooks on the game thread; a one-time widget scan refreshes
an already-initialized first page. No input polling, per-frame scan or delayed
object reference is used. Failed reads hide both rows, avoiding stale or partial
numbers. `FindRow` struct memory is never subjected to UObject flag reads.

Fixture checks cover active-effect stacking, live cap changes, Decoy, raw 500,
float32 rounding, expired/garbage effects, selected-character changes, battle
versus menu sources, missing data/signature guards, initial class loading,
combined runtime controls, settings and checked native staging. These checks
establish code/package behavior. Real-game rendering, page coverage and buff
refresh remain unverified until gameplay feedback is available.
