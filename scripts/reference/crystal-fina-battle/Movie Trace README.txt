Crystal Fina movie playback observer - FULL GAME

1. Extract this ZIP outside your game and Studio folders.
2. Run Install Movie Trace.cmd and confirm the FULL Resonance game folder.
3. Restart Resonance. Use Crystal Fina's resonance once, then press F8.
4. Run Collect Movie Trace.cmd and send the ZIP created in Downloads\FFR Mod.
5. After collection, run Disable Movie Trace.cmd; restart to stop the observer.

Keep your current Studio build installed with Test Crystal Fina cinematic ON.
No Studio update, rebuild or install is required for this trace. It does require
one game restart so UE4SS can load the observer. You do not need Cloud or Terra.

Install creates only ue4ss\Mods\FFRStudioMovieTrace\Scripts\main.lua, its ownership
marker and enabled.txt. It does not edit other mods or installed pak files.
The observer records the actual Mana player's status, decoded frame progress,
movie source, alpha-track selection and the cinematic manager's movie-use flag.
It calls read-only getters on the game thread. It never starts/stops movies,
changes visibility or modifies gameplay/save state. Diagnostics go to UE4SS.log.

This is an observer, not a playback fix. An unknown folder with the same name
will not be overwritten. Disable removes only this observer's enabled.txt.
