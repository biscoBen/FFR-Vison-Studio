import 'catalog_source_reference.dart';

/// Plain-language readings of the engine's catalog rows, mirroring tools/devui/web/src/api.ts `describe` and Easy.tsx.
const cgResonanceIds = {440010, 440090, 440110};

/// The catalog falls back to source names for untranslated entries. Keep Latin
/// names and English punctuation, including accented names and apostrophes.
bool catalogNameIsEnglish(dynamic value) {
  final name = (value ?? '').toString().trim();
  return RegExp(r'[A-Za-z]').hasMatch(name) &&
      !RegExp(r'[\u0370-\u052f\u0590-\u06ff\u0900-\u0e7f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\uf900-\ufaff]').hasMatch(name);
}

/// Selection filters do not remove full catalog rows or existing saved grants.
List<Map<String, dynamic>> catalogSelectableLibrary(
  Map<String, dynamic> catalog,
  String kind,
  Iterable<dynamic> roster,
) {
  final resonanceIds = {
    for (final vision in catalog['visions'] as List? ?? [])
      if (vision['finishBlow'] is num) vision['finishBlow'],
  };
  return catalogLibrary(catalog, kind, roster).where((row) {
    if (!catalogNameIsEnglish(row['name'])) return false;
    if (kind == 'skills' &&
        (row['name'].toString().trim().toLowerCase() == 'attack' ||
            row['attr'].toString().split('::').last == 'FinishBlow' ||
            resonanceIds.contains(row['id']))) {
      return false;
    }
    return true;
  }).toList();
}

/// Collapse only duplicates proven to have identical extracted game mechanics.
/// Prefer verified combat matches unless a default vision or current roster uses
/// the unverified ID. Original game rows and equipped-ID lookups stay intact.
/// The full catalog stays intact for saved configs and equipped-ID lookups.
List<Map<String, dynamic>> catalogLibrary(
  Map<String, dynamic> catalog,
  String kind,
  Iterable<dynamic> roster,
) {
  final entries = ((catalog[kind] as List?) ?? [])
      .map((e) => Map<String, dynamic>.from(e as Map))
      .toList();
  final policy = catalog['duplicatePolicy'] as Map?;
  if (![1, 2].contains(policy?['schema']) || policy?['available'] != true) {
    return entries;
  }
  if (policy?['schema'] == 2 && policy?['ownersComplete'] != true) {
    return entries;
  }
  final protected = <num>{
    for (final id in ((policy?['protected'] as Map?)?[kind] as List? ?? []))
      if (id is num) id,
  };
  final equipped = <num>{};
  void retain(dynamic value) {
    if (value is num) {
      equipped.add(value);
    } else if (value is Map) {
      for (final v in value.values) {
        retain(v);
      }
    } else if (value is Iterable) {
      for (final v in value) {
        retain(v);
      }
    }
  }

  for (final unit in roster) {
    retain(unit);
  }
  protected.addAll(equipped);
  for (final entry in entries) {
    if (catalogDefaultOwners(catalog, kind, entry).isNotEmpty) {
      protected.add(entry['id'] as num);
    }
  }
  final byId = {for (final entry in entries) entry['id'] as num: entry};
  final verifiedMatches = (policy?['verifiedMatches'] as Map?)?[kind] as Map?;
  final replaced = <num>{};
  if (kind == 'skills' && policy?['schema'] == 2) {
    for (final entry in entries) {
      final donors = ((verifiedMatches?['${entry['id']}'] as List?) ?? [])
          .whereType<num>()
          .where(
            (id) => byId[id] != null && catalogEntryVerified(byId[id]!, kind),
          )
          .toList();
      if (donors.isEmpty) continue;
      protected.addAll(donors);
      if (!catalogEntryVerified(entry, kind) &&
          !equipped.contains(entry['id']) &&
          catalogDefaultOwners(catalog, kind, entry).isEmpty) {
        replaced.add(entry['id'] as num);
      }
    }
  }
  final hidden = <num>{};
  for (final group in ((policy?['groups'] as Map?)?[kind] as List? ?? [])) {
    if (group is! List ||
        group.length < 2 ||
        group.any((id) => !byId.containsKey(id))) {
      continue;
    }
    final ids = group.cast<num>().toSet();
    final kept = ids.intersection(protected);
    if (kept.isEmpty) {
      final ranked = ids.toList()
        ..sort((a, b) {
          final aa = (byId[a]?['seq'] as List?)?.isNotEmpty == true ? 0 : 1;
          final bb = (byId[b]?['seq'] as List?)?.isNotEmpty == true ? 0 : 1;
          return aa != bb ? aa.compareTo(bb) : a.compareTo(b);
        });
      kept.add(ranked.first);
    }
    hidden.addAll(ids.difference(kept));
  }
  return entries
      .where((e) => !hidden.contains(e['id']) && !replaced.contains(e['id']))
      .toList();
}

