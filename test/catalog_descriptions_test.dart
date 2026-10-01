import 'dart:convert';

import 'package:ffr_vision_studio/state/catalog_descriptions.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> variantCatalog() => {
  'skills': [
    {
      'id': 400010,
      'name': 'Fire',
      'desc': 'The complete original description.',
      'attr': 'Magic',
      'seq': [1],
      'hasUnit': 'All',
      'target': 'Single',
      'relation': 'Enemies',
      'dmgType': 'Magic',
      'element': 'Fire',
      'mag': 17,
      'cost': 5,
    },
    {
      'id': 400020,
      'name': 'Fire',
      'desc': 'The complete original description.',
      'attr': 'Magic',
      'seq': [1],
      'hasUnit': 'All',
      'target': 'Group',
      'relation': 'Enemies',
      'dmgType': 'Magic',
      'element': 'Fire',
      'mag': 12,
      'cost': 5,
    },
  ],
  'passives': [
    {
      'id': 1001,
      'name': 'Grit',
      'desc': 'Survive with 1 HP.',
      'equipCost': 20,
      'effects': [10],
    },
    {
      'id': 1002,
      'name': 'Grit',
      'desc': 'Survive with 1 HP.',
      'equipCost': 40,
      'effects': [20],
    },
  ],
  'effects': [
    {
      'id': 10,
      'type': 'Reprieve',
      'params': [0, -1],
      'prob': 100,
    },
    {
      'id': 20,
      'type': 'Reprieve',
      'params': [0, 1],
      'prob': 100,
    },
  ],
  'icons': [],
};

void main() {
  test('same-name abilities explain each target and power without changing source descriptions', () {
    final cat = variantCatalog();
    final before = json.encode(cat);
    final descriptions = catalogDescriptions(cat, 'skills');
    expect(descriptions[400010], contains('Target: single target'));
    expect(descriptions[400010], contains('Power: 17'));
    expect(descriptions[400020], contains('Target: all targets'));
    expect(descriptions[400020], contains('Power: 12'));
    expect(
      descriptions.values.every(
        (d) => d.contains('The complete original description.'),
      ),
      isTrue,
    );
    expect(descriptions.values.any((d) => d.contains('MP cost:')), isFalse);
    expect(json.encode(cat), before);
  });

  test(
    'same-name passives explain equipment cost and different effect parameters',
    () {
      final descriptions = catalogDescriptions(variantCatalog(), 'passives');
      expect(descriptions[1001], contains('Equipment cost: 20'));
      expect(descriptions[1002], contains('Equipment cost: 40'));
      expect(
        descriptions[1001],
        contains('Effect 1 (Reprieve) parameter 2: -1'),
      );
      expect(
        descriptions[1002],
        contains('Effect 1 (Reprieve) parameter 2: 1'),
      );
      expect(descriptions[1001], contains('Survive with 1 HP.'));
    },
  );

  test('equivalent effects with different IDs do not invent a behavioral difference', () {
    final cat = variantCatalog();
    cat['passives'][1]['equipCost'] = 20;
    cat['effects'][1]['params'] = [0, -1];
    expect(
      catalogDescriptions(cat, 'passives').values,
      everyElement('Survive with 1 HP.'),
    );
    cat['skills'][1]['name'] = 'Other skill';
    expect(
      catalogDescriptions(cat, 'skills')[400010],
      isNot(contains('Same-name version:')),
    );
  });

  test('full extracted differences take precedence and preserve empty or missing fields', () {
    final cat = variantCatalog();
    cat['duplicatePolicy'] = {
      'available': true,
      'variants': {
        'skills': {
          '400010': [
            {'field': 'onlyWhenFullHP', 'value': true},
            {
              'field': 'effectBundleList.0.effectId.mechanics.ParamList',
              'value': [],
            },
            {'field': 'unknownSetting', 'value': null, 'missing': true},
          ],
        },
      },
    };
    final descriptions = catalogDescriptions(cat, 'skills');
    expect(descriptions[400010], contains('only When Full HP: yes'));
    expect(descriptions[400010], contains('Effect 1 Parameters: none'));
    expect(descriptions[400010], contains('unknown Setting: not set'));
    expect(descriptions[400010], isNot(contains('Power: 17')));
    expect(descriptions[400020], isNot(contains('Same-name version:')));
  });
}
