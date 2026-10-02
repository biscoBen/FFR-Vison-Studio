import 'dart:convert';

/// A portable snapshot of the complete engine spec, including advanced fields.
/// Artwork stays in the Studio cache when a vision is removed.
class CharacterConfig {
  static const format = 'FFR Vision Studio character config';
  static const allFormat = 'FFR Vision Studio character configs';
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

  static String encodeAll(List<dynamic> units) {
    validateAll(units);
    return '${const JsonEncoder.withIndent('  ').convert({'format': allFormat, 'version': 1, 'units': units})}\n';
  }

  static List<Map<String, dynamic>> decodeAll(String contents) {
    final document = json.decode(contents);
    if (document is! Map ||
        document['format'] != allFormat ||
        document['version'] != 1 ||
        document['units'] is! List) {
      throw const FormatException(
        'Choose a file made with Save all character configs (version 1).',
      );
    }
    final units = document['units'] as List;
    validateAll(units);
    return units.cast<Map<String, dynamic>>().map(copy).toList();
  }

  static void validateAll(List<dynamic> units) {
    if (units.isEmpty) {
      throw const FormatException('This file contains no character configs.');
    }
    final keys = <String>{},
        ids = <int>{},
        commands = <int>{},
        masters = <int>{},
        skills = <int>{};
    for (final unit in units) {
      if (unit is! Map<String, dynamic>) {
        throw const FormatException(
          'This file contains an invalid character config.',
        );
      }
      validate(unit);
      if (unit['party'] != null) {
        if (!keys.add(unit['key'] as String) || !ids.add(unit['id'] as int)) {
          throw const FormatException('Duplicate party character override.');
        }
        continue;
      }
      if (!keys.add(unit['key'] as String) ||
          !ids.add(unit['id'] as int) ||
          !commands.add(unit['command']['id'] as int) ||
          !masters.add(unit['master']['id'] as int) ||
          !(unit['skills'] as Map).keys.every(
            (id) => skills.add(int.parse(id.toString())),
          ) ||
          (unit['lb_custom'] != null &&
              !skills.add(resonanceId(unit['id'] as int)))) {
        throw const FormatException(
          'This file contains duplicate character or skill IDs. Your roster has not been changed.',
        );
      }
    }
  }

  /// Match every saved entry against the original roster before allocating IDs.
  /// Reserve exact entries first so a renamed/re-added duplicate cannot take
  /// the target belonging to another saved copy of the same character.
  static List<Map<String, dynamic>?> targets(
    List<Map<String, dynamic>> saved,
    List<dynamic> roster,
  ) {
    final result = List<Map<String, dynamic>?>.filled(saved.length, null);
    final used = <String>{};
    for (var i = 0; i < saved.length; i++) {
      final exact = roster
          .cast<Map<String, dynamic>>()
          .where(
            (u) => u['key'] == saved[i]['key'] && sameCharacter(saved[i], u),
          )
          .toList();
      if (exact.length == 1) {
        result[i] = exact.single;
        used.add(exact.single['key'] as String);
      }
    }
    for (var i = 0; i < saved.length; i++) {
      if (result[i] != null) {
        continue;
      }
      result[i] = target(
        saved[i],
        roster.where((u) => !used.contains(u['key'])).toList(),
      );
      if (result[i] != null) {
        used.add(result[i]!['key'] as String);
      }
    }
    return result;
  }

