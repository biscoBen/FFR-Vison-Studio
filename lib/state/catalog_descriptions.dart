const _catalogFields = {
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
  'equipCost': 'equipCost',
};

// Fixed ordering and an explicit player-facing field list keep voices, row IDs,
// debug commands and other implementation details out of the picker.
const _skillFields = {
  'DamageType': 'Damage type',
  'TargetType': 'Target',
  'accuracy': 'Accuracy',
  'availableLocation': 'Location',
  'breakDamageValue': 'Break Power',
  'defaultTargetRelation': 'Target side',
  'magnification': 'Power',
};
const _extraFields = {
  'Cost': 'MP cost',
  'hitCount': 'Hits',
  'element': 'Element',
  'damageCalcType': 'Damage calculation',
  'equipCost': 'Equipment cost',
  'defaultTargetState': 'Target state',
  'targetRage': 'Target range',
  'criticalHitRate': 'Critical chance',
  'statusCondition': 'Status',
  'addProbability': 'Status chance',
  'parameterType': 'Stat',
  'parameterVariationType': 'Stat change',
  'onlyWhenFullHP': 'Requires full HP',
  'isTargetIgnoreSelf': 'Excludes self',
  'isIgnoreDefence': 'Ignores defence',
  'isIgnoreResistance': 'Ignores resistance',
  'isAlwaysHit': 'Always hits',
  'isReflect': 'Can be reflected',
  'isCover': 'Can be covered',
};

String _words(String value) => value
    .split('::')
    .last
    .replaceAllMapped(RegExp(r'([a-z])([A-Z])'), (m) => '${m[1]} ${m[2]}')
    .replaceAll('_', ' ');

