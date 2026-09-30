import 'dart:convert';

/// A portable snapshot of the complete engine spec, including advanced fields.
/// Artwork stays in the Studio cache when a vision is removed.
class CharacterConfig {
  static const format = 'FFR Vision Studio character config';
  static const maxBytes = 16 * 1024 * 1024;

  static Map<String, dynamic> copy(Map<String, dynamic> unit) =>
      json.decode(json.encode(unit)) as Map<String, dynamic>;

  static String encode(Map<String, dynamic> unit) {
    validate(unit);
    return '${const JsonEncoder.withIndent('  ').convert({'format': format, 'version': 1, 'unit': unit})}\n';
  }

  static Map<String, dynamic> decode(String contents) {
    final document = json.decode(contents);
    if (document is! Map ||
        document['format'] != format ||
        document['version'] != 1 ||
        document['unit'] is! Map<String, dynamic>) {
      throw const FormatException(
        'Choose a character config saved by Studio (version 1).',
      );
    }
    final unit = document['unit'] as Map<String, dynamic>;
    validate(unit);
    return copy(unit);
  }

  static void validate(Map<String, dynamic> unit) {
    Never invalid() => throw const FormatException(
      'This character config is incomplete or invalid. Your roster has not been changed.',
    );
    bool integer(dynamic value) => value is int && value > 0;
    for (final field in ['key', 'jp', 'en', 'desc', 'attackType']) {
      if (unit[field] is! String) {
        invalid();
      }
    }
    if (!RegExp(r'^[a-zA-Z0-9_-]+$').hasMatch(unit['key'] as String) ||
        (unit['en'] as String).isEmpty) {
      invalid();
    }
    for (final field in ['id', 'sort', 'donor', 'lb']) {
      if (!integer(unit[field])) {
        invalid();
      }
    }
    if (unit['price'] is! num ||
        unit['roles'] is! List ||
        !(unit['roles'] as List).every((v) => v is String) ||
        unit['elemRes'] is! Map) {
      invalid();
    }
    final ffbe = unit['ffbe'];
    if (ffbe is! Map || ffbe['id'] is! String || ffbe['dir'] is! String) {
      invalid();
    }
    final directory = (ffbe['dir'] as String).replaceAll('\\', '/');
    if (!directory.startsWith('units/') ||
        directory.contains(':') ||
        directory.split('/').any((v) => v.isEmpty || v == '..' || v == '.')) {
      invalid();
    }
    for (final field in ['command', 'master']) {
      final definition = unit[field];
      if (definition is! Map ||
          !integer(definition['id']) ||
          definition['en'] is! String ||
          definition['desc'] is! String) {
        invalid();
      }
    }
    final stats = unit['stats'];
    if (stats is! Map) {
      invalid();
    }
    for (final field in [
      'MaxHitPoint',
      'MaxMagicPoint',
      'Attack',
      'Defence',
      'Intelligence',
      'Mind',
      'Agility',
    ]) {
      if (stats[field] is! num) {
        invalid();
      }
    }
    for (final field in ['awakening', 'synchro']) {
      final tiers = unit[field];
      if (tiers is! List || tiers.isEmpty) {
        invalid();
      }
      for (final tier in tiers) {
        if (tier is! List) {
          invalid();
        }
        for (final grant in tier) {
          if (grant is! List ||
              grant.length < 2 ||
              grant[0] is! String ||
              !integer(grant[1]) ||
              (grant.length > 2 && grant[2] is! num)) {
            invalid();
          }
        }
      }
    }
    final skills = unit['skills'];
    if (skills is! Map) {
      invalid();
    }
    final base = skillBase(unit['id'] as int);
    for (final entry in skills.entries) {
      final id = int.tryParse(entry.key.toString());
      final skill = entry.value;
      if (id == null ||
          id < base ||
          id >= base + 100 ||
          skill is! Map ||
          !integer(skill['from']) ||
          skill['jp'] is! String ||
          skill['en'] is! String ||
          skill['desc'] is! String ||
          (skill['set'] != null && skill['set'] is! Map)) {
        invalid();
      }
    }
    final lb = unit['lb_custom'];
    if (lb != null &&
        (lb is! Map ||
            !integer(lb['from']) ||
            lb['jp'] is! String ||
            lb['en'] is! String ||
            lb['desc'] is! String ||
            (lb['set'] != null && lb['set'] is! Map))) {
      invalid();
    }
    if (unit['ffbeMap'] != null &&
        (unit['ffbeMap'] is! Map ||
            (unit['ffbeMap'] as Map).values.any((v) => v is! Map))) {
      invalid();
    }
  }

  static int skillBase(int id) => 445000 + (id - 13100) * 100;
  static int resonanceId(int id) => 440000 + (id - 13099) * 10;

  static bool sameCharacter(Map saved, Map current) {
    final a = saved['ffbe'] as Map?, b = current['ffbe'] as Map?;
    if (a == null || b == null) {
      return false;
    }
    if (a['source'] != null &&
        b['source'] != null &&
        a['source'] != b['source']) {
      return false;
    }
    return (a['base'] ?? a['id']).toString() ==
        (b['base'] ?? b['id']).toString();
  }

