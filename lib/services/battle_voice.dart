/// Native Resonance battle speakers, independent of models and story identity.
class BattleVoice {
  static const names = <int, String>{
    1001: 'Rain',
    1002: 'Lasswell',
    1003: 'Fina',
    1004: 'Lid',
    1005: 'Nichol',
    1006: 'Dark Fina',
    1007: 'Jake',
    1008: 'Sakura',
  };
  static bool valid(dynamic value) => value is int && names.containsKey(value);
  static String name(Map<String, dynamic> unit) =>
      names[unit['battleVoice'] ?? unit['id']]!;
}
