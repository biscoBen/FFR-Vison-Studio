import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';
import 'character_config_buttons.dart';
import 'native_vision_dialog.dart';
import 'party_portrait.dart';
import 'remove_unit_dialog.dart';
import 'unit_anim_pane.dart';
import 'overworld_anim_pane.dart';
import '../services/overworld_appearance.dart';

class PartyCharacterScreen extends StatelessWidget {
  const PartyCharacterScreen({super.key, required this.unit});
  final Map<String, dynamic> unit;
  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Band('${unit['en']} · appearance', color: Guide.blue),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (unit['ffbe'] != null)
                  SizedBox(
                    width: 360,
                    child: UnitAnimPane(unit: unit, height: 260),
                  )
                else
                  Padding(
                    padding: const EdgeInsets.all(30),
                    child: PartyPortrait(characterId: unit['id'] as int, width: 96, height: 96),
                  ),
                const SizedBox(height: 16),
                Text(
                  unit['ffbe'] == null
                      ? 'Original battle model'
                      : 'Replacement battle model · FFBE ${unit['ffbe']['id']}',
                  style: Guide.h2(),
                ),
                const SizedBox(height: 12),
                Text(
                  'Choose battle and walking appearances independently. Abilities, equipment and progression keep ${unit['en']}’s original configuration.',
                  style: Guide.text(),
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    GuideButton(
                      'Change battle model',
                      onPressed: app.building
                          ? null
                          : () => showPartyModel(context, unit['id'] as int),
                    ),
                    GuideButton(
                      'Revert to original',
                      danger: true,
                      onPressed: app.building
                          ? null
                          : () => confirmRemove(context, app, unit),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text('Overworld appearance', style: Guide.h2()),
                const SizedBox(height: 12),
                if (unit['overworld'] != null) ...[
                  SizedBox(width: 360, child: OverworldAnimPane(model: unit['overworld']['model'] as String)),
                  const SizedBox(height: 12),
                  Text(OverworldAppearance.data(unit['overworld']['model'] as String)['name'] as String, style: Guide.text()),
                ] else Text('Original walking model', style: Guide.text()),
                const SizedBox(height: 12),
                Wrap(spacing: 12, runSpacing: 12, children: [
                  GuideButton('Edit overworld appearance', onPressed: app.building ? null : () => showOverworldModel(context, unit['id'] as int)),
                  if (unit['overworld'] != null) GuideButton('Revert overworld appearance', danger: true,
                    onPressed: app.building ? null : () async {
                      try { await app.editPartyCharacter(unit['id'] as int, clearOverworld: true); }
                      catch (e) { app.showNotice('Could not revert overworld appearance: $e'); }
                    }),
                ]),
                const SizedBox(height: 20),
                Text(
                  'Install from the main page to apply your choice to the game.',
                  style: Guide.small(),
                ),
              ],
            ),
          ),
        ),
        const CharacterConfigButtons(),
      ],
    );
  }
}
