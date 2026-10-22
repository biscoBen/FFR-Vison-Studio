import 'dart:convert';

import 'package:flutter/services.dart';

import 'character_config.dart';
import 'acquisition.dart';

/// Optional, editable presets. Membership lives in portable character configs;
/// disabled entries retain their IDs and edits but are omitted by the builder.
class SephiraVisions {
  static const field = 'sephiraVision';
  static const asset = 'assets/sephira_visions/catalog.json';
  static const retired = {'great_dragon'};
  static Future<List<Map<String, dynamic>>> get bundled async =>
      parse(await rootBundle.loadString(asset));

  static List<Map<String, dynamic>> parse(String contents) {
    final document = json.decode(contents);
    if (document is! Map || document['schema'] != 1 || document['presets'] is! List) {
      throw const FormatException('Unsupported Sephira vision catalog.');
    }
    final ids = <String>{};
    final result = <Map<String, dynamic>>[];
    for (final value in document['presets']) {
      if (value is! Map<String, dynamic> || value['id'] is! String ||
          !ids.add(value['id'] as String) || value['name'] is! String ||
          value['theme'] is! String) {
        throw const FormatException('Invalid Sephira vision preset.');
      }
      final profile = value['profile'];
      if (profile != null) {
        if (profile is! Map<String, dynamic>) {
          throw const FormatException('Invalid Sephira vision profile.');
        }
        CharacterConfig.validate(profile);
      }
      result.add(value);
    }
    final profiles = result.map((p) => p['profile']).whereType<Map<String, dynamic>>().toList();
    if (profiles.isNotEmpty) CharacterConfig.validateAll(profiles);
    return result;
  }

  static bool member(Map unit) => unit[field] is Map;
  static String? presetId(Map unit) => member(unit) ? unit[field]['preset'] as String? : null;
  static bool retiredMember(Map unit) => retired.contains(presetId(unit));
  static bool included(Map unit) => !member(unit) ||
      (!retiredMember(unit) && unit[field]['enabled'] == true);

  static bool hasRecipeUpdate(Map unit, List<Map<String, dynamic>> presets) {
    final id = presetId(unit);
    if (id == null) return false;
    final current = unit['sephiraRecipe'];
    return presets.any((p) {
      final profile = p['profile'];
      final latest = profile is Map ? profile['sephiraRecipe'] : null;
      return p['id'] == id && latest is int &&
          latest > (current is int ? current : 0);
    });
  }

  static bool valid(dynamic value) => value is Map && value.length == 3 &&
      value['version'] == 1 && value['preset'] is String &&
      (value['preset'] as String).isNotEmpty && value['enabled'] is bool;

  static Map<String, dynamic> setEnabled(Map<String, dynamic> unit, bool enabled) => {
    ...unit,
    field: {...unit[field] as Map, 'enabled': enabled},
  };

  static Map<String, dynamic> instantiate(
    Map<String, dynamic> preset,
    List<dynamic> roster, {
    required bool enabled,
    Map<String, dynamic>? replacing,
  }) {
    final profile = preset['profile'];
    if (profile is! Map<String, dynamic>) {
      throw StateError('The version and kit for ${preset['name']} are not finalized yet.');
    }
    final result = CharacterConfig.restore(profile, roster, replacing: replacing);
    result[field] = {'version': 1, 'preset': preset['id'], 'enabled': enabled};
    // Resetting a kit should not move a vision out of its assigned cave/shop.
    if (replacing?.containsKey('studioAcquisition') == true) {
      result['studioAcquisition'] = CharacterConfig.copy(replacing!['studioAcquisition'] as Map<String, dynamic>);
    }
    return result;
  }

