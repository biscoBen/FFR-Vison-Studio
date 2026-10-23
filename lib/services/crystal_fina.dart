import 'dart:convert';
import 'character_config.dart';

typedef UnitMap = Map<String, dynamic>;

class CrystalFina {
  static const presetId = 'custom.crystal_fina.v1';
  static const spriteId = '99887755552703';
  static const previewVersion = 'native-fina-10';
  static const previewCaption = 'Native battle preview · game lighting may differ';
  static const assetRoot = 'assets/crystal_fina';
  static const iconAsset = '$assetRoot/units/custom/crystal_fina_2/sprites/$spriteId/unit_icon_$spriteId.png';
  static const entry = <String, dynamic>{
    'id': presetId, 'bundledPreset': presetId, 'name': 'Crystal Fina',
    'hasSprites': true, 'iconForm': spriteId, 'packs': [spriteId],
    'rarity_min': 'NV', 'rarity_max': 'NV', 'roles': ['Healer'],
  };

  static bool matches(Map unit) => unit['bundledPreset'] == presetId ||
      unit['key'] == 'crystal_fina_2' ||
      (unit['ffbe'] is Map && [unit['ffbe']['id']?.toString(), unit['ffbe']['base']?.toString()].contains(spriteId));

  /// Recognize only the shipped, obsolete stat-only layout. Deliberately edited
  /// rewards, original-game overrides and party replacements are not migrated.
  static bool needsRewardRepair(Map unit) {
    if (!matches(unit) || unit['native'] != null || unit['party'] != null) return false;
    final tiers = unit['synchro'];
    if (tiers is! List || tiers.length != 10) return false;
    final normalized = [for (final tier in tiers)
      if (tier is List) [for (final grant in tier)
        if (grant is List && grant.length >= 2 && grant.length <= 3 &&
            (grant.length == 2 || grant[2] == -1 || grant[0] == 'BaseParameter'))
          grant[0] == 'MasterSkill' && grant[1] == unit['master']?['id']
              ? ['MasterSkill', 0] : grant.take(3).toList()
        else null]
      else null];
    return json.encode(normalized) == json.encode([
      [], [['BaseParameter', 1, 50]], [['BaseParameter', 5, 5]],
      [['BaseParameter', 6, 5]], [['BaseParameter', 2, 10]],
      [['BaseParameter', 7, 5]], [['BaseParameter', 8, 5]],
      [['BaseParameter', 9, 3]], [['BaseParameter', 1, 50]],
      [['BaseParameter', 5, 8], ['BaseParameter', 11, 8], ['MasterSkill', 0]],
    ]);
  }

  static UnitMap repairRewards(UnitMap unit, UnitMap currentProfile) {
    if (!needsRewardRepair(unit)) return unit;
    final template = CharacterConfig.restore(currentProfile, [], replacing: unit);
    final result = CharacterConfig.copy(unit);
    final rewards = template['synchro'] as List;
    final owned = result['skills'] as Map;
    for (final tier in rewards) {
      for (final grant in tier as List) {
        if (grant[0] == 'MasterSkill') grant[1] = unit['master']['id'];
        if (grant[0] != 'ActiveSkill') continue;
        final recipe = CharacterConfig.copy(template['skills'][grant[1].toString()] as UnitMap);
        final existing = owned.entries.where((e) => e.value['from'] == recipe['from'] &&
            e.value['en'] == recipe['en']).firstOrNull;
        if (existing != null) { grant[1] = int.parse(existing.key.toString()); continue; }
        final occupied = {for (final key in owned.keys)
          for (final offset in [0, 1, 2]) int.parse(key.toString()) + offset};
        final base = CharacterConfig.skillBase(unit['id'] as int);
        final target = [grant[1] as int, for (var i = 1; i < 32; i++) base + i * 3]
            .firstWhere((id) => [id, id + 1, id + 2].every((v) => !occupied.contains(v)));
        recipe['jp'] = '${unit['jp']}_MR_Repair_$target';
        for (final field in ['belongCommandList', 'commandIdBelongDebuggingAllSkills']) {
          recipe['set'][field] = [for (final value in recipe['set'][field] as List)
            value == template['command']['id'] ? unit['command']['id'] : value];
        }
        owned[target.toString()] = recipe;
        grant[1] = target;
      }
    }
    final moved = {for (final tier in rewards) for (final g in tier)
      if (g[0] == 'ActiveSkill' || g[0] == 'PassiveSkill') '${g[0]}:${g[1]}'};
    result['awakening'] = [for (final tier in result['awakening'] as List)
      [for (final g in tier as List) if (!moved.contains('${g[0]}:${g[1]}')) g]];
    result['synchro'] = rewards;
    result['sephiraPassiveText'] = {
      ...?result['sephiraPassiveText'] as Map?, ...template['sephiraPassiveText'] as Map,
    };
    result['sephiraRecipe'] = template['sephiraRecipe'];
    CharacterConfig.validate(result);
    return result;
  }

