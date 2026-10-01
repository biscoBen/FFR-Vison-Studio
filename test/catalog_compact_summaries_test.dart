import 'dart:convert';

import 'package:ffr_vision_studio/state/catalog_descriptions.dart';
import 'package:ffr_vision_studio/state/catalog_helpers.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> compactExamples() => {
  'skills': [
    {
      'id': 250050,
      'name': 'Blizzard',
      'desc': 'Deal ice-type magic damage.',
      'dmgType': 'Magic',
      'target': 'Single',
      'accuracy': 100,
      'breakDmg': 17,
      'mag': 14,
      'cost': 5,
      'hits': 1,
    },
    {
      'id': 400530,
      'name': 'Deathblow',
      'desc': '[Battle Skill] Guarantee a critical if attack lands, but with a low hit chance.',
      'dmgType': 'Physic',
      'target': 'Single',
      'accuracy': 50,
      'breakDmg': 25,
      'mag': 12,
      'cost': 0,
      'hits': 1,
    },
    {
      'id': 505450,
      'name': 'Execution',
      'desc': '[TEMP] Execution desc.',
      'effectType': 'DamageAndRecovery',
      'dmgType': 'Magic',
      'element': 'Dark',
      'target': 'Group',
      'relation': 'Enemies',
      'accuracy': 500,
      'breakDmg': 12,
      'mag': 36,
      'cost': 0,
      'hits': 3,
    },
    {
      'id': 210010,
      'name': 'Cure',
      'desc': '[White Magic] Restore a small amount of HP.',
      'effectType': 'DamageAndRecovery',
      'dmgType': 'Magic',
      'target': 'Single',
      'relation': 'Friendlies',
      'accuracy': 100,
      'breakDmg': 50,
      'mag': 200,
      'cost': 6,
      'hits': 1,
    },
  ],
  'duplicatePolicy': {
    'available': true,
    'details': {
      'skills': {
        '250050': {
          'criticalHitRate': 3,
          'availableLocation': 'BattleOnly',
          'equipCost': 10,
        },
        '400530': {'criticalHitRate': 100},
        '505450': {
          'criticalHitRate': 0,
          'hitDamageRatioList': [0.2, 0.3, 0.5],
        },
        '210010': {'criticalHitRate': 0, 'mapEffectType': 'RecoveryHP'},
      },
    },
  },
};

