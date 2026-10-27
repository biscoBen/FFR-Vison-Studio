# Sephira runtime reward and presentation review

Full-game reference: `8ce7a0746d0cc1b2`, collected 2026-10-22. This is a structural/native serialization audit; it does not certify the final appearance of every skill in a running game.

## Current revision 7

All 75 individual equipable MR rewards from the 15 excluded originals are MR rewards: 50 passives and 25 active skills. The 150 odd-rank slots contain 124 passive grants and 26 active grants (including Minfilia’s Libra). Each odd rank has one learned ability. 130 of 131 original passives remain after the approved Rikku Pharmacology replacement, with 186 awakening passive grants. The Libra swaps remove one passive each from Minfilia and Barusa and add one each to Primm and Trance Terra. All passive AP budgets remain within 20%. [The MR allocation](SEPHIRA_PASSIVE_MASTERY.md), [restoration details](SEPHIRA_MR_RESTORATION.md) and [awakening balance report](SEPHIRA_AWAKENING_BALANCE.md) list the choices and migration. Native writing/readback also verifies that all 25 MR actives retain their complete stock rows, including costs, mechanics and command membership.

39 neutral-source custom elemental attacks now use private native hit-particle rows at their original reaction times. The cosmetic rows add no damage events, sounds, hit slowdown or screen flash. Original motion/sound tracks and critical, weakness, additional, miss and death settings are retained. Three sources whose original reaction uses the default sentinel receive a private generic hit-feedback row. The standard native hit system supplies the actual recipient and body position. Borrowed elemental spell presentations retain their existing effects; stock neutral substitutes use the recovered original attack and its authored impact. Explicit user visual overrides remain authoritative.

All 39 inherited icon mismatches are corrected to the actual damage element. Every added vision gets its own command and Spirit icon tag/brush, including entries beyond the old 16-slot limit. No original command icon is overwritten, and the icon does not depend on Rain or Lasswell.

Native writing/readback passes for all 30 kits, 314 private definitions, 26 private passive identities, 312 original player routes, all 39 impacts and all 30 command/master icon pairs. The separate 131-passive coverage and saved-roster migration checks pass. These establish table and routing correctness; appearance in a running game still needs playtesting.

The earlier review below records the revision-5 fixes, which remain available for unmigrated saved profiles.

## Coverage and corrections

- All 30 presets, all four awakening tiers and MR0–9 were reviewed. The audit resolves 526 original active-skill sources; 523 have direct sequence bindings. Including the original player variants and their canonical aliases, 1,728 distinct timeline packages were inspected.
- 47 private passives previously used large allocated vision-derived IDs. Reserve stable IDs inside the native passive range instead, without changing their effects, equip costs, original donors or permanent stat budgets. This covers the reported Fina, Christine, Folka and Minfilia blanks, including Minfilia's awakening passive.
- 15 private learned MR abilities now use the general learned command. The original vision command restriction prevented those rewards from appearing in character ability lists. This includes Crystal Renewal, Tidal Invocation and Waterga Surge. Saved recipes retain their editable data; normalization is applied during building.
- Give private pure HP healing copies field-recovery metadata, preserving explicit user availability overrides. Both Crystal Renewal variants can include the caster. Damage, healing strength, MP costs, hit counts and target grouping remain unchanged.
- Copy 312 usable original source presentations to private player routes, including their original sound tracks. Prefer 190 complete native player variants from the same original sequence family. Restore 81 audited motion tracks and resolve embedded impact aliases. Keep native/global rows and the existing enemy routes. Preserve working player effects such as Aqua Breath; adapt only the audited enemy/party group points when an enemy timeline is transplanted or the recipe changes its target relationship. These repairs run even with borrowed visuals and library repairs off. Changed original bytes stop preparation before sprites are converted.
- Imported models expose the native motion names requested by their skills using their own FFBE clips. The 30 model manifests request 151 aliases in total. Their effects and sounds still come from each original skill; existing explicitly supplied clips take precedence.
- Read back every selected vision's awakening/MR tables, ability names, passive ID ranges and custom command/field-availability fields immediately after table writing, before sprite conversion.

## Original sources still needing individual review

These three original presentations remain flagged; no different skill's animation is substituted for them.

| Vision | Ability | Original source | Finding |
| --- | --- | --- | --- |
| Trance Terra | Trance Apocalypse | 505540 | The original timeline's event functions cannot all be decoded; no enabled particle spawn was resolved. Keep its original behavior and flag it. |
| Minfilia | Dual Jobs | 445210 | Original timeline copied; no enabled Niagara spawn. It contains a SpriteStudio actor event, so a live check is needed before treating this as missing visual content. |
| Relm | Forbidden Ars Magna | 503930 | Original timeline copied; its only particle spawn is disabled. Requires an individual review of that original presentation. |

