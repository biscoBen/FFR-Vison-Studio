import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';

void main() {
  test('original and Copy remain selectable together with matching descriptions and source labels', () {
    final originals = [
      {'id': 400440, 'name': 'Chakra', 'desc': 'Restore own HP.', 'attr': 'Ability', 'seq': [], 'hasUnit': 'All'},
      {'id': 403110, 'name': 'Cheer', 'desc': 'Increase defense and speed.', 'attr': 'Ability', 'seq': [], 'hasUnit': 'Fina'},
      {'id': 414500, 'name': 'Purify', 'desc': 'Restore allies’ HP and remove debuffs.', 'attr': 'Ability', 'seq': [], 'hasUnit': 'All'},
      {'id': 505580, 'name': 'Seal of Conviction', 'desc': 'Deal dark physical damage.', 'attr': 'Ability', 'seq': [], 'hasUnit': 'All'},
    ];
    final copies = [for (final r in originals) {...r, 'id': (r['id'] as int) + 9000000,
      'name': '${r['name']} (Copy)', 'comparisonOf': r['id']}];
    final catalog = <String, dynamic>{
      'skills': [...originals, ...copies],
      'visions': <Map<String, dynamic>>[],
      'animationPolicy': {'schema': 1, 'skills': {for (final r in originals) '${r['id']}': {'donor': 210010}}},
      'duplicatePolicy': {'schema': 2, 'available': true, 'ownersComplete': true,
        'groups': {'skills': <List<int>>[]}, 'verifiedMatches': {'skills': <String, dynamic>{}}},
    };
    final selected = catalogSelectableLibrary(catalog, 'skills', []);
    expect(selected.map((r) => r['id']).toSet(), [...originals, ...copies].map((r) => r['id']).toSet());
    for (var i = 0; i < originals.length; i++) {
      final title = catalogEntryTitle(catalog, 'skills', copies[i]);
      expect(title, contains('(Copy)'));
      expect(title, isNot(contains('(Verified)')));
      expect(title.split(' — Source: ').last,
          catalogEntryTitle(catalog, 'skills', originals[i]).split(' — Source: ').last);
      expect(copies[i]['desc'], originals[i]['desc']);
    }
    expect(catalogEntryTitle(catalog, 'skills', copies[0]), contains('MR=3'));
    expect(catalogEntryTitle(catalog, 'skills', copies[2]), contains('awakening=2'));
  });
}