bool catalogEntryVerified(Map row, String kind) {
  if (row['custom'] == true) return true;
  final name = (row['name'] ?? '').toString();
  if (kind == 'passives') {
    return name.isNotEmpty && !RegExp(r'[぀-ヿ一-鿿]').hasMatch(name);
  }
  return (row['seq'] as List?)?.isNotEmpty == true &&
      row['hasUnit'] == 'All' &&
      ['Ability', 'Magic', 'MagicSword'].contains(row['attr']) &&
      row['id'] is num &&
      (row['id'] as num) < 460000;
}

List<String> catalogDefaultOwners(
  Map<String, dynamic> catalog,
  String kind,
  Map row,
) {
  final owners = <String>{
    for (final name
        in (((catalog['duplicatePolicy'] as Map?)?['owners'] as Map?)?[kind]
                    as Map?)?['${row['id']}']
                as List? ??
            [])
      if (name is String && name.isNotEmpty) name,
  };
  for (final vision in catalog['visions'] as List? ?? []) {
    final name = (vision['name'] ?? '').toString();
    if (name.isEmpty) continue;
    if (kind == 'skills' &&
        (vision['finishBlow'] == row['id'] || row['hasUnit'] == name)) {
      owners.add(name);
    }
    for (final field in ['awakening', 'synchro']) {
      for (final tier in vision[field] as List? ?? []) {
        for (final grant in tier as List) {
          if (grant is List &&
              grant.length >= 2 &&
              grant[0] == (kind == 'skills' ? 'ActiveSkill' : 'PassiveSkill') &&
              grant[1] == row['id']) {
            owners.add(name);
          }
        }
      }
    }
  }
  return owners.toList()..sort();
}

String catalogEntryTitle(Map<String, dynamic> catalog, String kind, Map row, {bool? verified}) {
  final name = (row['name'] ?? '').toString();
  final label = name.isEmpty
      ? '${kind == 'skills' ? 'skill' : 'passive'} ${row['id']}'
      : name;
  final owners = catalogDefaultOwners(catalog, kind, row);
  final unverified = !(verified ?? catalogEntryVerified(row, kind));
  final reference = row['custom'] == true
      ? null
      : catalogSourceReferences[kind]?[row['id']];
  final confirmedSources = {
    if (unverified) ...owners,
    for (final name in ((((catalog['duplicatePolicy'] as Map?)?['sources'] as Map?)?[kind] as Map?)?['${row['id']}'] as List? ?? []))
      if (catalogNameIsEnglish(name)) name.toString(),
    if (reference != null && !reference.internalLabelOnly) reference.owner,
  };
  final sources = {
    ...confirmedSources,
    if (reference != null) reference.owner,
  }.toList()..sort();
  final sourceLabels = sources.map((name) =>
      reference?.internalLabelOnly == true &&
              name == reference!.owner && !confirmedSources.contains(name)
          ? '$name (internal label only)'
          : name);
  final awakening = reference?.awakening;
  return '$label${unverified ? ' (Unverified)' : ''}'
      '${sources.isNotEmpty ? ' — Source: ${sourceLabels.join(', ')}' : ''}'
      '${awakening != null ? '; awakening=$awakening${sources.length > 1 ? ' (${reference!.owner})' : ''}' : ''}';
}

