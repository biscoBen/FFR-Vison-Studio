# FFR Vision Studio (Windows app)

The native front of the studio: a Flutter desktop app that downloads and supervises the Python/.NET engine
(`FFR Vision Studio Engine.exe`, fetched from the project's host on first start) and drives its Easy mode natively.
This repository is the app on its own: it needs nothing else on disk to build, and at runtime it talks only to the
engine over localhost and to the host over HTTPS. Design: `DESIGN.md` and `lib/design/DIRECTION.md`. The engine's
source, the pack builder and the project notes live in a separate project repository, which is not published yet.

## Build

```
flutter pub get
flutter analyze
flutter test
flutter build windows --release            # defaults to version 1.0.0, build 15
```

A build talks to the live host, which can require a minimum app version in its manifest. This branch defaults to build 15
in both the executable metadata and the app's version check. To use another compatible build number:

```
flutter build windows --release --build-name 1.0.0 --build-number <n> \
  --dart-define=APP_VERSION=1.0.0 --dart-define=APP_BUILD=<n>
```

`.github/workflows/windows.yml` on this fork's development branch runs analyze, test and the Windows build on pushes to
`Sephira's-Update`, `main`, and `master`, as well as pull requests. It attaches the Release folder as the
`FFR-Vision-Studio-windows` artifact. Automatic builds default to build 15 and check the host's minimum-version requirement
when its manifest is reachable. A blocked or unavailable updater host does not prevent compilation; the app still checks
compatibility at startup.
A manual run ("Run workflow") can supply a different compatible build number.
If GitHub Actions is disabled on the fork, enable it from the repository's Actions page first. The zips people
download are assembled by the packaging run in the project repository, which passes the same flags and ships the
exe next to the engine and the data packs.

## Cloud builds

Windows users can install the separate test copy from a `Sephira-Studio-Test.zip` package. Extract it and run
`Start Studio Test.cmd` once; it creates a **Sephira Studio Test** desktop shortcut. Opening the shortcut checks for
the latest validated `Sephira's-Update` prerelease, verifies its SHA256 digest, and launches it. Settings and units
remain in `Studio Test Data` beside the launcher. Failed/offline updates retain the installed app. Close the test app
before reopening the shortcut to check again. Use a copied game folder to keep installed test mods separate too.

Successful builds on this development branch automatically publish those test packages. The test app uses its own
shortcut for frontend updates and continues to fetch engine/data packs from the original host. It does not offer the
original project's frontend updater. The release label remains build 15; the shortcut identifies updates by their
workflow run and commit. These packages are prereleases and do not replace the fork's stable release or change master.

From this checkout, use the helper to build the development branch and download the resulting Windows app:

```
python3 scripts/cloud_windows_build.py
```

Enable repository Actions from its Actions page first. The helper can also do this with `--enable-actions` if its credential
has Administration permission.
The helper defaults to `Sephira's-Update` and build 15, checks the remote commit, waits for its workflow run, and downloads
only that run's `FFR-Vision-Studio-windows` artifact. It writes a provenance record alongside the executable under
`/workspace/.runtime/ffr/builds`. Commit and push changes before building them.

If the cloud proxy blocks GitHub's artifact storage, use `python3 scripts/cloud_windows_build.py --cloud-download`
on the development branch. The workflow creates a temporary **unpublished draft** download through GitHub's release-asset
endpoint. The helper verifies its branch, commit, run and SHA256 digest, downloads it, and deletes the draft. This requires
Contents read/write in addition to Actions access. Normal push builds do not create temporary drafts; successful
development-branch builds publish the separate test prerelease described above.

The platform's GitHub integration may allow code pushes while denying Actions administration. In that case, supply a
fine-grained GitHub token securely as `FFR_GITHUB_ACTIONS_TOKEN` in the cloud environment's secret settings, scoped only
to `biscoBen/FFR-Vison-Studio`. It needs **Actions: read and write** to enable workflows, request builds, watch runs, and
download artifacts; **Contents: read** to verify the selected commit; and **Administration: read and write** for the
one-time repository Actions activation. Administration permission can be removed after activation.
The helper uses the existing injected GitHub authentication when this additional binding is absent. Never put token
values in the repository or chat.

Use `--ref master` to download a separate baseline build without changing or merging `master`.
Run the downloaded executable through the prepared Wine runtime with separate scratch application data.
Full mod tests still need the game's installation and extracted data.

## Saved character configurations

Open a vision and use **Save character config** at the bottom left to save a `.vision.json` file. It contains the full
character spec: abilities and passives by tier, custom moves, stats, resistances, roles, Resonance mechanics and animation
settings, and advanced fields. Studio suggests its persistent `Character Configs` folder, or you can choose another folder.

Use **Load character config** from a character page or **Your visions**. A removed character is restored directly;
an existing matching character requires confirmation before replacing its setup. An unrelated selected character is
never overwritten. Studio keeps a full roster backup under `config-backups` before loading and allocates free IDs and
internal table row names when necessary. Re-added characters keep their current ID whenever it is available.

These files save configuration, not artwork. Removing a vision keeps its cached artwork, and Crystal Fina's bundled
artwork is repaired automatically. On another installation, first add/import the character to obtain its artwork,
then load the saved file. Build or install the mod afterward to apply the restored setup to the game.

## Layout

- `lib/main.dart` window, single-instance lock, header, engine-down banner
- `lib/state/app_state.dart` boot (downloads, offline start, update notice), engine supervision, units, build, restore
- `lib/services/` engine process, downloader (resume + checksum), engine API client, game folder detection, paths
- `lib/design/` the guide's tokens (`Guide`, day and night editions), parts, wordmark, motion viewer, choice
- `lib/screens/` setup, home (spread), unit page and its four steps, add-unit, copy-a-vision, about, build status
- `windows/runner/Runner.rc` exe metadata; `windows/runner/resources/app_icon.ico` Rain's face

## Developing without touching your real install

Start the built exe with `LOCALAPPDATA` pointed at a scratch folder: the app keeps everything (engine, packs, units, logs)
under `<LOCALAPPDATA>\FFR Vision Studio`. `FFR_STUDIO_HOST` points it at another host tree (a local copy served on
127.0.0.1, for instance); it defaults to the live host, which is all a developer build needs.

To compare `Sephira's-Update` with a clean `master` build, keep the executables in separate folders and give each its own
scratch `LOCALAPPDATA` directory. This separates settings, engine files, and units. On Linux, run the Windows build
through Wine or Proton; compiling the Windows executable still requires Windows. Keep `master` unchanged when testing
the development branch.

## Files

`CHANGELOG.md` (by build), `LICENSE` (MIT for the code; the game's art and data are Square Enix's and excluded),
`CONTRIBUTING.md`, `.github/workflows/windows.yml` (analyze, test, build, artifact on every push).