  static List<Map<String, dynamic>> restoreAll(
    List<Map<String, dynamic>> saved,
    List<dynamic> roster,
    List<Map<String, dynamic>?> replacing,
  ) {
    validateAll(saved);
    if (saved.length != replacing.length) {
      throw ArgumentError('One target is required for each config.');
    }
    final targetKeys = replacing.whereType<Map>().map((u) => u['key']).toSet();
    final other = roster
        .cast<Map<String, dynamic>>()
        .where((u) => !targetKeys.contains(u['key']))
        .toList();
    // Reserve the preferred IDs of later characters so an earlier collision
    // cannot unnecessarily displace another saved or re-added character.
    final reserved = [
      for (var i = 0; i < saved.length; i++)
        restore(saved[i], [], replacing: replacing[i]),
    ];
    // Existing characters keep their current IDs ahead of a missing character
    // whose old ID has since been reused by one of them.
    final existingReservations = [
      for (var i = 0; i < saved.length; i++)
        if (replacing[i] != null) reserved[i],
    ];
    final reserve = [
      for (var i = 0; i < saved.length; i++)
        replacing[i] != null ||
            restore(reserved[i], existingReservations)['id'] ==
                reserved[i]['id'],
    ];
    final loaded = <Map<String, dynamic>>[];
    for (var i = 0; i < saved.length; i++) {
      loaded.add(
        restore(saved[i], [
          ...other,
          ...loaded,
          for (var j = i + 1; j < reserved.length; j++)
            if (reserve[j]) reserved[j],
        ], replacing: replacing[i]),
      );
    }
    final activeIds = <int, int>{}, masterIds = <int, int>{};
    for (var i = 0; i < saved.length; i++) {
      if (saved[i]['party'] != null) { continue; }
      final oldId = saved[i]['id'] as int, newId = loaded[i]['id'] as int;
      masterIds[saved[i]['master']['id'] as int] =
          loaded[i]['master']['id'] as int;
      for (final key in (saved[i]['skills'] as Map).keys) {
        final id = int.parse(key.toString());
        activeIds[id] = skillBase(newId) + id - skillBase(oldId);
      }
      if (saved[i]['lb_custom'] != null) {
        activeIds[resonanceId(oldId)] = resonanceId(newId);
      }
    }
    // Use the original references once, rather than remapping an already
    // remapped value that happens to equal another character's previous ID.
    for (var i = 0; i < saved.length; i++) {
      if (saved[i]['party'] != null) { continue; }
      final original = copy(saved[i]);
      for (final field in ['awakening', 'synchro']) {
        for (final tier in original[field] as List) {
          for (final grant in tier as List) {
            final ids = grant[0] == 'ActiveSkill'
                ? activeIds
                : grant[0] == 'MasterSkill'
                ? masterIds
                : const <int, int>{};
            if (ids.containsKey(grant[1])) {
              grant[1] = ids[grant[1]];
            }
          }
        }
        loaded[i][field] = original[field];
      }
      final mapping = (original['ffbeMap'] as Map?)?['skills'] as Map?;
      if (mapping != null) {
        for (final key in mapping.keys.toList()) {
          if (activeIds.containsKey(mapping[key])) {
            mapping[key] = activeIds[mapping[key]];
          }
        }
        loaded[i]['ffbeMap'] = original['ffbeMap'];
      }
      if (activeIds.containsKey(original['lb'])) {
        loaded[i]['lb'] = activeIds[original['lb']];
      }
    }
    return loaded;
  }

