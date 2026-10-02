import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'character_config_test.dart' show profile;

void main() {
  test('retired copies migrate on load and restore while preserving stats and saved files', () {
    final saved = profile();
    const retired = {9400440: 400440, 9403110: 403110, 9414500: 414500, 9505580: 505580};
    saved['awakening'] = [for (final entry in retired.entries)
      [['ActiveSkill', entry.key], ['ActiveSkill', entry.value], ['BaseParameter', 1, 50]]];
    saved['synchro'] = [for (final id in retired.keys) [['ActiveSkill', id]]];
    final before = CharacterConfig.copy(saved);
    final text = CharacterConfig.encode(saved);
    final migrated = CharacterConfig.retireComparisonAbilities(saved);
    expect(saved, before);
    expect(migrated['stats'], saved['stats']);
    expect(migrated['skills'], saved['skills']);
    for (var i = 0; i < retired.length; i++) {
      expect(migrated['awakening'][i], [['ActiveSkill', retired.values.elementAt(i)], ['BaseParameter', 1, 50]]);
      expect(migrated['synchro'][i], [['ActiveSkill', retired.values.elementAt(i)]]);
    }
    expect(CharacterConfig.decode(text), migrated);
    expect(CharacterConfig.decodeAll(CharacterConfig.encodeAll([saved])), [migrated]);
    expect(CharacterConfig.restore(saved, [], replacing: saved), migrated);
    expect(CharacterConfig.retireComparisonAbilities(migrated), same(migrated));
    expect(CharacterConfig.encode(saved), text);
  });

  test('unrelated duplicate grants and untouched party specs are preserved', () {
    final unit = <String, dynamic>{'awakening': [[['ActiveSkill', 9400440], ['ActiveSkill', 777], ['ActiveSkill', 777]],
      [['ActiveSkill', 400440]]], 'synchro': []};
    final result = CharacterConfig.retireComparisonAbilities(unit);
    expect(result['awakening'][0], [['ActiveSkill', 400440], ['ActiveSkill', 777], ['ActiveSkill', 777]]);
    expect(result['awakening'][1], unit['awakening'][1]);
    final party = <String, dynamic>{'id': 1001, 'party': {'version': 1, 'id': 1001}};
    expect(CharacterConfig.retireComparisonAbilities(party), same(party));
  });
}
