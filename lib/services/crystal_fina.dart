import 'dart:convert';

typedef UnitMap = Map<String, dynamic>;

class CrystalFina {
  static const presetId = 'custom.crystal_fina.v1';
  static const spriteId = '99887755552703';
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

  static UnitMap instantiate(UnitMap profile, List<dynamic> roster) {
    if (roster.any((u) => matches(u as Map))) { throw StateError('Crystal Fina is already in your roster.'); }
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
