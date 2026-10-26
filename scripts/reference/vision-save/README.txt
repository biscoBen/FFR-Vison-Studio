Vision save ownership check

Close Resonance. There is no need to save again; keep the save from before the
issue. If you want a new save, use a separate slot. Extract this ZIP and run
Collect Vision Save Check.cmd. The default output is Downloads/FFR Mod.
Upload the resulting Vision-Save-Check-....zip in this conversation.

The helper copies Resonance saves from %LOCALAPPDATA%/FFRS/Saved/SaveGames
and, when Studio is found, from the selected game's FFRS/Saved/SaveGames.
It also includes Studio's current units.json when found. It never writes to
the game, save folder, or Studio, and never edits or decrypts a save.
The ZIP contains your game progress and your roster; it is not uploaded
automatically. No tokens, Steam account folders, logs or game archives are copied.

If automatic discovery fails, drag the helper folder into the extracted Studio
test folder, or run in PowerShell with explicit paths:
& '.\Collect Vision Save Check.ps1' -SavePath 'C:\path\to\SaveGames' -StudioPath 'C:\path\to\Sephira-Studio-Test'

Use -SavePath with one save file to collect only that slot. Each save must be
32 MiB or smaller, and the total collection is limited to 64 MiB.
Copies are collected for inspection only. Their format and ownership fields
must be verified before drawing conclusions or changing vision IDs.
