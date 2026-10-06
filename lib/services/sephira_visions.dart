import 'dart:convert';

import 'package:flutter/services.dart';

import 'character_config.dart';

/// Optional, editable presets. Membership lives in portable character configs;
/// disabled entries retain their IDs and edits but are omitted by the builder.
class SephiraVisions {
  static const field = 'sephiraVision';
  static const asset = 'assets/sephira_visions/catalog.json';
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
  static bool included(Map unit) => !member(unit) || unit[field]['enabled'] == true;

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
}