  static UnitMap instantiate(UnitMap profile, List<dynamic> roster) {
    if (roster.any((u) => u['native'] == null && u['party'] == null && matches(u as Map))) { throw StateError('Crystal Fina is already in your roster.'); }
    final visions = <int>{}, commands = <int>{}, masters = <int>{}, skills = <int>{};
    for (final unit in roster.cast<Map>()) {
      if (unit['id'] is num) {
        final id = (unit['id'] as num).toInt();
        visions.add(id);
        if (unit['lb_custom'] != null) { skills.add(440000 + (id - 13099) * 10); }
      }
      if (unit['command']?['id'] is num) { commands.add((unit['command']['id'] as num).toInt()); }
      if (unit['master']?['id'] is num) { masters.add((unit['master']['id'] as num).toInt()); }
      skills.addAll(((unit['skills'] as Map?) ?? {}).keys.map((k) => int.parse(k.toString())));
    }
    final offsets = (profile['skills'] as Map).keys.map((key) => int.parse(key.toString()) - 485300).toList();
    bool free(int id) => !visions.contains(id) && !commands.contains(320 + id - 13500) &&
        !masters.contains(id * 100) && !skills.contains(440000 + (id - 13099) * 10) &&
        !offsets.any((offset) => skills.contains(445000 + (id - 13100) * 100 + offset));
    var id = 13503;
    if (!free(id)) {
      id = visions.where((id) => id >= 13500).fold(13499, (a, b) => a > b ? a : b) + 1;
      while (!free(id)) { id++; }
    }
    final result = json.decode(json.encode(profile)) as UnitMap;
    result['bundledPreset'] = presetId;
    if (id == 13503) { return result; }
    final remap = <int, int>{1350300: id * 100, 444040: 440000 + (id - 13099) * 10};
    final definitions = result['skills'] as UnitMap;
    final renamed = <String, dynamic>{};
    for (final entry in definitions.entries) {
      final old = int.parse(entry.key);
      final replacement = 445000 + (id - 13100) * 100 + (old - 485300);
      remap[old] = replacement;
      renamed['$replacement'] = entry.value;
    }
    result['skills'] = renamed;
    for (final recipe in renamed.values) {
      for (final field in ['belongCommandList', 'commandIdBelongDebuggingAllSkills']) {
        final commands = recipe['set']?[field];
        if (commands is List) {
          recipe['set'][field] = [for (final value in commands)
            value == profile['command']['id'] ? 320 + id - 13500 : value];
        }
      }
    }
    for (final tiers in [result['awakening'], result['synchro']]) {
      for (final tier in tiers as List) {
        for (final grant in tier as List) {
          if (['ActiveSkill', 'MasterSkill'].contains(grant[0]) && remap.containsKey(grant[1])) { grant[1] = remap[grant[1]]; }
        }
      }
    }
    for (final mapping in ((result['ffbeMap'] as Map?) ?? {}).values.whereType<Map>()) {
      for (final key in mapping.keys.toList()) {
        if (remap.containsKey(mapping[key])) { mapping[key] = remap[mapping[key]]; }
      }
    }
    result['id'] = id;
    result['sort'] = id + 70;
    result['command']['id'] = 320 + id - 13500;
    result['master']['id'] = id * 100;
    return result;
  }
}
