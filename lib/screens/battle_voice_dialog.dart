import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../services/battle_voice.dart';
import '../state/app_state.dart';

Future<void> showBattleVoice(
  BuildContext context,
  Map<String, dynamic> character,
) async {
  final app = context.read<AppState>();
  final id = character['id'] as int;
  final saved = app.units.where((u) => u['party']?['id'] == id);
  var selected =
      ((saved.isEmpty ? character : saved.single)['battleVoice'] ?? id) as int;
  final choice = await showDialog<int>(
    context: context,
    builder: (c) => StatefulBuilder(
      builder: (c, setState) => AlertDialog(
        backgroundColor: Guide.paper,
        shape: Border.fromBorderSide(Guide.frame),
        title: Text('${character['en']} · battle voice', style: Guide.h2()),
        content: SizedBox(
          width: 360,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<int>(
                key: const Key('battle-voice-source'),
                initialValue: selected,
                decoration: const InputDecoration(labelText: 'Voice character'),
                items: [
                  for (final entry in BattleVoice.names.entries)
                    DropdownMenuItem(
                      value: entry.key,
                      child: Text(
                        '${entry.value}${entry.key == id ? ' (original)' : ''}',
                      ),
                    ),
                ],
                onChanged: app.building
                    ? null
                    : (value) {
                        if (value != null) {
                          setState(() => selected = value);
                        }
                      },
              ),
              const SizedBox(height: 16),
              Text(
                'Changes standard battle voices and authored normal-attack/LB voice sections. Story dialogue and team victory conversations keep their original voices.',
                style: Guide.text(),
              ),
              const SizedBox(height: 12),
              Text(
                'Build/install afterward to apply this choice. LB voice lines use the selected character’s generic LB recordings; wording may differ from the skill.',
                style: Guide.small(),
              ),
            ],
          ),
        ),
        actions: [
          GuideButton('Cancel', onPressed: () => Navigator.pop(c)),
          GuideButton(
            'Save voice',
            onPressed: app.building ? null : () => Navigator.pop(c, selected),
          ),
        ],
      ),
    ),
  );
  if (choice == null) {
    return;
  }
  try {
    await app.editPartyCharacter(id, battleVoice: choice);
  } catch (e) {
    app.showNotice('Could not change battle voice: $e');
  }
}
