Crystal Fina movie playback diagnostics - FULL GAME

1. Extract this ZIP to a folder outside the game and Studio engine.
2. After the failed movie test, double-click Collect Fina Movie Diagnostics.cmd.
3. Select your Studio folder if prompted, then confirm the FULL Resonance folder.
4. Send back the Fina-Movie-Diagnostics-...zip created in Downloads\FFR Mod.

No need to own Cloud or Terra, unlock an original vision, rebuild/install,
or enable any additional testing switch. This tool does not start or change
the game. It does not update or publish the revised cinematic.

Collected: hashes of Studio's installed/build companion pak and utoc;
metadata for its ucas; Fina's generated movie descriptors and timeline;
original Cloud movie descriptors already extracted by Studio; the local
cinematic manifest/spec; testing switches; recent FFRS and UE4SS logs;
and movie-related options only from GameUserSettings.ini.

It uses Studio's bundled repak.exe to read at most 2 MiB each from the installed
Fina USM and an original Cloud VP9 USM. Version 2 checks loose Content/Movies
files first, then discovers the original entry in the top-level game paks. Samples
are explicitly marked as prefixes if truncated; they are for format checks,
not standalone movie playback. No whole game archives are exported.

Version 2 also compares movie/decryption options in the installed game and
Studio's cached game settings. Only boolean/numeric movie options and whether
a decryption key is configured are recorded. The key itself and the full INI
files are never copied. Failed original-movie lookups are listed in the report.

Save files, memory dumps, account credentials, unrelated mods and full Studio
configuration are not collected. Paths and recent logs are included. Every
read failure is recorded; send the resulting ZIP even if some items are missing.

Optional command line (PowerShell):
& '.\Collect Fina Movie Diagnostics.ps1' -GamePath 'G:\Steam\steamapps\common\FINAL FANTASY RESONANCE' -EnginePath 'C:\path\Sephira-Studio-Test' -NoPrompt