### Approved FFBE Blood Recovery test

The collected FFR source (501530) has no sequence binding. The user selected the FFBE ability with the same name,
**Scartio's Blood Recovery (231688)**, after reviewing its source. It is now assigned only to Snow White's private
copy, independently of borrowed visuals. Other original skills and explicit user presentation edits are retained.
The original FFBE front/back healing layers begin at frame 40, the red flash and single native healing reaction at
frame 100, and both recorded source sound events at frame 41. Actors are cleaned up after their source layers end.
Healing strength, MP cost and target grouping remain Snow White's existing settings; FFBE's regeneration mechanics
are not imported. The skill uses the caster's existing magic animation.

The selected 9.6 MB payload contains three separate converted projects and one original HCA recording. All 3,037
source sprite frames are retained with no cropping/dropping; mesh texture cells are resampled to 128 pixels while
retaining world sizes. Native SS6, texture, audio and compiled-event writing/readback pass. Front/back depth offsets,
source screen flash adapted to the caster, apparent size and final rendering still need a live test. The full optional
animation library remains downloaded separately; this import does not require it on the user's PC.

Native Cover (Mog, 400760) and Mimic (Relm, 400330) also have no ordinary direct sequence bindings. They use specialized mechanics and are kept as native skills. Generic physical/support presentations can legitimately have no Niagara particle; absence of a particle is not by itself a failed skill.

## Fina runtime evidence

Returned full-game diagnostics `Fina-Runtime-Diagnostics-20261022-173111-e46c95.zip` select the full game and the desktop Studio engine. The installed runtime and its per-game ownership record are present. The log shows the crystal attaching to FinaNative13500 twice; it later reports a Lua callback-registry error. This does not prove the exact visibility failure.

The runtime now restores both component visibility flags after native battle hiding, keeps the queued callback reachable, and retries a removed component or transient actor transition per instance. An individual failure cannot permanently disable every later Fina. Accepted glass/refraction, size, spin, attack speed and resonance timing are preserved. Executable Lua fixtures cover hiding, component removal, transient failure, reattachment and normal cleanup; live confirmation is still required for the boss and the vision.

## Per-preset inventory

Counts include every awakening and MR tier. Each private passive and each learned private MR active is covered by the shared correction rather than a preset-specific patch.

| Vision | Granted active skills | Private active copies | Native motion aliases |
| --- | ---: | ---: | ---: |
| A2 | 19 | 14 | 6 |
| Christine | 16 | 10 | 3 |
| Crystal Fina | 20 | 9 | 3 |
| Barusa | 16 | 7 | 7 |
| Blue Sky Belle Fran | 17 | 9 | 3 |
| Oracle Maiden Lunafreya | 17 | 9 | 4 |
| Minfilia | 16 | 9 | 3 |
| Folka | 19 | 13 | 3 |
| Fryevia | 17 | 13 | 5 |
| Lenneth | 19 | 12 | 7 |
| Lila | 16 | 8 | 5 |
| Mystea | 15 | 10 | 4 |
| Reberta (JP) | 18 | 9 | 5 |
| Snow White | 19 | 12 | 6 |
| Aria | 20 | 14 | 4 |
| Eiko | 17 | 10 | 3 |
| Alice/Half Nightmare | 17 | 14 | 10 |
| Moogle of Narshe Mog | 16 | 8 | 3 |
| Lilith | 16 | 9 | 11 |
| Dragon Knight Freya | 18 | 13 | 5 |
| Trance Terra | 17 | 5 | 7 |
| Charming Kitty Ariana | 18 | 12 | 3 |
| Aerith | 17 | 11 | 5 |
| Jade | 18 | 10 | 6 |
| Spirited Heart Primm | 18 | 10 | 4 |
| Relm | 19 | 14 | 3 |
| Rikku (FFX-2) | 20 | 11 | 7 |
| Nalu | 18 | 10 | 4 |
| Elza | 18 | 9 | 8 |
| Lunera | 17 | 10 | 4 |

## Validation

Focused Python and executable Lua/PowerShell fixture checks cover the reported failures and all presets. The pinned native tools write and read back all 30 visions' reward/ability tables, copy 1,264 original timeline packages, apply 339 private object edits and 1,303 bytecode edits, and reparse their exports. A native negative check deliberately restores Folka's vision-only command restriction and blanks a private Fina passive name; both must stop the early readback check. Windows validation and package provenance are recorded in the release notes after the build completes.
