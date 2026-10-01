import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';

void main() {
  Map<String, dynamic> catalog({List<int> protected = const []}) => {
    'skills': [
      {
        'id': 10,
        'name': 'Cure',
        'seq': [1],
      },
      {'id': 20, 'name': 'Cure', 'seq': []},
      {
        'id': 30,
        'name': 'Cure',
        'seq': [1],
        'mag': 500,
      },
    ],
    'passives': [
      {'id': 1, 'name': 'Boost'},
      {'id': 2, 'name': 'Boost'},
    ],
    'duplicatePolicy': {
      'schema': 1,
      'available': true,
      'groups': {
        'skills': [
          [10, 20],
        ],
        'passives': [
          [1, 2],
        ],
      },
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
    final own = {
      'awakening': [
        [
          ['ActiveSkill', 20],
        ],
      ],
      'synchro': [
        [
          ['PassiveSkill', 2],
        ],
      ],
    };
    expect(catalogLibrary(catalog(), 'skills', [own]).map((s) => s['id']), [
      20,
      30,
    ]);
    expect(catalogLibrary(catalog(), 'passives', [own]).map((s) => s['id']), [
      2,
    ]);
  });
  test(
    'missing or unavailable duplicate proof leaves all entries accessible',
    () {
      final cat = catalog()..remove('duplicatePolicy');
      expect(catalogLibrary(cat, 'skills', []).length, 3);
      cat['duplicatePolicy'] = {'schema': 1, 'available': false};
      expect(catalogLibrary(cat, 'skills', []).length, 3);
    },
  );
  test('unused unverified combat matches hide even if NPC tables reference them, keeping verified choices', () {
    final cat = catalog(protected: [20]);
    for (final s in cat['skills']) {
      s.addAll({'attr': 'Magic', 'hasUnit': 'All'});
    }
    cat['duplicatePolicy']['schema'] = 2;
    cat['duplicatePolicy']['ownersComplete'] = true;
    cat['duplicatePolicy']['groups']['skills'] = <List<int>>[];
    cat['duplicatePolicy']['verifiedMatches'] = {
      'skills': {
        '20': [10],
      },
    };
    final before = (cat['skills'] as List).map((s) => Map.from(s)).toList();
    expect(catalogLibrary(cat, 'skills', []).map((s) => s['id']), [10, 30]);
    final own = {
      'synchro': [
        [
          ['ActiveSkill', 20],
        ],
      ],
    };
    expect(catalogLibrary(cat, 'skills', [own]).map((s) => s['id']), [
      10,
      20,
      30,
    ]);
    expect(cat['skills'], before);
  });
  test('default assignments keep unverified matches visible with all owning vision names', () {
    final cat = catalog();
    for (final s in cat['skills']) {
      s.addAll({'attr': 'Magic', 'hasUnit': 'All'});
    }
    cat['visions'] = [
      {
        'name': 'Leah',
        'awakening': [
          [
            ['ActiveSkill', 20],
          ],
        ],
      },
      {
        'name': 'Ayaka',
        'synchro': [
          [
            ['ActiveSkill', 20],
          ],
        ],
      },
    ];
    cat['duplicatePolicy'].addAll({
      'schema': 2,
      'ownersComplete': true,
      'owners': {
        'skills': {
          '20': ['Cloud'],
        },
      },
      'verifiedMatches': {
        'skills': {
          '20': [10],
        },
      },
    });
    expect(catalogLibrary(cat, 'skills', []).map((s) => s['id']), [10, 20, 30]);
    expect(
      catalogEntryTitle(cat, 'skills', cat['skills'][1]),
      'Cure (Unverified) — Source: Ayaka, Cloud, Leah',
    );
    expect(catalogEntryTitle(cat, 'skills', cat['skills'][0]), 'Cure');
    cat['visions'] = [];
    cat['duplicatePolicy']['owners'] = {};
    expect(
      catalogEntryTitle(cat, 'skills', cat['skills'][1]),
      'Cure (Unverified)',
    );
  });
  test('unverified passive labels use original grants without treating NPC restrictions as default owners', () {
    final cat = <String, dynamic>{
      'visions': [
        {
          'name': 'Cloud',
          'awakening': [
            [
              ['PassiveSkill', 1],
            ],
          ],
        },
      ],
    };
    expect(
      catalogEntryTitle(cat, 'passives', {'id': 1, 'name': '攻撃アップ'}),
      '攻撃アップ (Unverified) — Source: Cloud',
    );
    expect(
      catalogEntryTitle(cat, 'skills', {
        'id': 2,
        'name': 'Move',
        'hasUnit': 'Goblin',
      }),
      'Move (Unverified)',
    );
  });
  test('incomplete original ownership data keeps every entry selectable', () {
    final cat = catalog();
    cat['duplicatePolicy'].addAll({
      'schema': 2,
      'ownersComplete': false,
      'verifiedMatches': {
        'skills': {
          '20': [10],
        },
      },
    });
    expect(catalogLibrary(cat, 'skills', []).map((s) => s['id']), [10, 20, 30]);
    expect(catalogLibrary(cat, 'passives', []).length, 2);
  });
}
