import 'dart:convert';

import 'package:ffr_vision_studio/state/catalog_helpers.dart';
import 'package:ffr_vision_studio/state/catalog_source_reference.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  String title(int id, {String name = 'Move', String kind = 'skills'}) =>
      catalogEntryTitle({}, kind, {'id': id, 'name': name});

  test(
    'the PDF covers all assigned Studio IDs, with explicit awakening only',
    () {
      final references = catalogSourceReferences.values.expand(
        (rows) => rows.values,
      );
      expect(catalogSourceReferences['skills']!.length, 329);
      expect(catalogSourceReferences['passives']!.length, 282);
      expect(references.where((r) => r.internalLabelOnly).length, 6);
      expect(references.where((r) => r.awakening != null).length, 322);
      expect(
        references.every(
          (r) =>
              r.awakening == null || (r.awakening! >= 1 && r.awakening! <= 4),
        ),
        isTrue,
      );
    },
  );

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
    expect(title(400450), 'Move (Unverified) — Source: Amelia'); // Bond reward.
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
