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
  test('unusual actual combat differences remain visible without presentation metadata', () {
    final cat = variantCatalog();
    cat['duplicatePolicy'] = {
      'available': true,
      'combatVariants': {
        'skills': {
          '400010': [
            {'field': 'customCombatCondition', 'value': true},
          ],
        },
      },
    };
    expect(
      catalogDescriptions(cat, 'skills')[400010],
      contains('custom Combat Condition: yes'),
    );
  });
  test('all abilities get consistently ordered recorded stats without mutating source descriptions', () {
    final cat = variantCatalog();
    final before = json.encode(cat);
    final descriptions = catalogDescriptions(cat, 'skills');
    expect(
      descriptions[400010],
      startsWith(
        'Damage type: Magic; Target: single target; Target side: Enemies; Power: 17; MP cost: 5; Element: Fire',
      ),
    );
    expect(descriptions[400020], contains('Target: all targets'));
    expect(descriptions[400020], contains('Power: 12'));
    expect(
      descriptions.values,
      everyElement(contains('The complete original description.')),
    );
    expect(
      descriptions.values,
      everyElement(isNot(contains('Same-name version:'))),
    );
    expect(json.encode(cat), before);
    cat['skills'][1]['name'] = 'Other skill';
    expect(catalogDescriptions(cat, 'skills')[400010], descriptions[400010]);
  });

  test(
    'same-name passives retain equipment cost and distinct effect parameters',
    () {
      final descriptions = catalogDescriptions(variantCatalog(), 'passives');
      expect(descriptions[1001], contains('Equipment cost: 20'));
      expect(descriptions[1002], contains('Equipment cost: 40'));
      expect(
        descriptions[1001],
        contains('Effect 1: Reprieve; Parameters: 0, -1'),
      );
      expect(
        descriptions[1002],
        contains('Effect 1: Reprieve; Parameters: 0, 1'),
      );
      expect(descriptions[1001], contains('Survive with 1 HP.'));
    },
  );

  test('equivalent effect IDs do not invent differences in descriptions', () {
    final cat = variantCatalog();
    cat['passives'][1]['equipCost'] = 20;
    cat['effects'][1]['params'] = [0, -1];
    final text = catalogDescriptions(cat, 'passives');
    expect(text[1001], text[1002]);
  });

  test('Curaga uses extracted stats and removes voice, debug, mode-change and placeholder text', () {
    final cat = <String, dynamic>{
      'skills': [
        {
          'id': 210030,
          'name': 'Curaga',
          'desc': '[White Magic] Restore a large amount of HP.',
          'mag': 600,
        },
      ],
      'duplicatePolicy': {
        'available': true,
        'details': {
          'skills': {
            '210030': {
              'DamageType': 'Magic',
              'TargetType': 'Single',
              'accuracy': 100,
              'availableLocation': 'Anywhere',
              'breakDamageValue': 60,
              'defaultTargetRelation': 'Friendlies',
              'magnification': 1500,
              'mapEffectType': 'RecoveryHP',
              'voiceLabel': 'VO BTL ALB 05',
              'selfSkillActivateVoiceLabel': 'VO BTL ALB 16',
              'skillIdAfterModeChange': 215020,
              'belongCommandList': [1],
              'commandIdBelongDebuggingAllSkills': 901,
              'effectBundleList': [],
            },
          },
        },
      },
    };
    final before = json.encode(cat);
    expect(
      catalogDescriptions(cat, 'skills')[210030],
      'Damage type: Magic; Target: single target; Accuracy: 100; Location: Anywhere; Break Power: 60; Target side: Friendlies; Power: 1500; Effect type: Recovery HP\nRestore a large amount of HP.',
    );
    expect(json.encode(cat), before);
    cat['skills'][0]['desc'] = '[TEMP] Gilgamesh big heal';
    expect(
      catalogDescriptions(cat, 'skills')[210030],
      isNot(contains('Gilgamesh')),
    );
    cat['skills'][0]['desc'] = '回復HPを全回復する';
    expect(catalogDescriptions(cat, 'skills')[210030], isNot(contains('回復')));
  });

  test(
    'missing extracted stats are omitted rather than given guessed defaults',
    () {
      final cat = <String, dynamic>{
        'skills': [
          {'id': 1, 'name': 'Unknown', 'target': 'Single', 'mag': 0},
        ],
      };
      final desc = catalogDescriptions(cat, 'skills')[1]!;
      expect(desc, 'Target: single target; Power: 0');
      for (final label in [
        'Accuracy',
        'Location',
        'Damage type',
        'MP cost',
        'Effect type',
      ]) {
        expect(desc, isNot(contains(label)));
      }
    },
  );

  test('old variant metadata supplies known gameplay conditions and ignores internal fields', () {
    final cat = variantCatalog();
    cat['duplicatePolicy'] = {
      'available': true,
      'variants': {
        'skills': {
          '400010': [
            {'field': 'onlyWhenFullHP', 'value': true},
            {'field': 'availableLocation', 'value': 'BattleOnly'},
            {'field': 'voiceLabel', 'value': 'VO Something'},
            {'field': 'unknownSetting', 'value': null, 'missing': true},
          ],
        },
      },
    };
    final desc = catalogDescriptions(cat, 'skills')[400010]!;
    expect(desc, contains('Requires full HP: yes'));
    expect(desc, contains('Location: Battle Only'));
    expect(desc, isNot(contains('VO Something')));
    expect(desc, isNot(contains('unknown Setting')));
  });

  test('raw effect bundles retain effect targets, status, chance and exact unknown parameters', () {
    final cat = variantCatalog();
    cat['duplicatePolicy'] = {
      'available': true,
      'details': {
        'passives': {
          '1001': {
            'effectBundleList': [
              {
                'effectId': {
                  'mechanics': {
                    'EffectType': 'Counter',
                    'statusCondition': 'Poison',
                    'addProbability': 30,
                    'ParamList': [6, 400010, -1],
                  },
                },
                'TargetType': 'Group',
                'targetRelation': 'Enemies',
              },
            ],
          },
        },
      },
    };
    expect(
      catalogDescriptions(cat, 'passives')[1001],
      contains(
        'Effect 1: Counter; Target: all targets; Target side: Enemies; Status: Poison; Chance: 30; Parameters: 6, 400010, -1',
      ),
    );
  });
}
