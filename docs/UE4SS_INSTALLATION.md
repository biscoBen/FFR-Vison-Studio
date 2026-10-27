# Optional UE4SS installation

Studio asks before building/installing when the selected game lacks the loader
needed by the selected runtime features. **Install UE4SS** installs the bundled
core with the completed mod. **Continue without it** installs the compiled assets
and disables the Studio Lua runtime. Cancel leaves the installation unchanged.
The same prompt applies to **Install the last build**, using that build's runtime
configuration. Installing the loader later and reinstalling the last build enables
the staged runtime without converting its sprites again.

Without UE4SS, overworld replacements/cycling, Crystal Fina's runtime crystal/glow
presentation and movie/music controls, and Eiko's custom esper mastery effects are
unavailable. Native vision kits, MR rewards and challenge acquisition still install.
The installation log lists the skipped features. Deck publishing still requires
the complete requested runtime; an incomplete runtime cannot be published as a
complete snapshot.

The existing ownership transaction installs only `dwmapi.dll`, `ue4ss/UE4SS.dll`,
`ue4ss/UE4SS-settings.ini` and `ue4ss/LICENSE`. It preserves an existing complete
loader, rejects conflicting partial installations, leaves other mods/settings
alone, rolls back failed deployments and removes only unchanged Studio-owned
files on restore. No upstream example mods, keybinds, SDK backends or mod lists are
installed. The official default settings have debug windows and hot reload off
and detect the engine version automatically. The install choice is local to the
selected game folder and does not change saves or cached build inputs.

## Bundled third-party provenance

- Project: [UE4SS](https://github.com/UE4SS-RE/RE-UE4SS), MIT license.
- Version: `3.0.1-1183-gcdbc0b66` (production Windows archive).
- Official source: [UE4SS_v3.0.1-1183-gcdbc0b66.zip](https://github.com/UE4SS-RE/RE-UE4SS/releases/download/experimental-latest/UE4SS_v3.0.1-1183-gcdbc0b66.zip).
- Original archive retained unchanged as `payload/ue4ss_runtime.zip`, including
  `ue4ss/LICENSE`; the license is also installed with the core.
- SHA-256: `e4a47e23e2eeb8379c4fc388d1b1686f01c6c5930d84a2ee4a6a9574b274e681`.
- Downloaded and checked 2026-10-27. The archive is bundled and checked at install
  time; installation does not fetch a moving upstream release.

Automated checks cover bootstrap deployment, rollback, existing-loader preservation,
optional installation and prompt routing. This revision of the loader has not
been tested inside Resonance here. Existing user-tested loader installations are
preserved; a fresh-PC game startup and feature check remain necessary.