Map<String, dynamic> migrateCgResonance(Map<String, dynamic> unit) {
  final lb = unit['lb_custom'] as Map?;
  if (unit['ffbe'] != null && lb != null &&
      cgResonanceIds.contains(lb['visuals'] ?? lb['from']) && lb['presentation'] != 'ffbe') {
    return {...unit, 'lb_custom': {...lb, 'presentation': 'ffbe'}};
  }
  return unit;
}

const targetText = <String, String>{
  'Single|Enemies': 'one enemy', 'Group|Enemies': 'all enemies', 'Random|Enemies': 'random enemies', 'Spread|Enemies': 'enemies in a line',
  'SingleAndGroup|Enemies': 'one enemy, then all', 'Single|Friendlies': 'one ally', 'Group|Friendlies': 'all allies', 'Self|Friendlies': 'self', 'Self|Enemies': 'self',
};

String describe(Map<String, dynamic>? row, [Map<String, dynamic> o = const {}]) {
  if (row == null) return '';
  final dmg = o['DamageType'] ?? row['dmgType'];
  final target = o['TargetType'] ?? row['target'];
  final rel = row['relation'];
  final element = o['element'] ?? row['element'];
  final hits = (o['hitCount'] ?? row['hits'] ?? 1) as num;
  final mag = (o['magnification'] ?? row['mag'] ?? 0) as num;
  final brk = (o['breakDamageValue'] ?? row['breakDmg'] ?? 0) as num;
  final who = targetText['$target|$rel'] ?? '$target $rel'.toLowerCase();
  final el = (element == null || element == 'None') ? '' : '$element ';
  String s;
  if ((dmg == 'Physic' || dmg == 'Magic') && mag > 0) {
    s = 'Deal $el${dmg == 'Physic' ? 'physical' : 'magic'} damage to $who';
    if (hits > 1) s += ' ($hits hits)';
  } else if (row['effectType'] == 'DamageAndRecovery' && rel == 'Friendlies') {
    s = 'Restore HP to $who';
  } else if (brk > 0 && mag == 0) {
    s = 'Break attack on $who (no damage)';
  } else {
    s = '${row['name'] ?? 'Effect'} on $who';
  }
  if (brk >= 9999) {
    s += ', staggers instantly';
  } else if (brk >= 40) {
    s += ', high break power';
  }
  return '$s.';
}

/// What a skill-effect row does, for the handful of types the shipped Resonances use.
String? effectLabel(Map<String, dynamic>? e) {
  if (e == null) return null;
  final p = ((e['params'] as List?) ?? const []).cast<num>();
  num at(int i) => i < p.length ? p[i] : 0;
  switch (e['type']) {
    case 'Deffence':
      return at(0) == 1 ? 'Protect: physical defence +${at(1)}%' : at(0) == 2 ? 'Shell: magic defence +${at(1)}%' : 'Cuts the next hit by ${at(1)}%';
    case 'CureStatusCondition':
      return at(1) == 1 ? 'Dispels buffs on the target' : 'Cures status ailments';
    case 'OverHeal':
      return 'Healing can exceed max HP';
    case 'ParameterVariation':
      final st = e['status'];
      return (st != null && st != 'None') ? 'Inflicts $st (${at(0)}% per turn, ${at(2)} turns)' : 'Changes a stat';
    case 'AccuracyVariation':
      return '${e['status'] ?? 'Accuracy'}: accuracy ${at(0)}%';
    case 'InstantDeath':
      return '${e['prob']}% chance of instant death';
    case 'Steal':
      return 'Steals an item';
    case 'CritMul':
      return 'Critical damage +${at(0)}%';
    case 'MulBaseSkillByLevel':
    case 'AppendDamage':
    case 'DmgMulSpecificSkill':
      return null;
    default:
      return e['type']?.toString();
  }
}