String _value(dynamic value) {
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

String _fieldValue(String field, dynamic value) {
  if (field == 'TargetType') {
    return switch (value.toString().split('::').last) {
      'Single' => 'single target',
      'Group' => 'all targets',
      'Self' => 'self',
      'Random' => 'random targets',
      'Spread' => 'targets in a line',
      'SingleAndGroup' => 'single, then all targets',
      _ => _value(value),
    };
  }
  if (field == 'DamageType' && value.toString().split('::').last == 'Physic') {
    return 'Physical';
  }
  return _value(value);
}

String _playerText(dynamic value) {
  final text = (value ?? '').toString().trim();
  if (text.isEmpty ||
      RegExp(r'[぀-ヿ一-鿿]').hasMatch(text) ||
      RegExp(r'\b(TEMP|DEBUG|TODO)\b', caseSensitive: false).hasMatch(text) ||
      RegExp(r'\{[^}]+\}').hasMatch(text)) {
    return '';
  }
  return text.replaceFirst(RegExp(r'^\[[^\]]+\]\s*'), '');
}

List<String> _effectDescriptions(
  Map data,
  List<dynamic> fallbackIds,
  Map<dynamic, Map> effects,
) {
  final bundles = data['effectBundleList'] as List?;
  final items = <(Map, Map)>[];
  if (bundles != null) {
    for (final bundle in bundles.cast<Map>()) {
      final reference = bundle['effectId'];
      final effect = reference is Map
          ? reference['mechanics'] as Map?
          : effects[reference];
      if (effect != null) items.add((bundle, effect));
    }
  } else {
    for (final id in fallbackIds) {
      if (effects[id] != null) items.add(({}, effects[id]!));
    }
  }
  return [
    for (var i = 0; i < items.length; i++)
      () {
        final (bundle, effect) = items[i];
        final type = effect['EffectType'] ?? effect['type'];
        final parts = <String>['Effect ${i + 1}: ${_value(type ?? 'Unknown')}'];
        for (final (field, label) in [
          ('TargetType', 'Target'),
          ('targetRelation', 'Target side'),
        ]) {
          if (bundle[field] != null) {
            parts.add('$label: ${_fieldValue(field, bundle[field])}');
          }
        }
        final status = effect['statusCondition'] ?? effect['status'];
        if (status != null && status.toString().split('::').last != 'None') {
          parts.add('Status: ${_value(status)}');
        }
        final chance = effect['addProbability'] ?? effect['prob'];
        if (chance != null &&
            (status != null && status != 'None' || chance != 100)) {
          parts.add('Chance: ${_value(chance)}');
        }
        final params = (effect['ParamList'] ?? effect['params']) as List?;
        if (params != null && params.any((p) => p != -1)) {
          // Preserve recorded parameters rather than guessing undocumented rules.
          parts.add('Parameters: ${params.map(_value).join(', ')}');
        }
        return parts.join('; ');
      }(),
  ];
}

/// Consistent recorded stats and effects, without rewriting the source catalog.
/// Extracted values take precedence; absent values are never filled with guesses.
Map<num, String> catalogDescriptions(
  Map<String, dynamic> catalog,
  String kind,
) {
  final rows = ((catalog[kind] as List?) ?? []).cast<Map>();
  final policy = catalog['duplicatePolicy'] as Map?;
  final details = policy?['available'] == true
      ? ((policy?['details'] as Map?)?[kind] as Map?)
      : null;
  final variants = policy?['available'] == true
      ? ((policy?['variants'] as Map?)?[kind] as Map?)
      : null;
  final effects = <dynamic, Map>{
    for (final e in catalog['effects'] as List? ?? []) (e as Map)['id']: e,
  };
  final combatVariants = (policy?['combatVariants'] as Map?)?[kind] as Map?;
  return {
    for (final row in rows)
      row['id'] as num: () {
        final data = <String, dynamic>{
          for (final e in _catalogFields.entries)
            if (row[e.key] != null) e.value: row[e.key],
          if (details?['${row['id']}'] is Map)
            ...Map<String, dynamic>.from(details!['${row['id']}'] as Map),
        };
        // Older engines supply full differing values but not complete raw rows.
        // Use their known stats without dumping unknown/debug fields into the UI.
        if (details?['${row['id']}'] is! Map) {
          for (final note
              in (variants?['${row['id']}'] as List? ?? []).cast<Map>()) {
            final field = note['field'].toString();
            if (!field.contains('.') &&
                note['missing'] != true &&
                note['value'] != null) {
              data[field] = note['value'];
            }
          }
        }
        final parts = <String>[];
        for (final field
            in (kind == 'skills' ? _skillFields : <String, String>{}).entries) {
          if (data[field.key] != null) {
            parts.add(
              '${field.value}: ${_fieldValue(field.key, data[field.key])}',
            );
          }
        }
        if (kind == 'skills') {
          final mapEffect = data['mapEffectType'];
          final effect =
              mapEffect != null &&
                  mapEffect.toString().split('::').last != 'None'
              ? mapEffect
              : data['skillEffectType'];
          if (effect != null) parts.add('Effect type: ${_value(effect)}');
        }
        for (final field in _extraFields.entries) {
          final value = data[field.key];
          if (value == null) continue;
          if (['element', 'statusCondition'].contains(field.key) &&
              value.toString().split('::').last == 'None') {
            continue;
          }
          final differs = (variants?['${row['id']}'] as List? ?? []).any(
            (n) => n['field'] == field.key,
          );
          if (value is bool && !value && !differs) continue;
          parts.add('${field.value}: ${_fieldValue(field.key, value)}');
        }
        final ratios = data['hitDamageRatioList'] as List?;
        if (ratios != null && (data['hitCount'] as num? ?? 0) > 1) {
          parts.add(
            'Hit damage shares: ${_value(ratios.where((v) => v != 0).toList())}',
          );
        }
        // Retain real same-name differences in less common game fields without
        // reintroducing presentation/debug metadata or guessing their meaning.
        for (final note
            in (combatVariants?['${row['id']}'] as List? ?? []).cast<Map>()) {
          final field = note['field'].toString();
          if (field.contains('.') ||
              _skillFields.containsKey(field) ||
              _extraFields.containsKey(field) ||
              [
                'skillEffectType',
                'hitDamageRatioList',
                'effectBundleList',
              ].contains(field)) {
            continue;
          }
          parts.add(
            '${_words(field)}: ${note['missing'] == true ? 'not provided' : _value(note['value'])}',
          );
        }
        final original = _playerText(row['desc']);
        return [
          if (parts.isNotEmpty) parts.join('; '),
          if (original.isNotEmpty) original,
          ..._effectDescriptions(
            data,
            (row['effects'] as List?) ?? [],
            effects,
          ),
        ].join('\n');
      }(),
  };
}
