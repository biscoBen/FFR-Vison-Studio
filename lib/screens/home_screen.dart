import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';
import '../services/sephira_visions.dart';
import 'add_unit_dialog.dart';
import 'build_status.dart';
import 'deck_sync_panel.dart';
import 'character_config_buttons.dart';
import 'native_vision_dialog.dart';
import 'native_portrait.dart';
import 'party_portrait.dart';
import 'remove_unit_dialog.dart';
import 'runtime_install_dialog.dart';

/// Left page: your visions as guide entries. Right page: install.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});
  Future<void> _chooseShopVisions(BuildContext context, AppState app) async {
    final presets = app.sephiraPresets;
    final selected = (app.sephiraShopSelection ?? presets.map((p) => p['id'] as String).toList()).toSet();
    final saved = await showDialog<bool>(context: context, builder: (context) => StatefulBuilder(
      builder: (context, update) => AlertDialog(
        title: const Text('Visions in the 1-gil shop'),
        content: SizedBox(width: 420, height: 460, child: Column(children: [
          const Text('Unselected visions keep their normal acquisition locations.'),
          Row(children: [
            TextButton(onPressed: () => update(() => selected.addAll(presets.map((p) => p['id'] as String))), child: const Text('All')),
            TextButton(onPressed: () => update(selected.clear), child: const Text('None')),
          ]),
          Expanded(child: ListView(children: [for (final p in presets) CheckboxListTile(
            title: Text(p['name'] as String), value: selected.contains(p['id']),
            onChanged: (value) => update(() { if (value == true) { selected.add(p['id'] as String); } else { selected.remove(p['id']); } }),
          )])),
        ])),
        actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Save'))],
      ),
    ));
    if (saved == true) {
      try { await app.setSephiraShopSelection(selected.length == presets.length ? null : (selected.toList()..sort())); }
      catch (e) { app.showNotice('$e'); }
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final busy = app.building || app.deckWorking || app.minimapWorking;
    final canBuild = app.includedUnitCount > 0 || app.modInstalled || app.testingMaxMr || app.testingPracticeBattle || app.fieldLeader || app.ffbeNeedles || app.surviveAtOne || app.noEncounters;
    final editedNativeIds = app.units.where((u) => u['native'] != null).map((u) => u['id']).toSet();
    final added = app.units.where((u) => !SephiraVisions.member(u as Map) && u['party'] == null && (u['native'] == null || u['testAcquire'] == true)).cast<Map<String, dynamic>>().toList();
    final defaults = [...app.units.where((u) => u['native'] != null && u['testAcquire'] != true), ...app.nativeVisions.where((u) => !editedNativeIds.contains(u['id']))].cast<Map<String, dynamic>>();
    final editedPartyIds = app.units.where((u) => u['party'] != null).map((u) => u['id']).toSet();
    final party = [...app.units.where((u) => u['party'] != null), ...app.partyCharacters.where((u) => !editedPartyIds.contains(u['id']))].cast<Map<String, dynamic>>();
    return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Expanded(
        flex: 7,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Expanded(
            child: _visionBox(context, app, added, title: 'Added visions', key: const Key('added-visions'), allowAdd: true),
          ),
          const SizedBox(height: 12),
          if (app.sephiraUnits.isEmpty)
            SizedBox(height: 154, child: _visionBox(context, app, app.sephiraUnits, title: "Sephira's Visions", key: const Key('sephira-visions'), isSephira: true))
          else Expanded(flex: 2, child: _visionBox(context, app, app.sephiraUnits, title: "Sephira's Visions", key: const Key('sephira-visions'), isSephira: true)),
          const SizedBox(height: 12),
          Expanded(
            child: _visionBox(context, app, defaults, title: 'Default visions', key: const Key('default-visions'), isDefault: true),
          ),
          const SizedBox(height: 12),
          Expanded(child: _visionBox(context, app, party, title: 'Party characters', key: const Key('party-characters'), isParty: true)),
          const CharacterConfigButtons(includeAll: true),
        ]),
      ),
      Container(width: 2, color: Guide.ink),
      Expanded(
        flex: 5,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Band('Install', color: Guide.red),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                Box(
                  padding: EdgeInsets.zero,
                  child: Column(children: [
                    StatRow('Game', app.gameRunning ? 'running' : 'closed', trailing: Icon(app.gameRunning ? Icons.warning_amber : Icons.check, size: 16, color: app.gameRunning ? Guide.gold : Guide.green)),
                    StatRow('Mod in the game', app.modInstalled ? 'installed' : 'not installed', zebra: true),
                    StatRow('Units ready', '${app.includedUnitCount}'),
                  ]),
                ),
                const SizedBox(height: 14),
                Text(app.gameRunning
                    ? 'Close the game to install. You can keep editing meanwhile.'
                    : 'Builds the mod from your edits and copies it into the game. Added visions are sold in the Mitra item shop; original visions keep their game identity. Party replacements apply during battles.', style: Guide.text()),
                const SizedBox(height: 14),
                Row(children: [
                  Expanded(child: SwitchListTile(
                    key: const Key('show-unverified-skills'), contentPadding: EdgeInsets.zero,
                    title: Text('Show unverified skills', style: Guide.text()),
                    value: app.showUnverifiedSkills,
                    onChanged: busy || app.api == null ? null : (value) async {
                      try { await app.setAbilityModes(showUnverified: value); } catch (e) { app.showNotice('$e'); }
                    },
                  )),
                  Expanded(child: CheckboxListTile(
                    key: const Key('use-ability-changes'), contentPadding: EdgeInsets.zero,
                    title: Text('Use our skill changes', style: Guide.text()),
                    value: app.useAbilityChanges,
                    onChanged: !app.showUnverifiedSkills || busy || app.api == null ? null : (value) async {
                      try { await app.setAbilityModes(useChanges: value == true); } catch (e) { app.showNotice('$e'); }
                    },
                  )),
                ]),
                CheckboxListTile(
                  key: const Key('native-skill-repairs'), contentPadding: EdgeInsets.zero,
                  title: Text('Repair native skill bindings / motions', style: Guide.text()),
                  subtitle: Text('Uses the skill’s own effects and timing. Repairs audited player bindings, aiming and caster motions without borrowing effects.', style: Guide.small()),
                  value: app.useNativeSkillRepairs,
                  onChanged: !app.showUnverifiedSkills || busy || app.api == null ? null : (value) async {
                    try { await app.setAbilityModes(useNativeRepairs: value == true); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                Text(!app.showUnverifiedSkills
                    ? 'Original library selection; library skill repairs are off.'
                    : app.useAbilityChanges
                        ? 'Studio skill repairs and reviewed hiding rules are on. Existing game animations take priority.'
                        : app.useNativeSkillRepairs
                            ? 'Native binding, aiming and motion repairs only. Borrowed library effects, fallback timelines and reviewed hiding rules are off.'
                        : 'Unverified library skills use original game animations. Library repairs and reviewed hides are off.', style: Guide.small()),
                Text('Rebuild/install after changing modes to replace the previous mod. Equipped skills and saved configs are retained.', style: Guide.small()),
                SwitchListTile(
                  key: const Key('sephira-borrowed-skill-visuals'), contentPadding: EdgeInsets.zero,
                  title: Text('Use borrowed Sephira skill visuals', style: Guide.text()),
                  subtitle: Text(app.useSephiraBorrowedVisuals
                      ? 'Uses the preset spell and attack effects. Turn off to try original source visuals; missing demo effects may stay blank. Rebuild/install to apply.'
                      : 'Uses original source visuals. MP, power, effects and saved kits are kept. Turn on and rebuild/install to restore the borrowed visuals.', style: Guide.small()),
                  value: app.useSephiraBorrowedVisuals,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setSephiraBorrowedVisuals(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                const SizedBox(height: 14),
                SwitchListTile(
                  key: const Key('sephira-shop-override'), contentPadding: EdgeInsets.zero,
                  title: Text('Sephira visions: 1-gil Mitra shop', style: Guide.text()),
                  subtitle: Text('Sell ${app.sephiraShopSelection == null ? 'all enabled' : '${app.sephiraShopSelection!.length} selected'} Sephira visions for 1 gil each. Other visions keep their normal locations. Rebuild/install to apply.', style: Guide.small()),
                  value: app.sephiraShopOverride,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setSephiraShopOverride(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                Align(alignment: Alignment.centerLeft, child: TextButton(
                  key: const Key('sephira-shop-selection'),
                  onPressed: busy || app.engineDown || app.api == null ? null : () => _chooseShopVisions(context, app),
                  child: const Text('Choose visions for the shop override'),
                )),
                SwitchListTile(
                  key: const Key('field-leader-cycle'), contentPadding: EdgeInsets.zero,
                  title: Text('Cycle walking character (LB / L1)', style: Guide.text()),
                  subtitle: Text('Cycles the active party’s field appearances while freely walking. F6 also works. Battle models stay separate; story appearances return for events. Requires the UE4SS loader prepared by the field-reference helper. Rebuild/install after switching.', style: Guide.small()),
                  value: app.fieldLeader,
                  onChanged: busy || app.api == null ? null : (value) async {
                    try { await app.setFieldLeader(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('testing-practice-battle'), contentPadding: EdgeInsets.zero,
                  title: Text('Shop practice battle', style: Guide.text()),
                  subtitle: Text('Young Woman in Mitra\'s item shop opens an in-game opponent picker. Includes the level-10 Crystal Fina boss test. Choose a different enemy for each fight without rebuilding. Rebuild/install after switching.', style: Guide.small()),
                  value: app.testingPracticeBattle,
                  onChanged: busy || app.api == null ? null : (value) async {
                    try { await app.setTestingPracticeBattle(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('testing-survive-at-one'), contentPadding: EdgeInsets.zero,
                  title: Text('Survive at 1 HP for testing', style: Guide.text()),
                  subtitle: Text('Party members take normal damage and can be healed, but survive lethal damage at 1 HP. Also resists instant death. Applies in all battles while enabled; rebuild/install after switching.', style: Guide.small()),
                  value: app.surviveAtOne,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setSurviveAtOne(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('testing-no-encounters'), contentPadding: EdgeInsets.zero,
                  title: Text('In-game encounter toggle', style: Guide.text()),
                  subtitle: Text('F7 or hold both controller triggers for 1 second while walking. Shows ON/OFF on screen; starts ON each game launch. Bosses and scripted fights remain available. Requires UE4SS; rebuild/install once after changing this switch.', style: Guide.small()),
                  value: app.noEncounters,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setNoEncounters(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('minimap-treasure'), contentPadding: EdgeInsets.zero,
                  title: Text('Show treasure on the minimap', style: Guide.text()),
                  subtitle: Text('Marks chests, glowing items and tablet fragments on the current map. '
                    '${app.minimapTreasure['message'] ?? 'Select your game folder first.'}', style: Guide.small()),
                  value: app.minimapTreasure['enabled'] == true,
                  onChanged: busy || app.engineDown || app.gameRunning || app.api == null ||
                    app.minimapTreasure['available'] != true || app.minimapTreasure['conflict'] == true ? null : (value) async {
                    try { await app.setMinimapTreasure(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('testing-ffbe-needles'), contentPadding: EdgeInsets.zero,
                  title: Text('Test FFBE 1,000 Needles visual', style: Guide.text()),
                  subtitle: Text('Imports the original FFBE needle groups and hit sounds for this skill on either side. Keeps native damage and MP. Independent of the other visual switches; rebuild/install after changing. Experimental: appearance and placement need in-game testing.', style: Guide.small()),
                  value: app.ffbeNeedles,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setFfbeNeedles(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('fina-cinematic'), contentPadding: EdgeInsets.zero,
                  title: Text('Crystal Fina resonance cinematic', style: Guide.text()),
                  subtitle: Text('Adds her movie and cave music before the sprite resonance. Off by default; her healing and sprite animation still play. Rebuild/install and restart the game after changing.', style: Guide.small()),
                  value: app.finaCinematic,
                  onChanged: busy || app.engineDown || app.api == null ? null : (value) async {
                    try { await app.setFinaCinematic(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                SwitchListTile(
                  key: const Key('testing-max-mr'), contentPadding: EdgeInsets.zero,
                  title: Text('One-battle MR for testing', style: Guide.text()),
                  subtitle: Text('Equipped visions earn the bounded native MR completion reward per reward-bearing victory. Does not change awakening ranks.', style: Guide.small()),
                  value: app.testingMaxMr,
                  onChanged: busy || app.api == null ? null : (value) async {
                    try { await app.setTestingMaxMr(value); } catch (e) { app.showNotice('$e'); }
                  },
                ),
                Align(alignment: Alignment.centerLeft, child: GuideButton('Preview Crystal Fina cinematic',
                  key: const Key('preview-fina-cinematic'), icon: Icons.movie_outlined,
                  onPressed: app.api == null ? null : () => launchUrl(Uri.parse('${app.api!.base}/crystal-fina-cinematic')))),
                Text('Drag default visions into Added visions to acquire the originals at the next battle start. Drag them back to stop. Install after changes; test on a clean save without saving, then disable and reinstall before reloading.', style: Guide.small()),
                const SizedBox(height: 14),
                Row(children: [
                  GoButton(busy ? 'Working' : 'Install into the game', busy: busy, onPressed: !canBuild || app.gameRunning || busy || app.sephiraWorking ? null : () => app.startBuild(install: true, prepareRuntime: () => confirmRuntimeInstall(context, app.api!))),
                ]),
                const SizedBox(height: 10),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  GuideButton('Build without installing', onPressed: !canBuild || busy || app.sephiraWorking ? null : () => app.startBuild(install: false)),
                  GuideButton('Install the last build', onPressed: app.gameRunning || busy || app.sephiraWorking ? null : () => app.installLast(prepareRuntime: () => confirmRuntimeInstall(context, app.api!, lastBuild: true))),
                  GuideButton('Game tools & snapshots', key: const Key('launch-preparation'), icon: Icons.fact_check_outlined,
                      onPressed: busy || app.api == null ? null : () async {
                        await app.save();
                        if (app.dirty) return;
                        await launchUrl(Uri.parse('${app.api!.base}/launch-preparation'));
                      }),
                  if (app.snapshotConflict) GuideButton('Reload restored setup', key: const Key('reload-restored-setup'),
                      onPressed: busy ? null : () async {
                        try { await app.reloadRestoredSetup(); } catch (e) { app.showNotice('$e'); }
                      }),
                  GuideButton('FFBE animation library', key: const Key('ffbe-animation-library'), icon: Icons.movie_outlined, onPressed: app.api == null ? null : () => launchUrl(Uri.parse('${app.api!.base}/ffbe-animation-library'))),
                  GuideButton('Advanced studio', icon: Icons.open_in_new, onPressed: app.api == null ? null : () => launchUrl(Uri.parse(app.api!.advancedUrl()))),
                ]),
                const SizedBox(height: 6),
                Text('Advanced opens the full studio in your browser: Brave Exvius kit imports, sprite settings, animation edits. It works on the same units.', style: Guide.small()),
                if (app.buildState != null) ...[const SizedBox(height: 18), const BuildStatus()],
                const SizedBox(height: 22),
                DeckSyncPanel(canBuild: canBuild),
                const SizedBox(height: 22),
                Band('Your game files', color: Guide.ink),
                Box(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Vision builds use three files in FFRS/Content/Paks/~mods. Previous vision builds are backed up before installing; the game\'s own files are preserved. Treasure radar is managed separately by the switch above.', style: Guide.text()),
                    const SizedBox(height: 10),
                    Row(children: [
                      GuideButton('Restore the original game', icon: Icons.history, danger: true, onPressed: app.gameRunning || busy || app.api == null ? null : () => showRestoreDialog(context)),
                      const SizedBox(width: 12),
                      Text(app.backups == 0 ? 'no backups yet' : '${app.backups} backup${app.backups == 1 ? '' : 's'} kept', style: Guide.small()),
                    ]),
                  ]),
                ),
              ]),
            ),
          ),
        ]),
      ),
    ]);
  }

  Widget _visionBox(BuildContext context, AppState app, List<Map<String, dynamic>> entries, {required String title, required Key key, bool allowAdd = false, bool isParty = false, bool isSephira = false, bool isDefault = false}) => DragTarget<int>(
        onWillAcceptWithDetails: (details) => !(app.building || app.deckWorking) && !isParty && !isSephira &&
            entries.every((u) => u['id'] != details.data),
        onAcceptWithDetails: (details) async {
          try {
            await app.editNativeVision(details.data, testAcquire: allowAdd, selectEditor: false);
          } catch (e) { app.showNotice('$e'); }
        },
        builder: (_, candidates, _) => Container(
        key: key,
        decoration: BoxDecoration(border: Border.all(color: candidates.isEmpty ? Guide.ink : Guide.blue, width: 1.5)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Band(title, trailing: isSephira ? Switch(
            key: const Key('sephira-enabled'),
            value: app.sephiraEnabled,
            onChanged: (app.building || app.deckWorking) || app.sephiraWorking || app.api == null ? null : (value) async {
              try { await app.setSephiraEnabled(value); } catch (e) { app.showNotice('$e'); }
            },
          ) : Text('${entries.length} ${isParty ? 'character' : 'vision'}${entries.length == 1 ? '' : 's'}', style: Guide.band().copyWith(letterSpacing: 0.4, fontSize: 13))),
          if (isDefault) Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Align(alignment: Alignment.centerLeft, child: GuideButton('Reset all visions',
              key: const Key('default-visions-reset-all'),
              onPressed: app.building || app.deckWorking || app.api == null || !app.units.any((u) => u['native'] != null)
                  ? null : () => confirmResetNativeVisions(context, app))),
          ),
          if (isSephira) Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(app.sephiraWorking ? app.sephiraProgress ?? 'Preparing visions…'
                  : app.sephiraRecipeUpdate ? 'Kit and MR update available. Apply it below, then build/install.'
                  : app.sephiraEnabled ? '${entries.length} presets enabled. Build/install to apply.'
                  : 'Off. Presets and edits are kept; build/install to remove them from the game.', style: Guide.small()),
              Wrap(spacing: 8, children: [
                if (app.sephiraRecipeUpdate) GuideButton('Apply kit and MR updates',
                  key: const Key('sephira-progression-update'),
                  onPressed: (app.building || app.deckWorking) || app.sephiraWorking || app.api == null ? null : () async {
                    try { await app.updateSephiraProgression(); } catch (e) { app.showNotice('$e'); }
                  }),
                GuideButton('Restore missing', key: const Key('sephira-restore-missing'),
                  onPressed: (app.building || app.deckWorking) || app.sephiraWorking || app.api == null ? null : () async {
                    try { await app.restoreSephira(); } catch (e) { app.showNotice('$e'); }
                  }),
                GuideButton('Reset all presets', key: const Key('sephira-reset-all'),
                  onPressed: (app.building || app.deckWorking) || app.sephiraWorking || app.api == null ? null : () => confirmResetSephira(context, app)),
              ]),
            ]),
          ),
          Expanded(
            child: entries.isEmpty
                ? allowAdd ? SingleChildScrollView(child: _empty(context)) : Center(child: Text(isSephira ? 'Enable the collection to add its presets.' : isParty ? 'Prepare game files to load party characters.' : 'No default visions loaded.', style: Guide.small()))
                : GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent: 300, mainAxisExtent: 128, crossAxisSpacing: 12, mainAxisSpacing: 12),
                    itemCount: entries.length + (allowAdd ? 1 : 0),
                    itemBuilder: (_, i) => i == entries.length ? _addEntry(context) : _entry(context, app, entries[i], allowRemove: allowAdd || isSephira),
                  ),
          ),
        ]),
      ),
      );

  Widget _empty(BuildContext context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('No visions yet.', style: Guide.h2()),
          const SizedBox(height: 8),
          Text('Add a unit from Brave Exvius, give it abilities, bonuses, stats and a Resonance from what the game already has, then install. Ten minutes for the first one.', style: Guide.text()),
          const SizedBox(height: 16),
          GoButton('Add a unit', color: Guide.blue, icon: Icons.add, onPressed: () => showAddUnit(context)),
        ]),
      );

  Widget _addEntry(BuildContext context) => Material(
        color: Guide.paper,
        shape: Border.fromBorderSide(BorderSide(color: Guide.ink, width: 1.5)),
        child: InkWell(
          onTap: () => showAddUnit(context),
          hoverColor: Guide.paper2,
          child: Center(child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.add, color: Guide.ink), const SizedBox(width: 8), Text('ADD A UNIT', style: Guide.band(Guide.ink))])),
        ),
      );

  Future<void> _visionMenu(BuildContext context, AppState app, Map<String, dynamic> unit, Offset position) async {
    final overlay = Overlay.of(context).context.findRenderObject()! as RenderBox;
    final local = overlay.globalToLocal(position);
    final action = await showMenu<String>(
      context: context,
      position: RelativeRect.fromRect(Rect.fromLTWH(local.dx, local.dy, 0, 0), Offset.zero & overlay.size),
      color: Guide.paper,
      shape: Border.fromBorderSide(Guide.frame),
      items: [PopupMenuItem(
        value: 'remove',
        enabled: !(app.building || app.deckWorking) && app.api != null,
        child: Text('Remove vision', style: Guide.text()),
      ), if (SephiraVisions.member(unit)) PopupMenuItem(
        value: 'reset', enabled: !(app.building || app.deckWorking) && !app.sephiraWorking && app.api != null,
        child: Text('Reset to preset', style: Guide.text()),
      )],
    );
    if (action == 'remove' && context.mounted) {
      await confirmRemove(context, app, unit);
    }
    if (action == 'reset' && context.mounted) await confirmResetSephira(context, app, unit: unit);
  }

  Widget _entry(BuildContext context, AppState app, Map<String, dynamic> u, {bool allowRemove = false}) {
    final native = u['native'] != null;
    final party = u['party'] != null;
    final edited = app.units.any((x) => x['key'] == u['key']);
    final rewards = [...u['awakening'] as List? ?? [], ...u['synchro'] as List? ?? []].cast<List>();
    final abilities = rewards.fold<int>(0, (n, t) => n + t.where((g) => g[0] == 'ActiveSkill').length);
    final bonuses = rewards.fold<int>(0, (n, t) => n + t.where((g) => g[0] != 'ActiveSkill').length);
    final lb = u['lb_custom'] as Map?;
    final card = Material(
      color: Guide.paper,
      shape: Border.fromBorderSide(BorderSide(color: Guide.ink, width: 1.5)),
      child: InkWell(
        onTap: () => party ? choosePartyCharacter(context, u) : native ? chooseNativeVision(context, u) : app.select(u['key'] as String),
        onSecondaryTapUp: allowRemove ? (details) => _visionMenu(context, app, u, details.globalPosition) : null,
        hoverColor: Guide.paper2,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Frame(padding: 2, child: party && u['ffbe'] == null
                ? PartyPortrait(characterId: u['id'] as int, width: 72, height: 72)
                : native && u['ffbe'] == null
                ? NativePortrait(visionId: u['id'] as int, fallbackUrl: app.api!.nativeIcon(u['id'] as int), width: 72, height: 72)
                : PixelImage(app.api!.unitIcon(u['key'] as String, 'face', form: (u['ffbe'] as Map?)?['id']?.toString(),
                    appearanceRevision: u['sephiraAppearanceRevision'] as int?), width: 72, height: 72)),
            const SizedBox(width: 10),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text((u['en'] as String? ?? '').toUpperCase(), style: Guide.h2().copyWith(fontSize: 20), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Text(party ? 'Battle appearance' : '${u['attackType'] == 'Magic' ? 'Magic' : 'Physical'} · ${((u['roles'] as List?) ?? []).map((r) => r.toString().replaceAll('eUnitRole::', '')).join(', ')}', style: Guide.small(), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 6),
                Text(party ? (u['ffbe'] == null ? 'Original model' : 'Replacement model') : '$abilities abilities · $bonuses bonuses', style: Guide.small(Guide.ink)),
                Text(party ? (edited ? 'Party character · your edits' : 'Party character · defaults') : native ? (u['testAcquire'] == true ? 'Original vision · test acquisition' : edited ? 'Game vision · your edits' : 'Game vision · defaults') : 'Resonance: ${lb != null ? lb['en'] : 'borrowed'}', style: Guide.small(), maxLines: 1, overflow: TextOverflow.ellipsis),
              ]),
            ),
          ]),
        ),
      ),
    );
    if (!native) { return card; }
    return Draggable<int>(
      key: ValueKey('drag-native-${u['id']}'), data: u['id'] as int,
      maxSimultaneousDrags: (app.building || app.deckWorking) ? 0 : 1,
      feedback: Material(child: SizedBox(width: 280, height: 128, child: card)),
      childWhenDragging: Opacity(opacity: 0.4, child: card),
      child: card,
    );
  }
}

