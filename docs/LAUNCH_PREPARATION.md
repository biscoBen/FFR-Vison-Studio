# Launch preparation and local snapshots

Open **Home → Launch preparation & snapshots**. Studio saves pending edits before opening the page.
The normal installation buttons and individual testing switches remain on Home. No GitHub repository or token
is needed for any workflow below. Nothing here uploads personal configurations.

## PC → Steam Deck, without building on the Deck

1. Finish your setup on the PC. Use **Build for Deck snapshot** or build/install normally and wait for success.
2. Open **Export / import snapshots**, then **Export Deck snapshot**. Keep Studio open until the ZIP is ready.
   The browser streams **Resonance-Mod-Snapshot.zip** to your downloads; large mods are not held in a browser Blob.
3. Copy that ZIP to the Deck using your preferred file transfer or removable drive. Extract the whole ZIP together.
4. Close Resonance. In Desktop Mode, run `bash "Install snapshot.sh"` from the extracted folder. It detects Steam
   libraries (including SD-card libraries) or asks for the game folder when more than one installation is found.
   Use `--game "/path/to/game"` to select one explicitly. The installer uses the Deck's Python 3 standard library;
   it needs no Studio, engine download, GitHub, token or asset build.
5. If the snapshot includes the runtime for Crystal Fina or character cycling, set the game's Steam launch option:

   `WINEDLLOVERRIDES="dwmapi=n,b" %command%`

Repeat export/copy/import whenever you change your PC setup. Both computers must have the same native game build.
The installer compares all top-level native container names/sizes and every `.utoc` SHA-256, in addition to the main
container hash. It excludes `~mods` from game identity. Existing unrelated mods remain outside its owned file set.

A successful import creates **Update my Resonance mod** in the Deck's Desktop/applications menu. Its local menu can
import the next `mod.zip` (inside another exported snapshot folder) or restore files from before importing. Previous
mod files are backed up; later snapshots also remove runtime files no longer needed. An interrupted installation
has a recovery journal. Changed externally owned files and conflicting runtime loaders stop the update.

The ZIP contains only the three compiled mod files and required owned runtime/loader files, plus the installer and
instructions. It contains no game files, saves, editable roster, machine paths or credentials. These are finished
mod snapshots: copying the Studio configuration alone would still require a Deck-side build.
Optional private GitHub publishing remains under a collapsed **Optional GitHub publishing** section for existing
users; normal builds, snapshots and local imports never publish.

## Back up or restore the editable Studio setup

**Export Studio backup** saves the entire recorded roster and the known icon-layout, ability-mode, Sephira-visual
and testing settings. That includes unit recipes, exact skill/passive IDs, MR rewards, appearance selections,
acquisition/cave choices, edits and disabled presets. It is separate from the finished Deck snapshot.

Select the ZIP under **Restore a Studio backup**. The page previews its units/files. **Restore previewed backup**
replaces the saved roster/settings, makes an automatic backup first and invalidates the previous build/export.
If settings changed after preview, preview again. Automatic backups can be downloaded in the page and restored
through the same preview flow. Studio polls the revision and reloads the restored setup when no unsaved edits exist. Stale desktop saves are
rejected after a restore/preset. If you had unsaved edits, **Reload restored setup** backs up those edits locally
before loading the restored roster; autosave cannot silently overwrite it.

Machine game paths, credential stores, native preparation, source sprite downloads and game saves are not restored.
Custom source artwork must remain available to the engine; the backup retains its selection/recipe rather than
bundling every source pack. Use the finished Deck snapshot to transfer the actual compiled artwork without a build.
The existing **Your game files** restore control continues to handle installed PC mod backups.

## Prepare and identify a new game build

The page displays the actual native-container fingerprint and whether prepared data matches it. The captured demo
identity comes from the user's original native reference. Other builds say **Unreviewed game build**; a folder name
or successful extraction does not mark the full game compatible.

An older Studio setup can need one initial preparation because no game-data baseline was recorded. That prompt
does not by itself mean Steam updated the game. Studio separately identifies a changed native-container fingerprint
and an interrupted preparation. Once recorded successfully, the same native build can be reused across Studio
updates; updating Studio alone does not require another preparation.

Choose the new game folder and **Prepare selected game**. When the fingerprint changes, old `extracted/` and
`build/` directories move to `engine/launch-prep/prepared-backups/<id>/`; saved units/settings stay in place.
Preparation uses an isolated view of official containers, rebuilds rows/inventory/catalog and avoids the shipped
demo catalog/listing/layout cache. The pinned mappings/enums remain helpers; changed full-game schemas may still
require an updated, verified engine. A failed preparation leaves the new build unprepared and preserves old data.

Builds with imported sprites do not need a donor menu-layout dump. Native sprite clones read the current native
layout data asset directly. The builder no longer requires a leftover file under `build/visions_mod/check/da/`.

Build/install refuses different or untracked prepared data. A verified build records its game and input fingerprint;
**Install last build** and snapshot export reject later game/settings changes. Native filenames can be found across
Steam libraries without assuming the full game's display name or app ID; explicitly selected paths take precedence.

On an unreviewed build, listed enabled patches require either the original-game preset or an explicit review on this
page. Review is remembered only for that game fingerprint; it is the user's choice to test, not proof of compatibility.
The source-specific guards inside individual repairs remain in effect.

## Original-game test preset

**Back up & apply original-game preset** turns off library changes, native repairs, borrowed Sephira visuals, FFBE
Needles import, practice/MR/survival controls, walking cycling, retired cave switches and original-vision test grants.
It keeps the roster and edited kits, MP/power changes and explicit custom presentations. All controls remain available
individually on Home. Rebuild/install after applying it. Remove the mod for a completely unmodified game comparison.
Restore its automatic Studio backup to return to your former switch/grant selections.

## Native comparison and test sheet

**Collect current game reference** reads fresh official containers, excluding all installed mods. It gathers the
scoped skill/unit/MR/asset/sound-reference tables, battle/skill timeline packages and complete native asset inventory.
It decodes tables with the installed reader/mappings and records schema/row hashes, exact IDs, primary/offset/pointer/
character-specific sequence links, sequence/sound asset presence and timeline-byte hashes. Original rows and packages
are kept in the local reference ZIP. Containers may need a temporary copy if a hard link is unavailable.

The packaged demo comparison metadata comes from the previously supplied October 16 native reference: 90 scoped
tables, 1,167 skill records, 28,688 inventory paths and 2,836 timeline files. It contains metadata/hashes, not another
copy of the source artwork. The report identifies added/removed/changed records and assets. Localized labels alone
do not count as a route change. **Download latest reference** provides the evidence plus `reference.json` and
`comparison.json`. You can also compare a separately collected `reference.json` on this page.

The editable test sheet carries all 19 named original-enemy failures (20 candidate IDs because Waterga's cast variant
is unresolved), two separate imported-vision failures and regression tasks for Fina, knockout/revival, MR/default
skills, acquisition, direction, practice, survival and Deck transfer. Visuals, direction, sound and hit timing are
recorded independently. Each fingerprint has its own results; previous demo observations never become full-game passes.
Export CSV to keep a readable copy. Asset/route presence and successful conversion do not establish live gameplay.

Live full-game behavior and Steam Deck/Proton rendering/controller use require testing on those systems.
