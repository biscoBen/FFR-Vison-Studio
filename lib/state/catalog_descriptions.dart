import 'dart:convert';

import 'catalog_helpers.dart';

const _fields = {
  'attr': 'skillAttrType',
  'effectType': 'skillEffectType',
  'dmgType': 'DamageType',
  'calcType': 'damageCalcType',
  'element': 'element',
  'target': 'TargetType',
  'relation': 'defaultTargetRelation',
  'cost': 'Cost',
  'mag': 'magnification',
  'breakDmg': 'breakDamageValue',
  'accuracy': 'accuracy',
  'hits': 'hitCount',
  'ratios': 'hitDamageRatioList',
  'hasUnit': 'hasUnit',
  'equipCost': 'equipCost',
};

const _labels = {
  'skillAttrType': 'Ability type',
  'skillEffectType': 'Effect type',
  'DamageType': 'Damage type',
  'damageCalcType': 'Damage calculation',
  'element': 'Element',
  'TargetType': 'Target',
  'defaultTargetRelation': 'Target side',
  'Cost': 'MP cost',
  'magnification': 'Power',
  'breakDamageValue': 'Break power',
  'accuracy': 'Accuracy',
  'hitCount': 'Hits',
  'hasUnit': 'Unit restriction',
  'equipCost': 'Equipment cost',
  'EffectType': 'Type',
  'statusCondition': 'Status',
  'addProbability': 'Chance',
  'ParamList': 'Parameters',
  'hitDamageRatioList': 'Hit damage shares',
};

String _words(String value) => value
    .split('::')
    .last
    .replaceAllMapped(RegExp(r'([a-z])([A-Z])'), (m) => '${m[1]} ${m[2]}')
    .replaceAll('_', ' ');

String _value(dynamic value) {
  if (value == null) return 'not set';
  if (value is bool) return value ? 'yes' : 'no';
  if (value is num) {
    return value == value.roundToDouble() ? '${value.toInt()}' : '$value';
  }
  if (value is List) {
    return value.isEmpty ? 'none' : value.map(_value).join(', ');
  }
  if (value is Map) {
    return value.entries
        .map((e) => '${_words('${e.key}')}: ${_value(e.value)}')
        .join(', ');
  }
  return _words('$value');
}

String _note(Map note, Map<num, Map> skills) {
  final path = note['field'].toString().split('.');
  final value = note['missing'] == true ? null : note['value'];
  var label = _labels[path.first] ?? _words(path.first);
  var text = _value(value);
  if (path.first == 'TargetType') {
    text = switch (value) {
      'Single' => 'single target',
      'Group' => 'all targets',
      'Self' => 'self',
      'Random' => 'random targets',
      'Spread' => 'targets in a line',
      'SingleAndGroup' => 'single, then all targets',
      _ => text,
    };
  } else if (path.first == 'DamageType' && value == 'Physic') {
    text = 'physical';
  } else if (path.first == 'hitDamageRatioList' && path.length > 1) {
    label = 'Hit ${int.parse(path[1]) + 1} damage share';
  } else if (path.first == 'SkillIcon') {
    label = 'Icon';
    text = value == null ? 'not set' : value.toString().split('.').last;
  } else if (path.first == 'effectBundleList') {
    if (path.length == 1) return 'Effects: $text';
    label = 'Effect ${int.parse(path[1]) + 1}';
    final position = path.indexOf('mechanics');
    final property = position >= 0 && position + 1 < path.length
        ? path[position + 1]
        : path.last;
    if (property == 'ParamList' && int.tryParse(path.last) != null) {
      final type = note['effectType'];
      label +=
          '${type == null ? '' : ' (${_words(type.toString())})'} parameter ${int.parse(path.last) + 1}';
      // A referenced ability can be named without guessing unknown effect rules.
      if (value is num && skills.containsKey(value)) {
        text = '${skills[value]!['name']}';
      }
    } else {
      label += ' ${_labels[property] ?? _words(property)}';
    }
  } else if (path.length > 1) {
    label += ' ${path.skip(1).map(_words).join(' ')}';
  }
  return '$label: $text';
}

/// Complete display descriptions; raw catalog rows and saved configs stay intact.
Map<num, String> catalogDescriptions(
  Map<String, dynamic> catalog,
  String kind,
) {
  final rows = ((catalog[kind] as List?) ?? []).cast<Map>();
  final effects = {
    for (final e in catalog['effects'] as List? ?? []) (e as Map)['id']: e,
  };
  final skills = <num, Map>{
    for (final s in catalog['skills'] as List? ?? [])
      (s as Map)['id'] as num: s,
  };
  final named = <String, List<Map>>{};
  for (final row in rows) {
    final name = (row['name'] ?? '').toString().trim().toLowerCase();
    if (name.isNotEmpty) named.putIfAbsent(name, () => []).add(row);
  }
  final fallback = <num, List<Map>>{};
  for (final versions in named.values.where((v) => v.length > 1)) {
    final mechanics = <num, Map<String, dynamic>>{};
    for (final row in versions) {
      final values = <String, dynamic>{
        for (final e in _fields.entries)
          if (row.containsKey(e.key)) e.value: row[e.key],
      };
      for (var i = 0; i < ((row['effects'] as List?) ?? []).length; i++) {
        final id = row['effects'][i];
        final effect = effects[id];
        if (effect == null) continue;
        for (final field in ['type', 'status', 'prob']) {
          if (effect.containsKey(field)) {
            values['effectBundleList.$i.effectId.mechanics.${{'type': 'EffectType', 'status': 'statusCondition', 'prob': 'addProbability'}[field]}'] =
                effect[field];
          }
        }
        for (var j = 0; j < ((effect['params'] as List?) ?? []).length; j++) {
          values['effectBundleList.$i.effectId.mechanics.ParamList.$j'] =
              effect['params'][j];
        }
      }
      mechanics[row['id'] as num] = values;
    }
    final fields = mechanics.values.expand((v) => v.keys).toSet();
    final changed = fields.where(
      (f) =>
          mechanics.values
              .map((v) => json.encode([v.containsKey(f), v[f]]))
              .toSet()
              .length >
          1,
    );
    for (final row in versions) {
      final values = mechanics[row['id']]!;
      fallback[row['id'] as num] = [
        for (final field in changed)
          {
            'field': field,
            'value': values[field],
            'missing': !values.containsKey(field),
            if (field.startsWith('effectBundleList.'))
              'effectType':
                  values['${field.split('.').take(4).join('.')}.EffectType'],
          },
      ];
    }
  }
  final policy = catalog['duplicatePolicy'] as Map?;
  final authoritative =
      policy?['available'] == true &&
      (policy?['variants'] as Map?)?.containsKey(kind) == true;
  final variants = (policy?['variants'] as Map?)?[kind] as Map?;
  return {
    for (final row in rows)
      row['id'] as num: () {
        final original = (row['desc'] ?? '').toString().trim();
        final generated = kind == 'skills' && row.containsKey('target')
            ? describe(Map<String, dynamic>.from(row))
            : '';
        final notes = authoritative
            ? ((variants?['${row['id']}'] as List?) ?? []).cast<Map>()
            : fallback[row['id']] ?? <Map>[];
        final differences = notes
            .map((n) => _note(n, skills))
            .toSet()
            .join('; ');
        return [
          if (differences.isNotEmpty) 'Same-name version: $differences.',
          if (original.isNotEmpty) original,
          if (generated.isNotEmpty && generated != original) generated,
        ].join('\n');
      }(),
  };
}
