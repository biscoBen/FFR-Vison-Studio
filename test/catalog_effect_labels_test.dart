import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';

void main() {
  Map<String, dynamic> fixture() => {
    'skills': [
      {
        'id': 250020,
        'name': 'Fira',
        'seq': [],
        'attr': 'Magic',
        'hasUnit': 'All',
      },
      {
        'id': 220020,
        'name': 'Fira',
        'seq': [1],
        'attr': 'Magic',
        'hasUnit': 'All',
      },
      {
        'id': 400210,
        'name': 'Jump',
        'seq': [],
        'attr': 'Ability',
        'hasUnit': 'All',
      },
    ],
    'animationPolicy': {
      'schema': 1,
      'skills': {
        '250020': {'donor': 220020, 'rule': 'same_name'},
      },
    },
    'duplicatePolicy': {
      'schema': 2,
      'available': true,
      'ownersComplete': true,
      'groups': {'skills': <List<int>>[]},
      'verifiedMatches': {
        'skills': {
          '250020': [220020],
        },
      },
      'owners': {
        'skills': {
          '250020': ['Tronn'],
        },
      },
    },
  };

  test('animation trials identify touched skills without changing sources or hiding rules', () {
    final cat = fixture();
    final rows = [
      {
        'id': 400260,
        'name': 'Steal',
        'attr': 'Ability',
        'hasUnit': 'All',
        'seq': [],
      },
      {
        'id': 400300,
        'name': 'Barrage',
        'attr': 'Ability',
        'hasUnit': 'All',
        'seq': [],
      },
    ];
    cat['skills'].addAll(rows);
    final before = catalogLibrary(
      cat,
      'skills',
      [],
    ).map((r) => r['id']).toList();
    cat['animationPolicy']['trials'] = {
      '400260': {'source': 'FFR'},
      '400300': {'source': 'FFBE'},
    };
    expect(
      catalogEntryTitle(cat, 'skills', rows[0]),
      'Steal (Verified; FFR test) — Source: Zidane; MR=1',
    );
    expect(
      catalogEntryTitle(cat, 'skills', rows[1]),
      'Barrage (Verified; FFBE test) — Source: Noctis; MR=9',
    );
    expect(catalogLibrary(cat, 'skills', []).map((r) => r['id']), before);
    expect(catalogEntryVerified(rows[0], 'skills'), isFalse);
    expect(catalogEntryVerified(rows[1], 'skills'), isFalse);
  });

  test('monster trials identify borrowed effects without changing selection or sources', () {
    final cat = fixture();
    final rows = [
      {
        'id': 500270,
        'name': '1,000 Needles',
        'attr': 'Ability',
        'hasUnit': 'All',
        'seq': [],
      },
      {
        'id': 505110,
        'name': '10,000 Needles',
        'attr': 'Ability',
        'hasUnit': 'All',
        'seq': [],
      },
    ];
    cat['skills'].addAll(rows);
    final before = catalogLibrary(
      cat,
      'skills',
      [],
    ).map((r) => r['id']).toList();
    cat['animationPolicy']['trials'] = {
      '500270': {'source': 'FFR mob'},
      '505110': {'source': 'FFR mob'},
    };
    expect(
      catalogEntryTitle(cat, 'skills', rows[0]),
      '1,000 Needles (Verified; FFR mob test) — Source: Cactuar',
    );
    expect(
      catalogEntryTitle(cat, 'skills', rows[1]),
      '10,000 Needles (Verified; FFR mob test) — Source: Gigantuar',
    );
    expect(catalogLibrary(cat, 'skills', []).map((r) => r['id']), before);
    expect(rows.every((r) => !catalogEntryVerified(r, 'skills')), isTrue);
  });

  test('mapped entries get Verified while untouched labels and sources stay intact', () {
    final cat = fixture();
    final mapped = cat['skills'][0] as Map;
    final original = fixture()..remove('animationPolicy');
    expect(
      catalogEntryTitle(cat, 'skills', mapped),
      catalogEntryTitle(
        original,
        'skills',
        mapped,
      ).replaceFirst('(Unverified)', '(Verified)'),
    );
    for (final index in [1, 2]) {
      expect(
        catalogEntryTitle(cat, 'skills', cat['skills'][index]),
        catalogEntryTitle(original, 'skills', original['skills'][index]),
      );
    }
    expect(catalogEntryVerified(mapped, 'skills'), isFalse);
  });

  test(
    'visual mappings do not weaken duplicate hiding or modify saved IDs',
    () {
      final cat = fixture();
      final before = catalogLibrary(
        cat,
        'skills',
        [],
      ).map((r) => r['id']).toList();
      final own = {
        'awakening': [
          [
            ['ActiveSkill', 250020],
          ],
        ],
      };
      final equipped = catalogLibrary(cat, 'skills', [
        own,
      ]).map((r) => r['id']).toList();
      cat.remove('animationPolicy');
      expect(catalogLibrary(cat, 'skills', []).map((r) => r['id']), before);
      expect(
        catalogLibrary(cat, 'skills', [own]).map((r) => r['id']),
        equipped,
      );
      expect(equipped, contains(250020));
    },
  );

  test(
    'unsupported metadata and custom moves do not gain visual verification',
    () {
      final cat = fixture();
      cat['animationPolicy']['schema'] = 99;
      expect(
        catalogEntryTitle(cat, 'skills', cat['skills'][0]),
        contains('(Unverified)'),
      );
      cat['animationPolicy']['schema'] = 1;
      final custom = Map<String, dynamic>.from(cat['skills'][0] as Map)
        ..['custom'] = true;
      expect(
        catalogEntryTitle(cat, 'skills', custom),
        isNot(contains('(Verified)')),
      );
    },
  );
}