  /// Prefer the original roster entry, then a re-added entry of the same form.
  /// Never apply a file to an unrelated selected character or silently choose
  /// between multiple copies of the same character.
  static Map<String, dynamic>? target(
    Map<String, dynamic> saved,
    List<dynamic> roster,
  ) {
    final candidates = roster
        .cast<Map<String, dynamic>>()
        .where((u) => sameCharacter(saved, u))
        .toList();
    final exact = candidates.where((u) => u['key'] == saved['key']).toList();
    if (exact.length == 1) {
      return exact.single;
    }
    final sameForm = candidates
        .where((u) => u['ffbe']['id'] == saved['ffbe']['id'])
        .toList();
    if (sameForm.length == 1) {
      return sameForm.single;
    }
    if (candidates.length == 1) {
      return candidates.single;
    }
    if (candidates.isNotEmpty) {
      throw StateError(
        'More than one copy of this character is in the roster. Remove the duplicate before loading this config.',
      );
    }
    return null;
  }

  static Map<String, dynamic> restore(
    Map<String, dynamic> saved,
    List<dynamic> roster, {
    Map<String, dynamic>? replacing,
  }) {
    validate(saved);
    final other = roster
        .cast<Map<String, dynamic>>()
        .where((u) => u['key'] != replacing?['key'])
        .toList();
    final result = copy(saved);
    final oldId = saved['id'] as int;
    final owned = (saved['skills'] as Map).keys
        .map((v) => int.parse(v.toString()))
        .toList();
    final visionIds = <int>{},
        commandIds = <int>{},
        masterIds = <int>{},
        skillIds = <int>{};
    for (final unit in other) {
      visionIds.add(unit['id'] as int);
      commandIds.add(unit['command']['id'] as int);
      masterIds.add(unit['master']['id'] as int);
      skillIds.addAll(
        (unit['skills'] as Map).keys.map((v) => int.parse(v.toString())),
      );
      if (unit['lb_custom'] != null) {
        skillIds.add(resonanceId(unit['id'] as int));
      }
    }
    bool free(int id) =>
        !visionIds.contains(id) &&
        !commandIds.contains(
          id == oldId ? saved['command']['id'] : 320 + id - 13500,
        ) &&
        !masterIds.contains(id == oldId ? saved['master']['id'] : id * 100) &&
        (saved['lb_custom'] == null || !skillIds.contains(resonanceId(id))) &&
        owned.every(
          (v) => !skillIds.contains(skillBase(id) + v - skillBase(oldId)),
        );
    var id = replacing?['id'] as int? ?? oldId;
    if (!free(id)) {
      id = visionIds.fold(13499, (a, b) => a > b ? a : b) + 1;
      while (!free(id)) {
        id++;
      }
    }
    if (id != oldId) {
      final remap = {
        for (final v in owned) v: skillBase(id) + v - skillBase(oldId),
      };
      if (saved['lb_custom'] != null) {
        remap[resonanceId(oldId)] = resonanceId(id);
      }
      final oldMaster = saved['master']['id'];
      result['id'] = id;
      result['sort'] = (saved['sort'] as int) + id - oldId;
      result['command']['id'] = 320 + id - 13500;
      result['master']['id'] = id * 100;
      result['skills'] = {
        for (final v in owned) '${remap[v]}': result['skills']['$v'],
      };
      for (final tiers in [result['awakening'], result['synchro']]) {
        for (final tier in tiers as List) {
          for (final grant in tier as List) {
            if (grant[0] == 'ActiveSkill' && remap.containsKey(grant[1])) {
              grant[1] = remap[grant[1]];
            }
            if (grant[0] == 'MasterSkill' && grant[1] == oldMaster) {
              grant[1] = id * 100;
            }
          }
        }
      }
      final mapping = (result['ffbeMap'] as Map?)?['skills'] as Map?;
      if (mapping != null) {
        for (final key in mapping.keys.toList()) {
          if (remap.containsKey(mapping[key])) {
            mapping[key] = remap[mapping[key]];
          }
        }
      }
      if (result['lb'] == resonanceId(oldId) && saved['lb_custom'] != null) {
        result['lb'] = resonanceId(id);
      }
    }
    var key = replacing?['key'] as String? ?? saved['key'] as String;
    final taken = other.map((u) => u['key']).toSet();
    final original = key;
    for (var suffix = 2; taken.contains(key); suffix++) {
      key = '${original}_$suffix';
    }
    result['key'] = key;
    // The builder uses JP names as table row keys, including custom moves.
    // A conflicting internal row name must be unique as well as its numeric ID.
    String rowName(String original, Set<String> used) {
      var name = original;
      for (var suffix = 2; used.contains(name); suffix++) {
        name = '${original}_$suffix';
      }
      used.add(name);
      return name;
    }

    result['jp'] = rowName(
      result['jp'] as String,
      other.map((u) => u['jp'] as String).toSet(),
    );
    final usedSkills = <String>{
      for (final u in other) ...[
        for (final s in (u['skills'] as Map).values) s['jp'] as String,
        if (u['lb_custom'] != null) u['lb_custom']['jp'] as String,
      ],
    };
    for (final definition in (result['skills'] as Map).values) {
      definition['jp'] = rowName(definition['jp'] as String, usedSkills);
    }
    if (result['lb_custom'] != null) {
      result['lb_custom']['jp'] = rowName(
        result['lb_custom']['jp'] as String,
        usedSkills,
      );
    }
    return result;
  }
}
