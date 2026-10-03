import 'dart:convert';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  Map<String, dynamic> fixture(bool show, bool changes) => {
    'abilityModes': {'schema': 1, 'showUnverified': show, 'useChanges': changes},
    'reviewedHiddenSkills': [500270, 220020],
    'skills': [
      {'id': 220020, 'name': 'Fira', 'seq': [1], 'hasUnit': 'All', 'attr': 'Magic'},
      {'id': 250020, 'name': 'Fira', 'seq': [], 'hasUnit': 'All', 'attr': 'Magic'},
      {'id': 500270, 'name': '1,000 Needles', 'seq': [], 'hasUnit': 'Cactuar', 'attr': 'Ability'},
    ],
    'animationPolicy': {
      'schema': 1, 'skills': {'250020': {'donor': 220020}},
      'trials': {'500270': {'source': 'FFR mob'}},
    },
  };

  test('three modes use the native verification filter and isolate reviewed hiding', () {
    for (final changes in [false, true]) {
      final cat = fixture(false, changes);
      expect(catalogSelectableLibrary(cat, 'skills', []).map((r) => r['id']), [220020]);
      expect(catalogUsesAbilityChanges(cat), isFalse);
    }
    expect(catalogSelectableLibrary(fixture(true, false), 'skills', []).map((r) => r['id']), [220020, 250020, 500270]);
    expect(catalogSelectableLibrary(fixture(true, true), 'skills', []).map((r) => r['id']), [250020]);
  });

  test('source and native verification labels survive while donor labels follow mode', () {
    final original = fixture(true, false);
    final enhanced = fixture(true, true);
    expect(catalogEntryTitle(original, 'skills', original['skills'][1]), contains('(Unverified)'));
    expect(catalogEntryTitle(enhanced, 'skills', enhanced['skills'][1]), contains('(Verified)'));
    for (final cat in [original, enhanced]) {
      expect(catalogEntryTitle(cat, 'skills', cat['skills'][2]), contains('Source: Cactuar'));
    }
    expect(catalogEntryTitle(original, 'skills', original['skills'][2]), isNot(contains('FFR mob test')));
  });

  test('selector modes preserve full rows, equipped lookups and passive behavior', () {
    final cat = fixture(false, false)..['passives'] = [{'id': 1, 'name': 'Passive'}];
    final before = jsonEncode(cat);
    expect(catalogSelectableLibrary(cat, 'skills', [{'awakening': [['ActiveSkill', 500270]]}]), hasLength(1));
    expect(catalogLibrary(cat, 'skills', []).map((r) => r['id']), contains(500270));
    expect(catalogSelectableLibrary(cat, 'passives', []), hasLength(1));
    expect(jsonEncode(cat), before);
  });

  test('persisted settings API sends both flags without touching roster or testing controls', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/abilities/settings');
      expect(request.method, 'PUT');
      expect(jsonDecode(request.body), {'schema': 1, 'showUnverified': true, 'useChanges': false});
      return http.Response(request.body, 200);
    });
    await http.runWithClient(() async {
      expect(await Api('http://studio').saveAbilityModes(showUnverified: true, useChanges: false),
          {'schema': 1, 'showUnverified': true, 'useChanges': false});
    }, () => client);
  });
}
