class OverworldAppearance {
  static const model = 'vagrant_knight_rain';
  static const sheet =
      'assets/existing_visions/payload/vagrant_knight_rain_field.png';
  static const profile = <String, dynamic>{'version': 1, 'model': model};
  static const entry = <String, dynamic>{
    'id': '100015005',
    'name': 'Vagrant Knight Rain',
    'jpname': '彷徨の騎士レイン',
    'packs': ['100015006'],
    'hasSprites': true,
    'rarity_min': 5,
    'rarity_max': 6,
    'roles': <String>[],
  };
  static const detail = <String, dynamic>{
    'id': '100015005',
    'name': 'Vagrant Knight Rain',
    'jpname': '彷徨の騎士レイン',
    'maxForm': '100015006',
    'forms': {
      '100015006': {'rarity': 6},
    },
  };
  static bool valid(dynamic value) =>
      value is Map &&
      value.length == 2 &&
      value['version'] is int && value['version'] == 1 &&
      value['model'] == model;
}
