import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';

void main() {
  test('demo-confirmed monsters are visible without enabling animation repairs', () {
    final working = [500120, 500580, 500440, 500140, 500510].map((id) => {
      'id': id, 'name': 'Working $id', 'seq': [1, 2], 'hasUnit': 'All', 'attr': 'Ability',
      'studioLiveTest': {'schema': 1, 'result': 'visible_animation'},
    }).toList();
    final cling = {'id': 500910, 'name': 'Cling', 'seq': [2], 'hasUnit': 'All', 'attr': 'Ability',
      'studioLiveTest': {'schema': 1, 'result': 'damage_only_no_animation'}};
    final catalog = {'skills': [...working, cling]};
    expect(catalogSelectableLibrary(catalog, 'skills', []).map((s) => s['id']), working.map((s) => s['id']));
    for (final skill in working) {
      expect(catalogEntryTitle(catalog, 'skills', skill), contains('(Verified; demo test)'));
    }
    expect(catalogEntryVerified(cling, 'skills'), isFalse);
    expect(catalogEntryTitle(catalog, 'skills', cling), contains('(Unverified)'));
  });
}
