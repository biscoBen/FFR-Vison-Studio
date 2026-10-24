import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../services/battle_voice.dart';
import '../state/app_state.dart';

Future<void> showNativeVisionVoice(
  BuildContext context,
  Map<String, dynamic> vision,
) async {
  final app = context.read<AppState>();
  final id = vision['id'] as int;
  final saved =
      app.units.where((u) => u['native']?['id'] == id).firstOrNull ?? vision;
  final original = (saved['native']?['baseline']?['en'] ?? vision['en'])
      .toString();
  var selected = (saved['nativeVoice'] ?? id) as int;
  final sources = [
    for (final u in app.nativeVisions)
      if (u['id'] != id) u,
  ]..sort((a, b) => a['en'].toString().compareTo(b['en'].toString()));
  if (selected != id && !sources.any((u) => u['id'] == selected)) selected = id;
  final choice = await showDialog<int>(
    context: context,
    builder: (c) => StatefulBuilder(
      builder: (c, setState) => AlertDialog(
        backgroundColor: Guide.paper,
        shape: Border.fromBorderSide(Guide.frame),
        title: Text('${saved['en']} · resonance voice', style: Guide.h2()),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<int>(
                key: const Key('native-vision-voice-source'),
                initialValue: selected,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Voice vision'),
                items: [
                  DropdownMenuItem(
                    value: id,
                    child: Text('Original voice · $original'),
                  ),
                  for (final source in sources)
                    DropdownMenuItem(
                      value: source['id'] as int,
                      child: Text(source['en'].toString()),
                    ),
                ],
                onChanged: app.building
                    ? null
                    : (value) {
                        if (value != null) setState(() => selected = value);
                      },
              ),
              const SizedBox(height: 16),
              Text(
                'Uses the selected default vision’s resonance voice. Longer lines may be cut short by the original resonance timing. Build/install to apply this choice.',
                style: Guide.text(),
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
  if (choice == null) return;
  try {
    await app.editNativeVision(id, voiceSource: choice, selectEditor: false);
  } catch (e) {
    app.showNotice('Could not change this voice: $e');
  }
}

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