  /// Apply the requested progression/acquisition revision without resetting
  /// artwork, combat edits, identities or user-added learned abilities.
  static Map<String, dynamic> updateProgression(
    Map<String, dynamic> unit, Map<String, dynamic> preset,
  ) {
    final latest = preset['profile']['sephiraRecipe'] as int;
    if ((unit['sephiraRecipe'] as int? ?? 0) >= latest) {
      return CharacterConfig.copy(unit);
    }
    final template = CharacterConfig.restore(
        preset['profile'] as Map<String, dynamic>, [], replacing: unit);
    final result = CharacterConfig.copy(unit);
    _replaceProtectedRewards(result, template, preset);
    // Revision 5 corrects sources in place. Preserve the already-applied MR
    // schedule, custom acquisition, stats, artwork and unrelated combat edits.
    if ((unit['sephiraRecipe'] as int? ?? 0) >= 4) {
      result['sephiraRecipe'] = latest;
      CharacterConfig.validate(result);
      return result;
    }
    final available = <String, List<dynamic>>{};
    String key(List g) => '${g[0]}:${g[1]}';
    for (final field in ['awakening', 'synchro']) {
      for (final tier in result[field] as List) {
        for (final raw in tier as List) {
          final g = List<dynamic>.from(raw as List);
          if (g[0] != 'ActiveSkill' && g[0] != 'PassiveSkill') continue;
          if (available.containsKey(key(g))) {
            throw StateError('${unit['en']} has duplicate learned abilities. Edit those before applying the MR update.');
          }
          available[key(g)] = g;
        }
      }
    }
    final chosen = <List<dynamic>?>[];
    for (final rank in [1, 3, 5, 7, 9]) {
      final preferred = (template['synchro'][rank] as List).first as List;
      final match = available[key(preferred)];
      chosen.add(match);
    }
    // Honor removed/replaced abilities: fill a missing selection from the
    // saved kit instead of silently restoring a deleted combat ability.
    for (var i = 0; i < chosen.length; i++) {
      if (chosen[i] != null) continue;
      chosen[i] = available.values.where((g) =>
          !chosen.any((v) => v != null && key(v) == key(g))).firstOrNull;
    }
    if (chosen.any((v) => v == null)) throw StateError('${unit['en']} needs five learned abilities for its MR rewards.');
    final picked = chosen.map((g) => key(g!)).toSet();
    final awakening = [
      for (final tier in result['awakening'] as List)
        [for (final g in tier as List) if (!picked.contains(key(g as List))) List<dynamic>.from(g)],
    ];
    final retained = awakening.expand((t) => t).map(key).toSet();
    void awaken(List<dynamic> g, {bool early = false}) {
      final order = early ? [0, 1, 2, 3] : [3, 2, 1, 0];
      final rank = order.where((r) => awakening[r].length < 8).firstOrNull;
      if (rank == null) throw StateError('${unit['en']} has no room for its retained awakening abilities.');
      awakening[rank].add(g); retained.add(key(g));
    }
    for (final g in available.values) {
      if (!picked.contains(key(g)) && !retained.contains(key(g))) awaken(g);
    }
    // Only the eight newly authored low-tier alternatives are eligible filler.
    // Never fill a short edited kit by restoring arbitrary deleted abilities.
    final sourceBase = CharacterConfig.skillBase(preset['profile']['id'] as int);
    final targetBase = CharacterConfig.skillBase(unit['id'] as int);
    for (final identity in preset['masteryFillers'] as List? ?? []) {
      if (awakening.expand((t) => t).length >= 20) break;
      final mapped = targetBase + (identity as int) - sourceBase;
      final recipe = CharacterConfig.copy(template['skills'][mapped.toString()] as Map<String, dynamic>);
      final owned = result['skills'] as Map;
      var free = mapped;
      if (owned.containsKey(free.toString())) {
        free = List.generate(100, (i) => targetBase + i)
            .firstWhere((i) => !owned.containsKey(i.toString()));
        recipe['jp'] = '${recipe['jp']}_MR4_$free';
      }
      owned[free.toString()] = recipe;
      awaken(['ActiveSkill', free, -1], early: true);
    }
    final mastery = template['synchro'] as List;
    for (var i = 0; i < chosen.length; i++) {
      mastery[[1, 3, 5, 7, 9][i]][0] = chosen[i];
    }
    result['awakening'] = awakening;
    result['synchro'] = mastery;
    result['sephiraRecipe'] = template['sephiraRecipe'];
    if (template['sephiraAcquisition'] is Map) {
      result['sephiraAcquisition'] = template['sephiraAcquisition'];
      result[Acquisition.field] = template['sephiraAcquisition'];
    }
    CharacterConfig.validate(result);
    return result;
  }

  static void _replaceProtectedRewards(Map<String, dynamic> unit,
      Map<String, dynamic> template, Map<String, dynamic> preset) {
    final replacements = preset['rewardReplacements'] as List? ?? [];
    final sourceBase = CharacterConfig.skillBase(preset['profile']['id'] as int);
    final targetBase = CharacterConfig.skillBase(unit['id'] as int);
    final owned = unit['skills'] as Map;
    final inserted = <String, List<dynamic>>{};
    for (final field in ['awakening', 'synchro']) {
      for (final tier in unit[field] as List) {
        for (var i = 0; i < (tier as List).length; i++) {
          final grant = tier[i] as List;
          final recipe = grant[0] == 'ActiveSkill' ? owned[grant[1].toString()] as Map? : null;
          final source = recipe?['from'] ?? grant[1];
          final spec = replacements.where((r) => r['oldKind'] == grant[0] && r['oldSource'] == source).firstOrNull;
          if (spec == null) continue;
          final replacement = List<dynamic>.from(spec['newGrant'] as List);
          if (replacement[0] == 'ActiveSkill') {
            final identity = targetBase + (replacement[1] as int) - sourceBase;
            final key = '${replacement[0]}:${spec['source']}';
            if (inserted.containsKey(key)) {
              tier[i] = List<dynamic>.from(inserted[key]!);
              continue;
            }
            final value = CharacterConfig.copy(template['skills'][identity.toString()] as Map<String, dynamic>);
            final same = owned.entries.where((e) => (e.value as Map)['from'] == spec['source']).firstOrNull;
            int target;
            if (same != null) {
              target = int.parse(same.key.toString());
            } else {
              final occupied = {for (final k in owned.keys) for (final offset in [0, 1, 2]) int.parse(k.toString()) + offset};
              target = [identity, for (var n = 1; n < 32; n++) targetBase + n * 3]
                  .firstWhere((id) => [id, id + 1, id + 2].every((v) => !occupied.contains(v)));
              value['jp'] = '${value['jp']}_MR5_$target';
              owned[target.toString()] = value;
            }
            replacement[1] = target;
            inserted[key] = replacement;
          }
          tier[i] = replacement;
        }
      }
    }
    final learned = {for (final field in ['awakening', 'synchro'])
      for (final tier in unit[field] as List) for (final g in tier as List)
        if (g[0] == 'ActiveSkill') g[1]};
    owned.removeWhere((id, recipe) => !learned.contains(int.parse(id.toString())) &&
        replacements.any((r) => r['oldKind'] == 'ActiveSkill' && r['oldSource'] == (recipe as Map)['from']));
    unit['sephiraPassiveText'] = {
      ...?unit['sephiraPassiveText'] as Map?, ...?template['sephiraPassiveText'] as Map?,
    };
  }
}
