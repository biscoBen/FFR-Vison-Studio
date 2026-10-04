import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../design/theme.dart';
import '../design/widgets.dart';
import '../state/app_state.dart';
import '../state/catalog_helpers.dart';
import 'steps/abilities_step.dart';
import 'steps/bonuses_step.dart';
import 'steps/resonance_step.dart';
import 'steps/stats_step.dart';
import 'steps/mr_step.dart';
import 'steps/acquisition_step.dart';
import 'steps/native_resonance_step.dart';
import 'native_vision_dialog.dart';
import 'unit_anim_pane.dart';
import 'character_config_buttons.dart';
import 'native_portrait.dart';
import 'party_character_screen.dart';

/// A unit's page: the character entry and its editable configuration.
class UnitScreen extends StatefulWidget {
  const UnitScreen({super.key});
  @override
  State<UnitScreen> createState() => _UnitScreenState();
}

class _UnitScreenState extends State<UnitScreen> {
  int step = 0;
  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final u = app.selected;
    if (u == null) return const SizedBox.shrink();
    if (u['party'] != null) { return PartyCharacterScreen(unit: u); }
    final api = app.api!;
    final stats = (u['stats'] as Map?) ?? {};
    final form = (u['ffbe'] as Map?)?['id']?.toString();
    void set(Map<String, dynamic> patch) => app.update({...u, ...patch});
    return Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      SizedBox(
        width: 300,
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Band((u['en'] ?? '').toString(), color: Guide.ink),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                if (form != null) UnitAnimPane(unit: u, height: 210) else Frame(padding: 8, child: u['native'] != null
                    ? NativePortrait(visionId: u['id'] as int, fallbackUrl: api.nativeIcon(u['id'] as int), width: 128, height: 128)
                    : PixelImage(api.unitIcon(u['key'] as String, 'face'), width: 128, height: 128)),
                if (u['native'] != null) ...[
                  const SizedBox(height: 8),
                  GuideButton('Change model', onPressed: app.building ? null : () => showChangeModel(context, u['id'] as int)),
                  if (form != null) GuideButton('Use original model', onPressed: app.building ? null : () => app.useOriginalModel(u)),
                ],
                const SizedBox(height: 6),
                Text('${u['attackType'] == 'Magic' ? 'Magic' : 'Physical'} · ${((u['roles'] as List?) ?? []).map((r) => r.toString().replaceAll('eUnitRole::', '')).join(', ')}', style: Guide.small()),
                const SizedBox(height: 14),
                Band('Stats at level 1', color: Guide.blue),
                Box(
                  padding: EdgeInsets.zero,
                  child: Column(children: [
                    for (var i = 0; i < statFields.length; i++) StatRow(statFields[i].$2, '${stats[statFields[i].$1] ?? '-'}', zebra: i.isOdd),
                  ]),
                ),
                const SizedBox(height: 14),
                Band('Resonance', color: Guide.gold),
                Box(child: Builder(builder: (_) {
                  final lb = u['lb_custom'] as Map?;
                  final tpl = (app.catalog?['lbTemplates'] as List?)?.cast<Map>().where((t) => t['id'] == (lb?['visuals'] ?? lb?['from'])).firstOrNull;
                  final el = (lb?['set'] as Map?)?['element']?.toString();
                  final originalLb = ((app.catalog?['skills'] as List?) ?? []).cast<Map>().where((s) => s['id'] == u['lb']).firstOrNull;
                  return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(lb?['desc']?.toString().isNotEmpty == true ? lb!['desc'].toString() : u['native'] != null ? (originalLb?['desc'] ?? originalLb?['name'] ?? 'Original game Resonance').toString() : 'Set in step 4.', style: Guide.small(Guide.ink)),
                    if (tpl != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text('${tpl['name']}${el != null && el != 'None' ? ' · $el' : ''}${tpl['good'] == true ? '' : ' · no limit-burst motion'}', style: Guide.small(tpl['good'] == true ? Guide.inkSoft : Guide.red))),
                  ]);
                })),
              ]),
            ),
          ),
          const CharacterConfigButtons(),
        ]),
      ),
      Container(width: 2, color: Guide.ink),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Container(
            color: Guide.paper2,
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
            child: SingleChildScrollView(scrollDirection: Axis.horizontal,
              child: PageTabs(tabs: const ['Abilities', 'Bonuses', 'Stats', 'Resonance', 'MR', 'Acquisition'], index: step, onSelect: (i) => setState(() => step = i))),
          ),
          Container(height: 2, color: Guide.ink),
          Expanded(
            child: AnimatedSwitcher(
              duration: Guide.fast,
              layoutBuilder: (current, previous) => Stack(fit: StackFit.expand, children: [...previous, ?current]),
              child: switch (step) {
                0 => AbilitiesStep(key: const ValueKey('a'), unit: u, set: set),
                1 => BonusesStep(key: const ValueKey('b'), unit: u, set: set),
                2 => StatsStep(key: const ValueKey('s'), unit: u, set: set),
                4 => MrStep(key: const ValueKey('mr'), unit: u, set: set),
                5 => AcquisitionStep(key: ValueKey('acquisition-${u['key']}'), unit: u, set: set, locations: app.acquisitionLocations, removeCave: app.removeAcquisitionCave),
                3 when u['native'] != null => NativeResonanceStep(key: const ValueKey('native-r'), unit: u, set: set),
                _ => ResonanceStep(key: const ValueKey('r'), unit: u, set: set),
              },
            ),
          ),
        ]),
      ),
    ]);
  }
}
