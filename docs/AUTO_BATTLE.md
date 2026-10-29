# Remembered-command auto-battle

Enable **In-game auto-battle** in Studio, rebuild/install and restart Resonance.
Install UE4SS when offered if it is missing. In battle, press **F9** or hold both
controller triggers **LT+RT / L2+R2 for one second**. Release before another hold.
The play indicator beside the battle-speed guide shows ON/OFF. Until that guide
finishes layout, its fallback position is at the bottom-right of the screen. It starts OFF
when you launch the game; switching during play uses no equipment slot or rebuild.

Use a command manually to update that character's remembered selection. Auto
repeats those selections in later ordinary turns and battles, including multicasts
and all-target mode learned during the session. Initial selections also come from
the game's saved command memory. Enemy target IDs are selected afresh; friendly
preferences follow party members when their battle IDs change. The native game
still validates abilities, MP, inventory, legal targets and action execution.

If a remembered command is unavailable or lacks a valid target, auto pauses with
an on-screen reason. Choose another action manually and toggle on again. Manual
input also takes over from an in-progress automatic selection. Events, cutscenes,
pause screens, guests and extra battle phases stay under native control.

The implementation uses the captured native command stack and public view-model
methods. It does not toggle the game's separate native auto option, overwrite
saves, supply free MP/items, or submit fabricated battle jobs. The runtime logs
state changes and unsupported bindings with `[FFR auto battle]` in UE4SS.log.
Offline fixtures exercise the protocol; actual replay timing, compound commands,
controller use and placement still require game testing.

The 1.2.126 correction uses native `CanActivateAction` for availability.
`GetCommands` returns already-selected stack data, not the current menu. Manual
decision capture remains active when the game closes command input during commit.
