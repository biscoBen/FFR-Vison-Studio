import 'package:flutter/material.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';

/// Removes an added unit or the selected default vision's overrides.
Future<void> confirmRemove(
  BuildContext context,
  AppState app,
  Map<String, dynamic> unit,
) async {
  final party = unit['party'] != null;
  final native = unit['native'] != null || party;
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
        party ? 'This restores the original battle and overworld models on the next build/install. Save its character config first to keep your choices.' : native
            ? 'This restores the original model, abilities, bonuses, stats, Resonance and MR rewards by removing this vision\'s overrides. Save its character config first to keep your edits. The next build/install applies the original vision to the game.'
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