String iconTagFor(Map<String, dynamic> cat, String element, bool physical, bool supportive) {
  final icons = (cat['icons'] as List).cast<Map<String, dynamic>>();
  bool has(String t) => icons.any((i) => i['tag'] == t);
  if (supportive) return has('UI.Skill.Action.Icon.Support') ? 'UI.Skill.Action.Icon.Support' : 'UI.Skill.Action.Icon.Heal';
  if (element != 'None' && has('UI.Skill.Action.Icon.$element')) return 'UI.Skill.Action.Icon.$element';
  return 'UI.Skill.Action.Icon.Attack';
}

/// PNG file name of an icon tag, or null.
String? iconPng(Map<String, dynamic>? cat, String? tag) {
  if (cat == null || tag == null) return null;
  for (final i in (cat['icons'] as List).cast<Map<String, dynamic>>()) {
    if (i['tag'] == tag) return i['png'] as String?;
  }
  return null;
}

String? ownerOf(Map<String, dynamic> cat, num finishBlow) {
  for (final v in (cat['visions'] as List).cast<Map<String, dynamic>>()) {
    if (v['finishBlow'] == finishBlow) return v['name'] as String?;
  }
  return null;
}

const statParams = <(int, String, int)>[(1, 'HP', 50), (2, 'MP', 10), (5, 'Attack', 5), (6, 'Defence', 5), (7, 'Intelligence', 5), (8, 'Mind', 5), (9, 'Agility', 3)];
const statFields = <(String, String, int, int)>[('MaxHitPoint', 'HP', 200, 3000), ('MaxMagicPoint', 'MP', 30, 400), ('Attack', 'Attack', 5, 120), ('Defence', 'Defence', 5, 120), ('Intelligence', 'Intelligence', 5, 120), ('Mind', 'Mind', 5, 120), ('Agility', 'Agility', 5, 120)];
const elements = ['None', 'Fire', 'Ice', 'Wind', 'Earth', 'Thunder', 'Water', 'Light', 'Dark'];
const roles = <(String, String)>[('eUnitRole::Attacker', 'Attacker'), ('eUnitRole::Breaker', 'Breaker'), ('eUnitRole::Defender', 'Defender'), ('eUnitRole::Healer', 'Healer'), ('eUnitRole::Enhancer', 'Enhancer'), ('eUnitRole::Jammer', 'Jammer')];
const tierCap = 8;

/// Brave Exvius rarity: 1..7 are stars, then NV and NV+ (and EX) as written.
String rarityLabel(dynamic r) {
  if (r == null) return '-';
  final s = r.toString();
  return int.tryParse(s) != null ? '$s★' : s;
}

String rarityRange(dynamic lo, dynamic hi) => lo == null && hi == null ? '' : (lo == hi || hi == null ? rarityLabel(lo) : '${rarityLabel(lo)} → ${rarityLabel(hi)}');

const _animOrder = ['idle', 'standby', 'move', 'jump', 'atk', 'magicatk', 'magic_atk', 'limitatk', 'limit_atk', 'limitmove', 'limit_move', 'magic_standby', 'win', 'winbefore', 'win_before', 'dying', 'dead'];
List<String> orderAnims(List<String> a) => [..._animOrder.where(a.contains), ...(a.where((x) => !_animOrder.contains(x)).toList()..sort())];

/// " · Brave Shift" / " · Super Limit Break" for a shifted look, else nothing.
String shiftLabel(dynamic sh) => sh == null ? '' : (sh['kind'] == 'brave_shift' ? ' · Brave Shift' : ' · Super Limit Break');