  static void validate(Map<String, dynamic> unit) {
    Never invalid() => throw const FormatException(
      'This character config is incomplete or invalid. Your roster has not been changed.',
    );
    if (unit['party'] != null) {
      const names = ['Rain', 'Lasswell', 'Fina', 'Lid', 'Nichol', 'Dark Fina', 'Jake', 'Sakura'];
      const jp = ['レイン', 'ラスウェル', 'フィーナ', 'リド', 'ニコル', '魔人フィーナ', 'ジェイク', 'サクラ'];
      final id = unit['id'];
      if (id is! int || id < 1001 || id > 1008 || unit['key'] != 'party_$id' ||
          unit['en'] != names[id - 1001] || unit['jp'] != jp[id - 1001] ||
          unit['party'] is! Map || unit['party']['version'] != 1 || unit['party']['id'] != id ||
          (unit['party'] as Map).length != 2 ||
          unit.keys.any((k) => !['key', 'id', 'jp', 'en', 'party', 'ffbe', 'menuScale', 'icon'].contains(k))) { invalid(); }
      final ffbe = unit['ffbe'];
      if (ffbe != null) {
        if (ffbe is! Map || ffbe['id'] is! String || !RegExp(r'^\d+$').hasMatch(ffbe['id'].toString())) { invalid(); }
        for (final field in ['dir', 'baseDir']) {
          final path = ffbe[field];
          if (field == 'dir' && path == null) { invalid(); }
          if (path != null && (path is! String || !path.startsWith('units/') ||
              path.contains('\\') || path.contains(':') || path.split('/').contains('..'))) { invalid(); }
        }
      }
      if (ffbe is Map && ffbe['baseDir'] != null && !RegExp(r'^\d+$').hasMatch(ffbe['baseForm'].toString())) { invalid(); }
      return;
    }
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
    final native = unit['native'];
    if (native != null &&
        (native is! Map ||
            native['version'] != 1 ||
            native['id'] != unit['id'] ||
            native['baseline'] is! Map ||
            native['baseline']['id'] != unit['id'] ||
            native['baseline']['native'] != null ||
            unit['donor'] != unit['id'] ||
            unit['lb_custom'] != null)) {
      invalid();
    }
    if (native != null) {
      final baseline = Map<String, dynamic>.from(native['baseline'] as Map);
      // Validate the complete original snapshot without requiring custom artwork.
      validate({
        ...baseline,
        'ffbe': baseline['ffbe'] ?? {'id': '0', 'dir': 'units/original'},
      });
      for (final field in ['command', 'master']) {
        if (unit[field] is! Map || unit[field]['id'] != baseline[field]['id']) {
          invalid();
        }
      }
      for (final field in ['awakening', 'synchro']) {
        if (unit[field] is! List ||
            unit[field].length != baseline[field].length) {
          invalid();
        }
      }
      final caps = native['synchroCaps'];
      if (caps is! List ||
          caps.length != baseline['synchro'].length ||
          !caps.every((v) => v is int && v >= 0)) {
        invalid();
      }
    }
    if ((native == null || ffbe != null) &&
        (ffbe is! Map || ffbe['id'] is! String || ffbe['dir'] is! String)) {
      invalid();
    }
    for (final field in ['dir', 'baseDir']) {
      if (ffbe == null || ffbe[field] == null) continue;
      if (ffbe[field] is! String) invalid();
      final directory = (ffbe[field] as String).replaceAll('\\', '/');
      if (!directory.startsWith('units/') ||
          directory.contains(':') ||
          directory.split('/').any((v) => v.isEmpty || v == '..' || v == '.')) {
        invalid();
      }
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
    if (saved['party'] != null || current['party'] != null) {
      return saved['party'] != null && current['party'] != null && saved['party']['id'] == current['party']['id'];
    }
    if (saved['native'] != null || current['native'] != null) {
      return saved['native'] != null &&
          current['native'] != null &&
          saved['native']['id'] == current['native']['id'];
    }
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
        .where(
          (u) =>
              saved['party'] != null || saved['native'] != null || u['ffbe']['id'] == saved['ffbe']['id'],
        )
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
    if (saved['native'] != null || saved['party'] != null) {
      if (other.any((u) => u['id'] == oldId || u['key'] == saved['key'])) {
        throw StateError(
          'This original vision has a conflicting roster entry. Its game ID cannot be reassigned.',
        );
      }
      if (replacing != null && replacing['id'] != oldId) {
        throw StateError('An original vision must keep its game ID.');
      }
      return result;
    }
    final owned = (saved['skills'] as Map).keys
        .map((v) => int.parse(v.toString()))
        .toList();
    final visionIds = <int>{},
        commandIds = <int>{},
        masterIds = <int>{},
        skillIds = <int>{};
    for (final unit in other) {
      visionIds.add(unit['id'] as int);
      if (unit['party'] != null) { continue; }
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
        for (final s in ((u['skills'] as Map?) ?? {}).values) s['jp'] as String,
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
