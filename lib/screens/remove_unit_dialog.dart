import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';
import '../services/sephira_visions.dart';

/// Removes an added unit or reverts a default vision/party character.
Future<void> confirmRemove(
  BuildContext context,
  AppState app,
  Map<String, dynamic> unit,
) async {
  if (unit['party'] != null) {
    await _confirmRevertParty(context, app, unit);
    return;
  }
  final native = unit['native'] != null;
  final ok = await showDialog<bool>(
    context: context,
    builder: (c) => AlertDialog(
      backgroundColor: Guide.paper,
      shape: Border.fromBorderSide(Guide.frame),
      title: Text(
        native
            ? 'Revert ${unit['en']} to original?'
            : 'Remove ${unit['en']} from the mod?',
        style: Guide.h2(),
      ),
      content: Text(
        native
            ? 'This restores the original model, abilities, bonuses, stats, Resonance and MR rewards by removing this vision\'s overrides. Save its character config first to keep your edits. The next build/install applies the original vision to the game.'
            : SephiraVisions.member(unit)
                ? 'This removes the vision from the collection. Restore missing brings back its preset later. Save its character config to keep your edits. Build/install to remove it from the game.'
                : 'The unit and its choices are deleted from the mod. Save its character config first if you want to restore this setup later. The next install removes it from the game.',
        style: Guide.text(),
      ),
      actions: [
        GuideButton('Keep', onPressed: () => Navigator.pop(c, false)),
        GuideButton(
          native ? 'Revert to original' : 'Remove',
          danger: true,
          onPressed: () => Navigator.pop(c, true),
        ),
      ],
    ),
  );
  if (ok == true) {
    await app.removeUnit(unit['key'] as String);
  }
}

Future<void> confirmResetSephira(BuildContext context, AppState app, {Map<String, dynamic>? unit}) async {
  final ok = await showDialog<bool>(context: context, builder: (c) => AlertDialog(
    backgroundColor: Guide.paper,
    title: Text(unit == null ? 'Reset all Sephira presets?' : 'Reset ${unit['en']} to its preset?', style: Guide.h2()),
    content: Text('Restores preset kits and appearances, replacing their edits and bringing back missing entries. Acquisition locations are kept. A roster backup is saved in your config backups. Your other visions and party edits are kept.', style: Guide.text()),
    actions: [
      GuideButton('Keep edits', onPressed: () => Navigator.pop(c, false)),
      GuideButton('Reset to preset', danger: true, onPressed: () => Navigator.pop(c, true)),
    ],
  ));
  if (ok == true) {
    try { await app.restoreSephira(presetId: unit == null ? null : SephiraVisions.presetId(unit), reset: true); }
    catch (e) { app.showNotice('$e'); }
  }
}

Future<void> _confirmRevertParty(
  BuildContext context,
  AppState app,
  Map<String, dynamic> unit,
) async {
  // Home can supply the original character rather than its saved override.
  final overrides = app.units.where((u) => u['key'] == unit['key']);
  final current = overrides.isEmpty ? unit : overrides.single;
  final battle = ['ffbe', 'menuScale', 'icon'].any(current.containsKey);
  final overworld = current['overworld'] != null;
  final choice = await showDialog<String>(
    context: context,
    builder: (c) => AlertDialog(
      backgroundColor: Guide.paper,
      shape: Border.fromBorderSide(Guide.frame),
      title: Text('Revert ${unit['en']} to original?', style: Guide.h2()),
      content: Text(
        'Choose which appearance to restore. Appearance reverts keep your battle voice choice. Revert all also restores the original voice. Build/install afterward to apply it to the game. Save the character config first to keep your choices.',
        style: Guide.text(),
      ),
      actions: [
        GuideButton('Keep', onPressed: () => Navigator.pop(c)),
        GuideButton('Revert battle only', danger: true,
          onPressed: app.building || !battle ? null : () => Navigator.pop(c, 'battle')),
        GuideButton('Revert overworld only', danger: true,
          onPressed: app.building || !overworld ? null : () => Navigator.pop(c, 'overworld')),
        GuideButton('Revert both', danger: true,
          onPressed: app.building || overrides.isEmpty ? null : () => Navigator.pop(c, 'both')),
        if (current['battleVoice'] != null) GuideButton('Revert all', danger: true,
          onPressed: app.building ? null : () => Navigator.pop(c, 'all')),
      ],
    ),
  );
  if (choice == null) { return; }
  try {
    if (choice == 'all' || (choice == 'both' && current['battleVoice'] == null)) {
      await app.removeUnit(unit['key'] as String);
    } else {
      await app.editPartyCharacter(unit['id'] as int,
        clearBattle: choice == 'battle' || choice == 'both', clearOverworld: choice == 'overworld' || choice == 'both');
    }
  } catch (e) {
    app.showNotice('Could not revert this appearance: $e');
  }
}
