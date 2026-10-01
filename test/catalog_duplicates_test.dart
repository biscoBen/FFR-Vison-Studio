import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';

void main() {
  Map<String, dynamic> catalog({List<int> protected = const []}) => {
    'skills': [
      {'id': 10, 'name': 'Cure', 'seq': [1]},
      {'id': 20, 'name': 'Cure', 'seq': []},
      {'id': 30, 'name': 'Cure', 'seq': [1], 'mag': 500},
    ],
    'passives': [{'id': 1, 'name': 'Boost'}, {'id': 2, 'name': 'Boost'}],
    'duplicatePolicy': {
      'schema': 1, 'available': true,
      'groups': {'skills': [[10, 20]], 'passives': [[1, 2]]},
      'protected': {'skills': protected, 'passives': []},
    },
  };
  test('unused exact duplicates collapse while same-name variants and the full catalog remain', () {
    final cat = catalog();
    expect(catalogLibrary(cat, 'skills', []).map((s) => s['id']), [10, 30]);
    expect((cat['skills'] as List).length, 3);
    expect(catalogLibrary(cat, 'passives', []).map((s) => s['id']), [1]);
  });
  test('every original equipped entry and edited roster/MR/config reference stays available', () {
    final cat = catalog(protected: [10, 20]);
    expect(catalogLibrary(cat, 'skills', []).length, 3);
    final own = {'awakening': [[['ActiveSkill', 20]]], 'synchro': [[['PassiveSkill', 2]]]};
    expect(catalogLibrary(catalog(), 'skills', [own]).map((s) => s['id']), [20, 30]);
    expect(catalogLibrary(catalog(), 'passives', [own]).map((s) => s['id']), [2]);
  });
  test('missing or unavailable duplicate proof leaves all entries accessible', () {
    final cat = catalog()..remove('duplicatePolicy');
    expect(catalogLibrary(cat, 'skills', []).length, 3);
    cat['duplicatePolicy'] = {'schema': 1, 'available': false};
    expect(catalogLibrary(cat, 'skills', []).length, 3);
  });
}
