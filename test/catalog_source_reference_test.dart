import 'dart:convert';

import 'package:ffr_vision_studio/state/catalog_helpers.dart';
import 'package:ffr_vision_studio/state/catalog_source_reference.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  String title(int id, {String name = 'Move', String kind = 'skills'}) =>
      catalogEntryTitle({}, kind, {'id': id, 'name': name});

  test('native kits label the exact shared ID and their own granting ranks', () {
    final unit = <String, dynamic>{
      'native': {'baseline': {
        'en': 'Tronn',
        'awakening': [[['ActiveSkill', 220010]], [], [], []],
        'synchro': [for (var i = 0; i < 10; i++)
          i == 7 ? [['PassiveSkill', 1279, -1]] : []],
      }},
    };
    final fire = {'id': 220010, 'name': 'Fire', 'attr': 'Magic',
      'seq': [1], 'hasUnit': 'All'};
    final cat = <String, dynamic>{'visions': [
      for (final name in ['Amelia', 'Rain', 'Tronn'])
        {'name': name, 'awakening': [[['ActiveSkill', 220010]]]},
    ]};
    expect(catalogEntryTitle(cat, 'skills', fire),
      'Fire — Source: Amelia, Rain, Tronn; awakening=1 (Amelia)');
    expect(catalogEntryTitle(cat, 'skills', fire, nativeUnit: unit),
      'Fire — Source: Tronn; awakening=1');
    expect(catalogEntryTitle(cat, 'passives',
      {'id': 1279, 'name': 'Stagger Power +20%'}, nativeUnit: unit),
      'Stagger Power +20% — Source: Tronn; MR=7');
    expect(catalogEntryTitle(cat, 'skills',
      {'id': 250010, 'name': 'Fire', 'row': '(敵用)ファイア'}, nativeUnit: unit),
      'Fire (Unverified) (Enemy version) — Source: Tronn');
    // A newly equipped same-name ID cannot acquire the inherited ID's labels.
    expect(catalogEntryTitle(cat, 'skills',
      {'id': 777777, 'name': 'Fire'}, nativeUnit: unit),
      'Fire (Unverified)');
  });

  test('the full 91-page PDF covers every assigned game ID, with explicit awakening only', () {
    final references = catalogSourceReferences.values.expand(
      (rows) => rows.values,
    );
    expect(catalogSourceReferences['skills']!.length, 1141);
    expect(catalogSourceReferences['passives']!.length, 343);
    expect(references.where((r) => r.internalLabelOnly).length, 6);
    expect(references.where((r) => r.awakening != null).length, 322);
    expect(references.where((r) => r.mr != null).length, 128);
    expect(
      references
          .where((r) => r.mr != null)
          .every((r) => r.awakening == null && r.mr! >= 1 && r.mr! <= 10),
      isTrue,
    );
    expect(
      references.every(
        (r) => r.awakening == null || (r.awakening! >= 1 && r.awakening! <= 4),
      ),
      isTrue,
    );
  });

  test('additional PDF sections label enemies, party members, espers and items by ID', () {
    expect(
      title(500270, name: '1,000 Needles'),
      '1,000 Needles (Unverified) — Source: Cactuar',
    );
    expect(
      title(505110, name: '10,000 Needles'),
      '10,000 Needles (Unverified) — Source: Gigantuar',
    );
    expect(
      title(571030, name: '100,000 Needles'),
      '100,000 Needles (Unverified) — Source: Gargantuan Gigantuar',
    );
    expect(
      title(408040, name: 'Abyss Graviton'),
      'Abyss Graviton (Unverified) — Source: Archwitch Fina',
    );
    expect(title(300370), 'Move (Unverified) — Source: Leviathan');
    expect(title(100070), 'Move (Unverified) — Source: Antidote Herb');
    expect(title(1550, kind: 'passives'), 'Move — Source: Mastery Ring');
    expect(title(1136, kind: 'passives'), 'Move — Source: Elnath');
    expect(title(505130, name: 'Tidal Wave'), 'Tidal Wave (Unverified)');
    expect(title(1541, kind: 'passives'), 'Move');
  });

  test('additional source metadata never unhides a duplicate, Attack, untranslated or Resonance row', () {
    final cat = <String, dynamic>{
      'abilityModes': {'schema': 1, 'showUnverified': true, 'useChanges': true},
      'skills': [
        {'id': 500270, 'name': '1,000 Needles', 'seq': [], 'attr': 'Ability'},
        {'id': 505110, 'name': '10,000 Needles', 'seq': [], 'attr': 'Ability'},
        {'id': 413600, 'name': 'Attack', 'attr': 'Fight'},
        {'id': 300370, 'name': '(召喚獣用)ウォタガ全体化', 'attr': 'Magic'},
        {'id': 440280, 'name': 'Aetherial Wind', 'attr': 'FinishBlow'},
      ],
      'duplicatePolicy': {
        'schema': 2,
        'available': true,
        'ownersComplete': true,
        'groups': {
          'skills': [
            [500270, 505110],
          ],
        },
      },
    };
    final before = jsonEncode(cat);
    for (final row in cat['skills']) {
      expect(catalogEntryTitle(cat, 'skills', row), contains('Source:'));
      expect(catalogDefaultOwners(cat, 'skills', row), isEmpty);
    }
    expect(
      catalogSelectableLibrary(cat, 'skills', []).map((row) => row['id']),
      [500270],
    );
    final saved = {
      'awakening': [
        [
          ['ActiveSkill', 505110],
        ],
      ],
    };
    final savedBefore = jsonEncode(saved);
    expect(
      catalogSelectableLibrary(cat, 'skills', [saved]).map((row) => row['id']),
      [505110],
    );
    expect(jsonEncode(cat), before);
    expect(jsonEncode(saved), savedBefore);
  });

  test('same-name IDs keep their documented source and exact awakening', () {
    expect(
      title(220170, name: 'Aero'),
      'Aero (Unverified) — Source: Onion Knight; awakening=1',
    );
    expect(title(225120, name: 'Aero'), 'Aero (Unverified) — Source: Victoria');
    expect(
      title(250170, name: 'Aero'),
      'Aero (Unverified) — Source: Aether’s Minion',
    );
    expect(
      title(220190, name: 'Aeroga'),
      'Aeroga (Unverified) — Source: Onion Knight; awakening=3',
    );
    expect(title(220460), 'Move (Unverified) — Source: Y’shtola; awakening=2');
  });

  test('verified abilities, passives, equipment, espers and Resonances get sources', () {
    expect(
      catalogEntryTitle({}, 'skills', {
        'id': 220170,
        'name': 'Aero',
        'seq': [1],
        'hasUnit': 'All',
        'attr': 'Magic',
      }),
      'Aero — Source: Onion Knight; awakening=1',
    );
    expect(
      title(1128, name: 'Add Blind', kind: 'passives'),
      'Add Blind — Source: Firion; awakening=3',
    );
    expect(
      title(1130, name: 'Add Instant Death', kind: 'passives'),
      'Add Instant Death — Source: Death Adder',
    );
    expect(title(225190), 'Move (Unverified) — Source: Siren');
    expect(title(440280), 'Move (Unverified) — Source: Y’shtola');
    expect(title(400450), 'Move (Unverified) — Source: Amelia; MR=3');
  });

  test('bond levels identify the source reward without implying awakening or changing ownership', () {
    expect(
      title(400260, name: 'Steal'),
      'Steal (Unverified) — Source: Zidane; MR=1',
    );
    expect(
      title(400300, name: 'Barrage'),
      'Barrage (Unverified) — Source: Noctis; MR=9',
    );
    expect(title(1281, kind: 'passives'), 'Move — Source: Tronn; MR=1');
    final cat = {
      'duplicatePolicy': {
        'sources': {
          'skills': {
            '400260': ['A2'],
          },
        },
      },
    };
    expect(
      catalogEntryTitle(cat, 'skills', {'id': 400260, 'name': 'Steal'}),
      'Steal (Unverified) — Source: A2, Zidane; MR=1 (Zidane)',
    );
  });

  test(
    'sources merge without duplicates and a tier belongs to its PDF owner',
    () {
      final cat = <String, dynamic>{
        'visions': [
          {
            'name': 'Onion Knight',
            'awakening': [
              [
                ['ActiveSkill', 220170],
              ],
            ],
          },
          {
            'name': 'Victoria',
            'awakening': [
              [],
              [],
              [
                ['ActiveSkill', 220170],
              ],
            ],
          },
        ],
        'duplicatePolicy': {
          'sources': {
            'skills': {
              '220170': ['Siren', 'Onion Knight', 'Siren'],
            },
          },
        },
      };
      expect(
        catalogEntryTitle(cat, 'skills', {'id': 220170, 'name': 'Aero'}),
        'Aero (Unverified) — Source: Onion Knight, Siren, Victoria; awakening=1 (Onion Knight)',
      );
    },
  );

  test('internal owner labels are qualified and unknown assignments stay unlabelled', () {
    expect(
      title(420060),
      'Move (Unverified) — Source: Lasswell (internal label only)',
    );
    expect(title(210190, name: 'Holy'), 'Holy (Unverified)');
    expect(title(999999, name: 'Aero'), 'Aero (Unverified)');
    expect(
      title(1281, kind: 'skills'),
      'Move (Unverified)',
    ); // Passive IDs do not cross kinds.
    expect(
      catalogEntryTitle({}, 'skills', {
        'id': 220170,
        'name': 'Custom Aero',
        'custom': true,
      }),
      'Custom Aero',
    );
    expect(
      catalogEntryTitle(
        {
          'duplicatePolicy': {
            'sources': {
              'skills': {
                '420060': ['Lasswell'],
              },
            },
          },
        },
        'skills',
        {'id': 420060, 'name': 'Blizzaga Blade'},
      ),
      'Blizzaga Blade (Unverified) — Source: Lasswell',
    );
  });

  test('reference labels leave every selection rule and saved ID intact', () {
    final cat = <String, dynamic>{
      'abilityModes': {'schema': 1, 'showUnverified': true, 'useChanges': true},
      'skills': [
        {
          'id': 220170,
          'name': 'Aero',
          'seq': [1],
          'hasUnit': 'All',
          'attr': 'Magic',
        },
        {'id': 225120, 'name': 'Aero', 'seq': [], 'attr': 'Magic'},
        {'id': 300380, 'name': '(召喚獣用)エアロガ全体化', 'attr': 'Magic'},
        {'id': 440280, 'name': 'Aetherial Wind', 'attr': 'FinishBlow'},
        {'id': 501000, 'name': 'Attack', 'attr': 'Fight'},
      ],
      'visions': [],
      'duplicatePolicy': {
        'schema': 2,
        'available': true,
        'ownersComplete': true,
        'verifiedMatches': {
          'skills': {
            '225120': [220170],
          },
        },
      },
    };
    final unit = {
      'synchro': [
        [
          ['ActiveSkill', 440280],
          ['ActiveSkill', 501000],
        ],
      ],
    };
    final before = jsonEncode([cat, unit]);
    for (final row in cat['skills']) {
      catalogEntryTitle(cat, 'skills', row);
    }
    expect(
      catalogSelectableLibrary(cat, 'skills', [unit]).map((r) => r['id']),
      [220170],
    );
    expect(
      catalogSelectableLibrary(cat, 'skills', [
        {
          'awakening': [
            [
              ['ActiveSkill', 225120],
            ],
          ],
        },
      ]).map((r) => r['id']),
      [220170, 225120],
    );
    expect(jsonEncode([cat, unit]), before);
  });
}