void main() {
  test('requested examples have compact prose and exact recorded stats; full details remain separate', () {
    final cat = compactExamples();
    final before = jsonEncode(cat);
    final short = catalogAbilitySummaries(cat);
    expect(short[250050]!.description, 'Deal ice-type magic damage.');
    expect(
      short[250050]!.stats,
      'Type=Magic; Single Target; Accuracy=100; Break=17; Power=14; MP=5; Hits=1; Crit Chance=3',
    );
    expect(
      short[400530]!.description,
      'Guarantee a critical if attack lands, but with a low hit chance.',
    );
    expect(
      short[400530]!.stats,
      'Type=Physical; Single Target; Accuracy=50; Break=25; Power=12; MP=0; Hits=1; Crit Chance=100',
    );
    expect(short[505450]!.description, 'Deal dark-type magic damage.');
    expect(
      short[505450]!.stats,
      'Type=Magic; All Targets; Accuracy=500; Break=12; Power=36; MP=0; Hits=3; Crit Chance=0',
    );
    expect(short[210010]!.description, 'Restore a small amount of HP.');
    expect(
      short[210010]!.stats,
      'Type=Magic; Single Target; Accuracy=100; Break=50; Power=200; MP=6; Hits=1; Crit Chance=0',
    );
    final full = catalogDescriptions(cat, 'skills');
    expect(full[250050], contains('Equipment cost: 10'));
    expect(full[250050], contains('Location: Battle Only'));
    expect(full[505450], contains('Hit damage shares: 0.2, 0.3, 0.5'));
    expect(jsonEncode(cat), before);
  });

  test('raw stats override compact aliases without filling absent fields or dropping zeroes', () {
    final cat = compactExamples();
    cat['skills'] = [
      {'id': 250050, 'name': 'Blizzard', 'mag': 14, 'cost': 0},
    ];
    cat['duplicatePolicy']['details']['skills']['250050'] = {
      'magnification': 17,
      'criticalHitRate': 0,
    };
    expect(
      catalogAbilitySummaries(cat)[250050]!.stats,
      'Power=17; MP=0; Crit Chance=0',
    );
    cat.remove('duplicatePolicy');
    expect(catalogAbilitySummaries(cat)[250050]!.stats, 'Power=14; MP=0');
  });

  test('missing prose distinguishes healing, MP recovery and damage from recorded mechanics', () {
    final cat = compactExamples();
    cat['skills'][3]['desc'] = '回復HPを回復する';
    expect(catalogAbilitySummaries(cat)[210010]!.description, 'Restore HP.');
    cat['duplicatePolicy']['details']['skills']['210010'] = {
      'parameterType': 'MagicPoint',
      'parameterVariationType': 'Increase',
    };
    expect(catalogAbilitySummaries(cat)[210010]!.description, 'Restore MP.');
    cat['skills'][2]['effects'] = [1];
    cat['effects'] = [
      {
        'id': 1,
        'type': 'InstantDeath',
        'params': [-1],
        'prob': 100,
      },
    ];
    expect(
      catalogAbilitySummaries(cat)[505450]!.description,
      'Deal dark-type magic damage. Inflict instant death.',
    );
  });

  test('selection rules apply without duplicate proof and never mutate saved references', () {
    final cat = <String, dynamic>{
      'skills': [
        {'id': 1, 'name': ' Attack ', 'attr': 'Fight'},
        {'id': 2, 'name': '針万本', 'attr': 'Ability'},
        {'id': 3, 'name': 'Finish', 'attr': 'FinishBlow'},
        {'id': 4, 'name': 'Aetherial Wind', 'attr': 'Ability'},
        {'id': 5, 'name': 'Gentleman’s Gambit', 'attr': 'Ability'},
        {'id': 6, 'name': 'Double Attack', 'attr': 'Ability'},
      ],
      'passives': [
        {'id': 100, 'name': '攻撃力アップ'},
        {'id': 101, 'name': 'Grit'},
      ],
      'visions': [
        {'name': 'Y’shtola', 'finishBlow': 4},
      ],
    };
    final own = {
      'awakening': [
        [
          ['ActiveSkill', 1],
          ['ActiveSkill', 3],
          ['PassiveSkill', 100],
        ],
      ],
    };
    final before = jsonEncode([cat, own]);
    for (final policy in [
      null,
      {'available': false},
      {'schema': 2, 'available': true, 'ownersComplete': false},
    ]) {
      if (policy != null) cat['duplicatePolicy'] = policy;
      expect(
        catalogSelectableLibrary(cat, 'skills', [own]).map((s) => s['id']),
        [5, 6],
      );
      expect(
        catalogSelectableLibrary(cat, 'passives', [own]).map((s) => s['id']),
        [101],
      );
    }
    cat.remove('duplicatePolicy');
    expect(jsonEncode([cat, own]), before);
    expect(catalogNameIsEnglish('Glücksschmied'), isTrue);
    expect(catalogNameIsEnglish('Attack（敵用）'), isFalse);
  });

  test('confirmed source labels are independent of verification and default ownership', () {
    final row = {
      'id': 5,
      'name': '10,000 Needles',
      'hasUnit': 'All',
      'attr': 'Ability',
      'seq': [1],
    };
    final cat = <String, dynamic>{
      'duplicatePolicy': {
        'sources': {
          'skills': {
            '5': ['Cactuar', 'Cactuar', 'Metal Cactuar'],
          },
        },
      },
    };
    expect(
      catalogEntryTitle(cat, 'skills', row),
      '10,000 Needles — Source: Cactuar, Metal Cactuar',
    );
    row['seq'] = [];
    expect(
      catalogEntryTitle(cat, 'skills', row),
      '10,000 Needles (Unverified) — Source: Cactuar, Metal Cactuar',
    );
    cat['duplicatePolicy']['owners'] = {
      'skills': {
        '5': ['Leah'],
      },
    };
    expect(
      catalogEntryTitle(cat, 'skills', row),
      '10,000 Needles (Unverified) — Leah — Source: Cactuar, Metal Cactuar',
    );
    cat.remove('duplicatePolicy');
    expect(
      catalogEntryTitle(cat, 'skills', row),
      '10,000 Needles (Unverified)',
    );
  });
}