/// Restore: shows exactly what will be removed and what comes back, then does it. A backup can also be put back one by one.
Future<void> showRestoreDialog(BuildContext context) async {
  final app = context.read<AppState>();
  Map<String, dynamic>? files;
  String? err;
  try { files = await app.api!.gameFiles(); } catch (e) { err = e.toString(); }
  if (!context.mounted) return;
  final present = ((files?['present'] as List?) ?? []).cast<Map<String, dynamic>>();
  final backups = ((files?['backups'] as List?) ?? []).cast<Map<String, dynamic>>();
  final ours = present.where((f) => f['ours'] == true).toList();
  final foreign = present.where((f) => f['ours'] != true).toList();
  final original = ((files?['record'] as Map?)?['original'] as Map?) ?? {};
  await showDialog<void>(
    context: context,
    builder: (c) => Dialog(
      backgroundColor: Guide.paper,
      shape: Border.fromBorderSide(Guide.frame),
      child: SizedBox(
        width: 640,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Band('Restore the original game', color: Guide.ink),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
              if (err != null) Text(err, style: Guide.text(Guide.red))
              else ...[
                Text(ours.isEmpty ? 'Nothing of the studio\'s is in the game folder. There is nothing to remove.' : 'These files are removed from the game folder:', style: Guide.text()),
                if (ours.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Box(padding: EdgeInsets.zero, child: Column(children: [for (var i = 0; i < ours.length; i++) StatRow(ours[i]['path'].toString(), _mb(ours[i]['size']), zebra: i.isOdd)])),
                ],
                if (original.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text('These files were there before the studio and are put back:', style: Guide.text()),
                  const SizedBox(height: 6),
                  for (final k in original.keys) Text(k.toString(), style: Guide.small(Guide.ink)),
                ],
                if (foreign.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text('Other mods in the same folder stay as they are: ${foreign.map((f) => f['path'].toString().split('/').last).join(', ')}.', style: Guide.small()),
                ],
                const SizedBox(height: 10),
                Text('The game\'s own files are never changed by the studio, so this brings the game back to the state Steam installed. Your units stay in the studio; installing again puts the mod back.', style: Guide.small()),
                if (backups.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text('BACKUPS', style: Guide.label()),
                  const SizedBox(height: 4),
                  Text('Each install keeps the files it replaced. Put one back to return to that earlier install.', style: Guide.small()),
                  const SizedBox(height: 6),
                  Box(
                    padding: EdgeInsets.zero,
                    child: Column(children: [
                      for (var i = backups.length - 1; i >= 0 && i >= backups.length - 6; i--)
                        Container(
                          color: (backups.length - 1 - i).isOdd ? Guide.paper2 : Guide.paper,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          child: Row(children: [
                            Expanded(child: Text(_stamp(backups[i]['id'].toString()), style: Guide.strong())),
                            Text('${(backups[i]['files'] as List).length} files · ${_mb(backups[i]['size'])}', style: Guide.small()),
                            const SizedBox(width: 10),
                            GuideButton('Put back', small: true, onPressed: () async {
                              Navigator.pop(c);
                              try { await app.restoreGame(backup: backups[i]['id'].toString()); } catch (e) { app.showNotice(e.toString()); }
                            }),
                          ]),
                        ),
                    ]),
                  ),
                ],
              ],
            ]),
          ),
          Container(height: 1, color: Guide.hairline),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 14),
            child: Row(children: [
              const Spacer(),
              GuideButton('Keep the mod', onPressed: () => Navigator.pop(c)),
              const SizedBox(width: 8),
              GuideButton('Restore the original game', icon: Icons.history, danger: true, onPressed: err != null ? null : () async {
                Navigator.pop(c);
                try { await app.restoreGame(); } catch (e) { app.showNotice(e.toString()); }
              }),
            ]),
          ),
        ]),
      ),
    ),
  );
}

String _mb(dynamic size) { final n = (size as num?)?.toDouble() ?? 0; return n > 1e6 ? '${(n / 1e6).toStringAsFixed(n > 1e8 ? 0 : 1)} MB' : '${(n / 1e3).toStringAsFixed(0)} KB'; }
String _stamp(String id) => id.length >= 15 ? '${id.substring(0, 4)}-${id.substring(4, 6)}-${id.substring(6, 8)} ${id.substring(9, 11)}:${id.substring(11, 13)}' : id;
